import asyncio
import math
import time
from collections import deque
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx
from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.ai import AICapability, ConnectionReply, ConnectionResult

# Reviewed free-inference model. Aliases and arbitrary model IDs fail closed.
REVIEWED_MODELS = {"gemini-3.5-flash-lite"}
API_BASE = "https://generativelanguage.googleapis.com"


class AIError(Exception):
    def __init__(self, code: str, status: int = 503, retry_after: int = 0):
        self.code, self.status, self.retry_after = code, status, retry_after
        super().__init__(code)


class LimitedStream(httpx.AsyncByteStream):
    def __init__(self, stream):
        self.stream = stream

    async def __aiter__(self):
        count = 0
        async for chunk in self.stream:
            count += len(chunk)
            if count > 262_144:
                raise AIError("ai_response_too_large")
            yield chunk

    async def aclose(self):
        await self.stream.aclose()


class GeminiTransport(httpx.AsyncBaseTransport):
    def __init__(self, transport=None):
        self.inner = transport or httpx.AsyncHTTPTransport(retries=0)

    async def handle_async_request(self, request):
        if request.url.host != "generativelanguage.googleapis.com" or request.url.scheme != "https":
            raise AIError("ai_invalid_endpoint")
        # Avoid compressed bodies expanding past the transport's byte limit.
        request.headers["Accept-Encoding"] = "identity"
        response = await self.inner.handle_async_request(request)
        if response.headers.get("content-encoding", "identity").lower() != "identity":
            await response.aclose()
            raise AIError("ai_invalid_response")
        return httpx.Response(
            status_code=response.status_code,
            headers=response.headers,
            stream=LimitedStream(response.stream),
            extensions=response.extensions,
        )

    async def aclose(self):
        await self.inner.aclose()


class GeminiService:
    def __init__(self, settings: Settings, transport=None):
        self.settings, self.transport = settings, transport
        self.client = None
        self.http = None
        self.lock = asyncio.Lock()
        self.calls = deque()
        self.cooldown = 0.0
        self.last_success = None

    def capability(self) -> AICapability:
        s = self.settings
        key = bool(s.gemini_api_key.get_secret_value().strip())
        if not s.free_only_mode:
            reason = "free_only_required"
        elif s.gemini_model not in REVIEWED_MODELS:
            reason = "model_not_reviewed"
        elif not key:
            reason = "missing_api_key"
        elif not s.gemini_free_tier_confirmed:
            reason = "free_tier_unconfirmed"
        else:
            reason = "ready_to_check"
        return AICapability(
            enabled=reason == "ready_to_check",
            reason=reason,
            model=s.gemini_model if s.gemini_model in REVIEWED_MODELS else "unreviewed",
            key_configured=key,
            account_verification="operator_attested"
            if s.gemini_free_tier_confirmed
            else "unverified",
            live_verified_this_process=self.last_success is not None,
            last_success_at=self.last_success,
        )

    def _client(self):
        if self.client is None:
            self.http = httpx.AsyncClient(
                transport=GeminiTransport(self.transport),
                follow_redirects=False,
                timeout=httpx.Timeout(self.settings.gemini_timeout_seconds, connect=5),
                trust_env=False,
            )
            self.client = genai.Client(
                api_key=self.settings.gemini_api_key.get_secret_value(),
                enterprise=False,
                vertexai=False,
                http_options=types.HttpOptions(
                    base_url=API_BASE,
                    api_version="v1beta",
                    timeout=int(self.settings.gemini_timeout_seconds * 1000),
                    retry_options=types.HttpRetryOptions(attempts=1),
                    httpx_async_client=self.http,
                ),
            )
        return self.client

    async def aclose(self):
        if self.client:
            await self.client.aio.aclose()
            self.client.close()
        if self.http:
            await self.http.aclose()

    @staticmethod
    def retry_delay(exc) -> int:
        value = exc.response.headers.get("Retry-After") if exc.response is not None else None
        details = (
            exc.details.get("error", {}).get("details", []) if isinstance(exc.details, dict) else []
        )
        delays = []
        for detail in details if isinstance(details, list) else []:
            if (
                isinstance(detail, dict)
                and detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo"
            ):
                try:
                    seconds = float(str(detail.get("retryDelay", "")).removesuffix("s"))
                    if math.isfinite(seconds):
                        delays.append(seconds)
                except ValueError:
                    pass
        try:
            delay = float(value) if value else 60
        except ValueError:
            try:
                delay = (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                delay = 60
        if not math.isfinite(delay):
            delay = 60
        return max(1, math.ceil(max([delay, *delays])))

    async def check(self, language: str) -> ConnectionResult:
        capability = self.capability()
        if not capability.enabled:
            raise AIError(capability.reason, 409)
        if self.lock.locked():
            raise AIError("ai_busy", 429, 2)
        async with self.lock:
            now = time.monotonic()
            if now < self.cooldown:
                raise AIError("ai_quota_exhausted", 429, math.ceil(self.cooldown - now))
            while self.calls and self.calls[0] <= now - 86400:
                self.calls.popleft()
            if len(self.calls) >= self.settings.gemini_daily_limit:
                raise AIError("ai_local_limit", 429, math.ceil(self.calls[0] + 86400 - now))
            minute = [stamp for stamp in self.calls if stamp > now - 60]
            if len(minute) >= self.settings.gemini_minute_limit:
                raise AIError("ai_local_limit", 429, math.ceil(minute[0] + 60 - now))
            self.calls.append(now)
            try:
                async with asyncio.timeout(self.settings.gemini_timeout_seconds):
                    response = await self._client().aio.models.generate_content(
                        model=self.settings.gemini_model,
                        contents=(
                            "Connection test only. Return status ok and a short greeting in "
                            + ("Turkish." if language == "tr" else "English.")
                        ),
                        config=types.GenerateContentConfig(
                            system_instruction="Return JSON only. No travel facts or advice.",
                            response_mime_type="application/json",
                            response_json_schema=ConnectionReply.model_json_schema(),
                            max_output_tokens=512,
                            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                                disable=True
                            ),
                            # No search/maps, automatic tool execution, paid tier or fallback.
                        ),
                    )
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    raise AIError("ai_blocked", 422)
                candidates = response.candidates or []
                if len(candidates) != 1 or candidates[0].finish_reason != types.FinishReason.STOP:
                    raise AIError("ai_invalid_response")
                parts = candidates[0].content.parts if candidates[0].content else []
                if not parts or any(p.function_call for p in parts):
                    raise AIError("ai_invalid_response")
                text = "".join(p.text or "" for p in parts if not p.thought)
                if not text or len(text) > 4096:
                    raise AIError("ai_invalid_response")
                reply = ConnectionReply.model_validate_json(text)
                self.last_success = datetime.now(UTC)
                return ConnectionResult(
                    model=self.settings.gemini_model,
                    message=reply.message,
                    checked_at=self.last_success,
                )
            except errors.APIError as exc:
                if exc.code == 429:
                    delay = self.retry_delay(exc)
                    self.cooldown = time.monotonic() + delay
                    raise AIError("ai_quota_exhausted", 429, delay) from None
                code = {
                    400: "ai_request_rejected",
                    401: "ai_key_rejected",
                    403: "ai_access_denied",
                    404: "ai_model_unavailable",
                }.get(exc.code, "ai_provider_unavailable")
                raise AIError(code) from None
            except (TimeoutError, httpx.TimeoutException):
                raise AIError("ai_timeout") from None
            except (httpx.HTTPError, OSError):
                raise AIError("ai_provider_unavailable") from None
            except (ValidationError, ValueError, TypeError, AttributeError):
                raise AIError("ai_invalid_response") from None

    async def agent_turn(self, contents, declarations, response_schema, system_instruction):
        """Run one bounded manual function-calling turn; no automatic tool execution."""
        capability = self.capability()
        if not capability.enabled:
            raise AIError(capability.reason, 409)
        if self.lock.locked():
            raise AIError("ai_busy", 429, 2)
        async with self.lock:
            now = time.monotonic()
            if now < self.cooldown:
                raise AIError("ai_quota_exhausted", 429, math.ceil(self.cooldown - now))
            while self.calls and self.calls[0] <= now - 86400:
                self.calls.popleft()
            if len(self.calls) >= self.settings.gemini_daily_limit:
                raise AIError("ai_local_limit", 429, math.ceil(self.calls[0] + 86400 - now))
            minute = [stamp for stamp in self.calls if stamp > now - 60]
            if len(minute) >= self.settings.gemini_minute_limit:
                raise AIError("ai_local_limit", 429, math.ceil(minute[0] + 60 - now))
            self.calls.append(now)
            try:
                async with asyncio.timeout(self.settings.gemini_timeout_seconds):
                    response = await self._client().aio.models.generate_content(
                        model=self.settings.gemini_model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            tools=[types.Tool(function_declarations=declarations)],
                            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                                disable=True
                            ),
                            response_mime_type="application/json",
                            response_json_schema=response_schema,
                            max_output_tokens=4096,
                        ),
                    )
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    raise AIError("ai_blocked", 422)
                candidates = response.candidates or []
                if len(candidates) != 1 or candidates[0].finish_reason != types.FinishReason.STOP:
                    raise AIError("ai_invalid_response")
                content = candidates[0].content
                if not content or not content.parts:
                    raise AIError("ai_invalid_response")
                calls = [part.function_call for part in content.parts if part.function_call]
                text = "".join(
                    part.text or "" for part in content.parts if part.text and not part.thought
                )
                if text and len(text) > 65_536:
                    raise AIError("ai_response_too_large")
                self.last_success = datetime.now(UTC)
                return content, calls, text
            except errors.APIError as exc:
                if exc.code == 429:
                    delay = self.retry_delay(exc)
                    self.cooldown = time.monotonic() + delay
                    raise AIError("ai_quota_exhausted", 429, delay) from None
                code = {
                    400: "ai_request_rejected",
                    401: "ai_key_rejected",
                    403: "ai_access_denied",
                    404: "ai_model_unavailable",
                }.get(exc.code, "ai_provider_unavailable")
                raise AIError(code) from None
            except (TimeoutError, httpx.TimeoutException):
                raise AIError("ai_timeout") from None
            except (httpx.HTTPError, OSError):
                raise AIError("ai_provider_unavailable") from None
            except AIError:
                raise
            except (ValidationError, ValueError, TypeError, AttributeError):
                raise AIError("ai_invalid_response") from None

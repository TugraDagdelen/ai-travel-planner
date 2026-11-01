import asyncio
import copy
import json
import time
from collections import OrderedDict, deque
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx

from app.core.config import Settings

ENDPOINTS = {
    "geocoding": "https://geocoding-api.open-meteo.com/v1/search",
    "forecast": "https://api.open-meteo.com/v1/forecast",
    # One bounded fallback is allowed for availability, never to evade a 429 or cooldown.
    "overpass": (
        "https://overpass-api.de/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
    ),
}


class ProviderError(Exception):
    def __init__(self, code: str, provider: str, retryable: bool = True, retry_after: int = 0):
        self.code = code
        self.provider = provider
        self.retryable = retryable
        self.retry_after = retry_after
        super().__init__(code)


@dataclass
class Payload:
    data: dict
    fetched_at: datetime
    cached: bool = False


class Gateway:
    """One process: bounded LRU cache, serialized providers and conservative call budgets."""

    def __init__(self, client: httpx.AsyncClient, settings: Settings):
        self.client = client
        self.settings = settings
        self.cache: OrderedDict[str, tuple[float, Payload]] = OrderedDict()
        self.locks = {name: asyncio.Lock() for name in ("meteo", "overpass")}
        self.calls = {name: deque() for name in self.locks}
        self.next_call = {name: 0.0 for name in self.locks}
        self.cooldown = {name: 0.0 for name in self.locks}

    async def request(self, endpoint: str, parameters: dict, ttl: int) -> Payload:
        provider = "overpass" if endpoint == "overpass" else "meteo"
        key = endpoint + json.dumps(parameters, sort_keys=True)
        try:
            async with asyncio.timeout(self.settings.provider_timeout_seconds):
                async with self.locks[provider]:
                    now = time.monotonic()
                    if key in self.cache:
                        expiry, payload = self.cache[key]
                        if expiry > now:
                            self.cache.move_to_end(key)
                            result = copy.deepcopy(payload)
                            result.cached = True
                            return result
                        del self.cache[key]
                    if self.cooldown[provider] > now:
                        raise ProviderError(
                            "provider_rate_limited",
                            provider,
                            retry_after=int(self.cooldown[provider] - now) + 1,
                        )
                    payload = await self._fetch(endpoint, provider, parameters)
                    self.cache[key] = (time.monotonic() + ttl, copy.deepcopy(payload))
                    while len(self.cache) > 128:
                        self.cache.popitem(last=False)
                    return payload
        except TimeoutError as exc:
            raise ProviderError("provider_timeout", provider) from exc

    async def _fetch(self, endpoint: str, provider: str, parameters: dict) -> Payload:
        interval = (
            self.settings.overpass_min_interval_seconds
            if provider == "overpass"
            else self.settings.meteo_min_interval_seconds
        )
        endpoint_urls = ENDPOINTS[endpoint]
        urls = endpoint_urls if isinstance(endpoint_urls, tuple) else (endpoint_urls,) * 2
        for attempt in range(2):
            now = time.monotonic()
            while self.calls[provider] and self.calls[provider][0] < now - 86400:
                self.calls[provider].popleft()
            if (
                len(self.calls[provider]) >= self.settings.provider_daily_limit
                or sum(t > now - 3600 for t in self.calls[provider])
                >= self.settings.provider_hourly_limit
            ):
                raise ProviderError("local_request_limit", provider, retry_after=3600)
            await asyncio.sleep(max(0, self.next_call[provider] - now))
            self.calls[provider].append(time.monotonic())
            self.next_call[provider] = time.monotonic() + interval
            method = "POST" if endpoint == "overpass" else "GET"
            kwargs = {"data" if method == "POST" else "params": parameters}
            try:
                async with self.client.stream(method, urls[attempt], **kwargs) as response:
                    if response.status_code == 429:
                        delay = self._retry_after(response.headers.get("Retry-After"))
                        self.cooldown[provider] = time.monotonic() + delay
                        raise ProviderError("provider_rate_limited", provider, retry_after=delay)
                    if response.status_code in {502, 503, 504}:
                        delay = self._retry_after(response.headers.get("Retry-After"), default=1)
                        if delay > 2 or attempt == 1:
                            self.cooldown[provider] = time.monotonic() + delay
                            raise ProviderError("provider_unavailable", provider, retry_after=delay)
                        await asyncio.sleep(delay)
                        continue
                    if response.status_code != 200:
                        raise ProviderError("provider_unavailable", provider)
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > 2_000_000:
                            raise ProviderError("provider_response_too_large", provider, False)
                    data = json.loads(body)
                    if not isinstance(data, dict) or data.get("error"):
                        raise ValueError("invalid object")
                    # Never cache a partial/error Overpass remark as a complete empty result.
                    if endpoint == "overpass" and data.get("remark"):
                        raise ProviderError("provider_unavailable", provider)
                    return Payload(data, datetime.now(UTC))
            except httpx.TimeoutException as exc:
                if endpoint == "overpass" and attempt == 0:
                    continue
                raise ProviderError("provider_timeout", provider) from exc
            except httpx.HTTPError as exc:
                if endpoint == "overpass" and attempt == 0:
                    continue
                raise ProviderError("provider_unavailable", provider) from exc
            except (ValueError, UnicodeError) as exc:
                raise ProviderError("provider_invalid_response", provider, False) from exc
        raise ProviderError("provider_unavailable", provider)

    @staticmethod
    def _retry_after(value: str | None, default: int = 60) -> int:
        try:
            seconds = (
                int(value)
                if value and value.isdigit()
                else int((parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds())
            )
            return max(1, min(seconds, 3600))
        except (ValueError, TypeError, OverflowError):
            return default

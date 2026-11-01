import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.gemini import AIError, GeminiService


def configured(**changes):
    return Settings(
        _env_file=None,
        **(
            {
                "gemini_api_key": "test-key-not-real",
                "gemini_free_tier_confirmed": True,
            }
            | changes
        ),
    )


def reply(text='{"status":"ok","message":"Merhaba"}', finish="STOP"):
    return {
        "candidates": [
            {"content": {"role": "model", "parts": [{"text": text}]}, "finishReason": finish}
        ]
    }


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"gemini_api_key": ""}, "missing_api_key"),
        ({"gemini_free_tier_confirmed": False}, "free_tier_unconfirmed"),
        ({"free_only_mode": False}, "free_only_required"),
        ({"gemini_model": "gemini-flash-latest"}, "model_not_reviewed"),
        ({"gemini_model": "gemini-4-argon"}, "model_not_reviewed"),
    ],
)
def test_configuration_gates_make_no_calls(changes, reason):
    def reject(_):
        raise AssertionError("No external call permitted")

    with TestClient(
        create_app(configured(**changes), gemini_transport=httpx.MockTransport(reject))
    ) as c:
        status = c.get("/api/ai/status")
        assert status.json()["gemini"]["reason"] == reason
        assert status.json()["gemini"]["enabled"] is False
        assert "test-key-not-real" not in status.text
        assert c.post("/api/ai/check", json={"language": "tr"}).status_code == 409


def test_real_sdk_request_contract_and_success(monkeypatch):
    calls = []
    monkeypatch.setenv("GOOGLE_GEMINI_BASE_URL", "https://example.invalid")
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "true")
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "true")

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=reply())

    with TestClient(create_app(configured(), gemini_transport=httpx.MockTransport(handler))) as c:
        before = c.get("/api/ai/status").json()["gemini"]
        assert before["enabled"] and not before["live_verified_this_process"]
        assert not calls
        response = c.post("/api/ai/check", json={"language": "tr"})
        assert response.status_code == 200, response.text
        assert response.json()["message"] == "Merhaba"
        assert response.json()["tool_calls_executed"] == 0
        assert response.json()["itinerary_generated"] is False
        assert c.get("/api/ai/status").json()["gemini"]["live_verified_this_process"]
    assert len(calls) == 1
    assert calls[0].url.host == "generativelanguage.googleapis.com"
    assert calls[0].url.path.endswith("/models/gemini-3.5-flash-lite:generateContent")
    assert calls[0].headers["x-goog-api-key"] == "test-key-not-real"
    body = json.loads(calls[0].content)
    assert not body.get("tools")
    assert body["generationConfig"]["maxOutputTokens"] == 512
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert not any(
        k in body["generationConfig"]
        for k in ("candidateCount", "temperature", "serviceTier", "topP", "topK")
    )
    assert "Connection test only" in str(body["contents"])


@pytest.mark.parametrize(
    "code,expected",
    [
        (400, "ai_request_rejected"),
        (401, "ai_key_rejected"),
        (403, "ai_access_denied"),
        (404, "ai_model_unavailable"),
        (500, "ai_provider_unavailable"),
        (503, "ai_provider_unavailable"),
    ],
)
def test_provider_errors_are_safe_and_not_retried(code, expected):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(code, json={"error": {"code": code, "message": "test-key-not-real"}})

    with TestClient(create_app(configured(), gemini_transport=httpx.MockTransport(handler))) as c:
        response = c.post("/api/ai/check", json={})
        assert response.json()["code"] == expected
        assert "test-key-not-real" not in response.text
        assert len(calls) == 1


def test_quota_cooldown_prevents_immediate_second_request():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(429, headers={"Retry-After": "120"}, json={"error": {"code": 429}})

    with TestClient(create_app(configured(), gemini_transport=httpx.MockTransport(handler))) as c:
        first = c.post("/api/ai/check", json={})
        second = c.post("/api/ai/check", json={})
        assert first.status_code == second.status_code == 429
        assert first.headers["Retry-After"] == "120"
        assert second.json()["retry_after_seconds"] > 0
        assert len(calls) == 1


@pytest.mark.parametrize(
    "data",
    [
        {},
        reply("not-json"),
        reply('{"status":"ok","message":""}'),
        reply('{"status":"ok","message":"hello","extra":"bad"}'),
        reply(f'{{"status":"ok","message":"{"x" * 241}"}}'),
        reply(finish="MAX_TOKENS"),
        {
            "candidates": [
                {
                    "content": {"parts": [{"functionCall": {"name": "run_shell"}}]},
                    "finishReason": "STOP",
                }
            ]
        },
    ],
)
def test_unusable_output_never_becomes_success(data):
    with TestClient(
        create_app(
            configured(),
            gemini_transport=httpx.MockTransport(lambda _: httpx.Response(200, json=data)),
        )
    ) as c:
        assert c.post("/api/ai/check", json={}).json()["code"] == "ai_invalid_response"
        assert not c.get("/api/ai/status").json()["gemini"]["live_verified_this_process"]


def test_blocked_output():
    with TestClient(
        create_app(
            configured(),
            gemini_transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}})
            ),
        )
    ) as c:
        response = c.post("/api/ai/check", json={})
        assert response.status_code == 422
        assert response.json()["code"] == "ai_blocked"


@pytest.mark.parametrize(
    "failure,expected",
    [
        (httpx.ReadTimeout("secret"), "ai_timeout"),
        (httpx.ConnectError("secret"), "ai_provider_unavailable"),
    ],
)
def test_network_errors(failure, expected):
    def handler(_):
        raise failure

    with TestClient(create_app(configured(), gemini_transport=httpx.MockTransport(handler))) as c:
        response = c.post("/api/ai/check", json={})
        assert response.json()["code"] == expected
        assert "secret" not in response.text


def test_oversized_response_is_bounded():
    with TestClient(
        create_app(
            configured(),
            gemini_transport=httpx.MockTransport(
                lambda _: httpx.Response(200, content=b"x" * 262_145)
            ),
        )
    ) as c:
        assert c.post("/api/ai/check", json={}).json()["code"] == "ai_response_too_large"


@pytest.mark.parametrize("limits", [{"gemini_daily_limit": 1}, {"gemini_minute_limit": 1}])
def test_local_budget_and_invalid_input_do_not_send_more_calls(limits):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=reply())

    with TestClient(
        create_app(configured(**limits), gemini_transport=httpx.MockTransport(handler))
    ) as c:
        assert c.post("/api/ai/check", json={"notes": "private"}).status_code == 422
        assert not calls
        assert c.post("/api/ai/check", json={}).status_code == 200
        assert c.post("/api/ai/check", json={}).json()["code"] == "ai_local_limit"
        assert len(calls) == 1


def test_concurrent_call_is_not_queued():
    async def run():
        entered, release = asyncio.Event(), asyncio.Event()

        async def handler(_):
            entered.set()
            await release.wait()
            return httpx.Response(200, json=reply())

        service = GeminiService(configured(), httpx.MockTransport(handler))
        first = asyncio.create_task(service.check("en"))
        await entered.wait()
        try:
            with pytest.raises(AIError, match="ai_busy"):
                await service.check("en")
            release.set()
            assert (await first).status == "connected"
        finally:
            release.set()
            await service.aclose()

    asyncio.run(run())


def test_both_research_adapters_stay_disabled_even_with_flags():
    def reject(_):
        raise AssertionError("Grounding must never contact Google")

    settings = configured(enable_google_maps_grounding=True, enable_google_search_grounding=True)
    with TestClient(create_app(settings, gemini_transport=httpx.MockTransport(reject))) as c:
        for provider in ("google_maps", "google_search"):
            capability = c.get("/api/capabilities").json()["providers"][provider]
            assert capability["enabled"] is False
            assert capability["requested"] is True
            result = c.post("/api/research", json={"provider": provider}).json()
            assert result["status"] == "unavailable"
            assert result["reason"] == "not_free_for_reviewed_model"
            assert result["citations"] == []
            assert result["source_support"] is None
            assert result["fallback"] == "osm_discovery"


def test_structured_retry_info_controls_cooldown():
    body = {
        "error": {
            "code": 429,
            "details": [
                {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "180.5s"}
            ],
        }
    }
    with TestClient(
        create_app(
            configured(),
            gemini_transport=httpx.MockTransport(lambda _: httpx.Response(429, json=body)),
        )
    ) as c:
        assert c.post("/api/ai/check", json={}).headers["Retry-After"] == "181"


def test_overall_deadline_cancels_request():
    async def handler(_):
        await asyncio.sleep(5)
        raise AssertionError("deadline should cancel this request")

    with TestClient(
        create_app(
            configured(gemini_timeout_seconds=1), gemini_transport=httpx.MockTransport(handler)
        )
    ) as c:
        assert c.post("/api/ai/check", json={}).json()["code"] == "ai_timeout"

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def client():
    with TestClient(create_app(Settings(_env_file=None))) as value:
        yield value


@pytest.fixture
def preferences():
    return {
        "destination": "  İstanbul  ",
        "start_date": "2027-02-01",
        "end_date": "2027-02-04",
        "interests": ["culture", "food", "culture"],
        "language": "tr",
    }


def test_health_and_capabilities_report_phase_six_without_live_ai(client):
    health = client.get("/api/health").json()
    assert health["status"] == "ok"
    assert health["phase"] == 6
    assert health["version"] == "0.6.0"
    capabilities = client.get("/api/capabilities").json()
    assert capabilities["phase"] == 6
    assert capabilities["itinerary_generation"] is True
    assert capabilities["function_calling"] is False
    assert capabilities["persistence"] is True
    assert capabilities["providers"]["open_meteo"]["enabled"] is True
    assert capabilities["providers"]["gemini"]["enabled"] is False
    assert capabilities["providers"]["google_maps"]["enabled"] is False


def test_preferences_are_normalized_without_generating_a_trip(client, preferences):
    response = client.post("/api/trip-requests/validate", json=preferences)
    assert response.status_code == 200
    result = response.json()
    assert result["request"]["destination"] == "İstanbul"
    assert result["request"]["interests"] == ["culture", "food"]
    assert result["duration_days"] == 4
    assert result["itinerary_generated"] is False


@pytest.mark.parametrize(
    "change",
    [
        {"end_date": "2027-01-31"},
        {"end_date": "2027-02-15"},
        {"destination": "   "},
        {"interests": []},
        {"interests": ["injected_tool"]},
        {"start_date": "not-a-date"},
        {"budget": "unknown"},
        {"notes": "x" * 1001},
        {"unexpected": "secret"},
    ],
)
def test_invalid_preferences_return_safe_error(client, preferences, change):
    response = client.post("/api/trip-requests/validate", json=preferences | change)
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert "input" not in response.json()
    assert "secret" not in response.text


def test_cors_allows_only_configured_browser_origin(client):
    for origin, allowed in [("http://localhost:5173", True), ("https://other.test", False)]:
        response = client.options(
            "/api/trip-requests/validate",
            headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
        )
        assert (response.headers.get("access-control-allow-origin") == origin) is allowed


def test_false_environment_flags_are_not_truthy(monkeypatch):
    monkeypatch.setenv("ENABLE_GOOGLE_MAPS_GROUNDING", "false")
    assert Settings(_env_file=None).enable_google_maps_grounding is False


def test_production_build_serves_assets_and_spa_routes():
    dist = Path(__file__).parent / "fixtures" / "frontend-dist"
    with TestClient(create_app(Settings(_env_file=None), frontend_dist=dist)) as production:
        assert "Rota production" in production.get("/").text
        assert "Rota production" in production.get("/trips/saved-id").text
        assert "console.log" in production.get("/assets/app.js").text
        missing_api = production.get("/api/does-not-exist")
        assert missing_api.status_code == 404
        assert missing_api.headers["content-type"].startswith("application/json")


def test_configuration_can_reduce_trip_limit(preferences):
    with TestClient(create_app(Settings(_env_file=None, max_trip_days=3))) as client:
        response = client.post("/api/trip-requests/validate", json=preferences)
        assert response.status_code == 422

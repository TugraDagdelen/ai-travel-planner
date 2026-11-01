import copy
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from google.genai import types

from app.core.config import Settings
from app.main import create_app

NOW = datetime(2027, 2, 1, 8, tzinfo=UTC)
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def client():
    def reject_network(_request):
        raise AssertionError("demo itinerary must remain offline")

    settings = Settings(_env_file=None, database_url="sqlite+pysqlite:///:memory:")
    with TestClient(
        create_app(settings, transport=httpx.MockTransport(reject_network), now=lambda: NOW)
    ) as value:
        yield value


def generation_body(client, *, days=2, generation_mode="demo", data_mode="demo"):
    destination = client.get(
        "/api/destinations", params={"q": "Paris", "mode": data_mode}
    ).json()["destinations"][0]
    return {
        "request": {
            "destination": "Paris, France",
            "start_date": "2027-02-01",
            "end_date": f"2027-02-{days:02d}",
            "interests": ["culture", "food"],
            "budget": "balanced",
            "pace": "relaxed",
            "language": "en",
            "notes": "",
        },
        "destination_id": destination["id"],
        "data_mode": data_mode,
        "generation_mode": generation_mode,
        "idempotency_key": str(uuid4()),
    }


def test_demo_generation_is_valid_persisted_and_source_labelled(client):
    response = client.post("/api/trips/generate", json=generation_body(client))
    assert response.status_code == 201
    trip = response.json()
    assert [day["date"] for day in trip["days"]] == ["2027-02-01", "2027-02-02"]
    place_ids = [item["place"]["id"] for day in trip["days"] for item in day["activities"]]
    assert len(place_ids) == len(set(place_ids))
    assert all(source["mode"] == "demo" for source in trip["sources"])
    assert {item["name"] for item in trip["agent_activity"]} >= {
        "get_weather",
        "search_places",
        "deterministic_planner",
        "sqlite",
    }
    assert client.get(f"/api/trips/{trip['id']}").json()["version"] == 1
    listing = client.get("/api/trips").json()
    assert listing["total"] == 1
    assert listing["trips"][0]["id"] == trip["id"]


def test_revision_reuses_saved_evidence_and_crud_is_transactional(client):
    trip = client.post("/api/trips/generate", json=generation_body(client)).json()
    original = [day["activities"][0]["place"]["id"] for day in trip["days"]]
    revised = client.post(
        f"/api/trips/{trip['id']}/revise", json={"instruction": "Swap the first two stops"}
    )
    assert revised.status_code == 200
    body = revised.json()
    assert body["version"] == 2
    assert [day["activities"][0]["place"]["id"] for day in body["days"]] == original[::-1]
    assert body["agent_activity"][-1]["name"] == "saved_evidence"
    renamed = client.patch(f"/api/trips/{trip['id']}", json={"title": "Paris weekend"})
    assert renamed.json()["title"] == "Paris weekend"
    assert renamed.json()["version"] == 3
    assert client.delete(f"/api/trips/{trip['id']}").status_code == 204
    assert client.get(f"/api/trips/{trip['id']}").status_code == 404


def test_generation_idempotency_prevents_duplicate_saved_trips(client):
    body = generation_body(client)
    first = client.post("/api/trips/generate", json=body)
    second = client.post("/api/trips/generate", json=body)
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert client.get("/api/trips").json()["total"] == 1


def test_targeted_revision_changes_only_requested_day(client):
    trip = client.post("/api/trips/generate", json=generation_body(client)).json()
    before = copy.deepcopy(trip["days"])
    revised = client.post(
        f"/api/trips/{trip['id']}/revise",
        json={"instruction": "Change day 2"},
    )
    assert revised.status_code == 200
    after = revised.json()
    assert after["days"][0] == before[0]
    assert after["days"][1] != before[1]
    assert after["revisions"][0]["version"] == 2


def test_invalid_modes_ai_readiness_and_insufficient_evidence_fail_closed(client):
    mismatch = generation_body(client)
    mismatch["generation_mode"] = "deterministic"
    assert client.post("/api/trips/generate", json=mismatch).status_code == 422

    ai_body = generation_body(client)
    demo_destination = client.app.state.discovery.resolve(ai_body["destination_id"], "demo")
    client.app.state.discovery.remember([demo_destination], "live")
    ai_body["generation_mode"] = "ai"
    ai_body["data_mode"] = "live"
    response = client.post("/api/trips/generate", json=ai_body)
    assert response.status_code == 409
    assert response.json()["code"] == "missing_api_key"

    long_trip = generation_body(client, days=4)
    result = client.post("/api/trips/generate", json=long_trip)
    assert result.status_code == 422
    assert result.json()["code"] == "insufficient_place_evidence"


def test_unknown_trip_and_revision_input_are_safe(client):
    assert client.get("/api/trips/missing").status_code == 404
    assert client.delete("/api/trips/missing").status_code == 404
    response = client.post("/api/trips/missing/revise", json={"instruction": "x"})
    assert response.status_code == 422
    assert "x" not in response.text


class FakeGemini:
    def __init__(self):
        self.turns = 0
        self.declaration_names = []

    async def agent_turn(self, _history, declarations, _schema, _system):
        self.declaration_names = [item.name for item in declarations]
        self.turns += 1
        if self.turns == 1:
            content = types.Content(
                role="model",
                parts=[
                    types.Part.from_function_call(
                        name="get_weather",
                        args={
                            "destination_id": "geonames:2988507",
                            "start_date": "2027-02-01",
                            "end_date": "2027-02-02",
                        },
                    ),
                    types.Part.from_function_call(
                        name="search_places",
                        args={
                            "destination_id": "geonames:2988507",
                            "categories": ["museum", "park"],
                            "radius_m": 1500,
                        },
                    ),
                ],
            )
            return content, [part.function_call for part in content.parts], ""
        proposal = {
            "title": "Verified Paris plan",
            "days": [
                {
                    "date": "2027-02-01",
                    "activities": [
                        {"period": "morning", "place_id": "osm:node:1", "reason": "Museum"}
                    ],
                    "alternative_place_ids": [],
                },
                {
                    "date": "2027-02-02",
                    "activities": [
                        {"period": "morning", "place_id": "osm:way:3", "reason": "Park"}
                    ],
                    "alternative_place_ids": [],
                },
            ],
            "warnings": [],
        }
        text = json.dumps(proposal)
        content = types.Content(role="model", parts=[types.Part.from_text(text=text)])
        return content, [], text


def test_ai_loop_dispatches_declared_tools_and_validates_actual_results():
    cities = json.loads((FIXTURES / "cities.json").read_text(encoding="utf-8"))
    places = json.loads((FIXTURES / "places.json").read_text(encoding="utf-8"))
    forecast = {
        "timezone": "Europe/Paris",
        "daily": {
            "time": ["2027-02-01", "2027-02-02"],
            "temperature_2m_min": [7, 8],
            "temperature_2m_max": [13, 14],
            "precipitation_sum": [0, 3],
            "precipitation_probability_max": [10, 50],
            "weather_code": [1, 3],
        },
        "daily_units": {
            "temperature_2m_min": "°C",
            "temperature_2m_max": "°C",
            "precipitation_sum": "mm",
            "precipitation_probability_max": "%",
            "weather_code": "wmo code",
        },
    }
    responses = {
        "geocoding-api.open-meteo.com": cities,
        "api.open-meteo.com": forecast,
        "overpass-api.de": places,
        "overpass.private.coffee": places,
    }
    provider_calls = []

    def handler(request):
        provider_calls.append(request.url.host)
        return httpx.Response(200, json=copy.deepcopy(responses[request.url.host]))

    settings = Settings(
        _env_file=None,
        database_url="sqlite+pysqlite:///:memory:",
        meteo_min_interval_seconds=0,
        overpass_min_interval_seconds=0,
    )
    fake = FakeGemini()
    with TestClient(
        create_app(settings, transport=httpx.MockTransport(handler), now=lambda: NOW)
    ) as live:
        live.app.state.itineraries.gemini = fake
        destination = live.get("/api/destinations", params={"q": "Paris"}).json()[
            "destinations"
        ][0]
        body = {
            "request": {
                "destination": "Paris, France",
                "start_date": "2027-02-01",
                "end_date": "2027-02-02",
                "interests": ["culture", "nature"],
                "budget": "balanced",
                "pace": "relaxed",
                "language": "en",
                "notes": "",
            },
            "destination_id": destination["id"],
            "data_mode": "live",
            "generation_mode": "ai",
            "idempotency_key": str(uuid4()),
        }
        result = live.post("/api/trips/generate", json=body)
    assert result.status_code == 201
    assert fake.turns == 2
    assert fake.declaration_names == ["get_weather", "search_places"]
    assert provider_calls == [
        "geocoding-api.open-meteo.com",
        "api.open-meteo.com",
        "overpass-api.de",
    ]
    assert result.json()["days"][0]["activities"][0]["place"]["name"] == "Fixture Museum"

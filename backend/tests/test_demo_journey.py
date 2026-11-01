from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_complete_turkish_demo_journey_is_offline_and_transactional():
    def reject_network(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"demo journey attempted network access: {request.url.host}")

    settings = Settings(_env_file=None, database_url="sqlite+pysqlite:///:memory:")
    with TestClient(
        create_app(settings, transport=httpx.MockTransport(reject_network))
    ) as client:
        request = {
            "destination": "İstanbul, Türkiye",
            "start_date": "2027-02-01",
            "end_date": "2027-02-02",
            "interests": ["culture", "food"],
            "budget": "economy",
            "pace": "relaxed",
            "language": "tr",
            "notes": "Yerel kültür ve sakin bir tempo.",
        }
        validated = client.post("/api/trip-requests/validate", json=request)
        assert validated.status_code == 200
        assert validated.json()["request"]["destination"] == "İstanbul, Türkiye"

        search = client.get(
            "/api/destinations",
            params={"q": "İstanbul", "language": "tr", "mode": "demo"},
        )
        assert search.status_code == 200
        destination = search.json()["destinations"][0]
        assert destination["name"] == "İstanbul"

        weather = client.get(
            "/api/weather",
            params={
                "destination_id": destination["id"],
                "start_date": request["start_date"],
                "end_date": request["end_date"],
                "mode": "demo",
            },
        )
        places = client.get(
            "/api/places",
            params=[
                ("destination_id", destination["id"]),
                ("categories", "historic"),
                ("categories", "museum"),
                ("categories", "restaurant"),
                ("mode", "demo"),
            ],
        )
        assert weather.status_code == places.status_code == 200
        metadata = [weather.json()["metadata"], places.json()["metadata"]]
        assert all(item["mode"] == "demo" for item in metadata)

        generation = {
            "request": request,
            "destination_id": destination["id"],
            "data_mode": "demo",
            "generation_mode": "demo",
            "idempotency_key": str(uuid4()),
        }
        created = client.post("/api/trips/generate", json=generation)
        assert created.status_code == 201
        trip = created.json()
        assert len(trip["days"]) == 2

        repeated = client.post("/api/trips/generate", json=generation)
        assert repeated.json()["id"] == trip["id"]
        assert client.get("/api/trips").json()["total"] == 1

        first_day = trip["days"][0]
        revised = client.post(
            f"/api/trips/{trip['id']}/revise",
            json={"instruction": "2. günü değiştir"},
        )
        assert revised.status_code == 200
        assert revised.json()["days"][0] == first_day
        assert revised.json()["revisions"][0]["result_summary"].startswith("2. günün")

        assert client.get(f"/api/trips/{trip['id']}").status_code == 200
        assert client.delete(f"/api/trips/{trip['id']}").status_code == 204
        assert client.get("/api/trips").json()["total"] == 0

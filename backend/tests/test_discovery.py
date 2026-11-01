import copy
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2027, 2, 1, 8, tzinfo=UTC)


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def forecast():
    return {
        "timezone": "Europe/Paris",
        "daily": {
            "time": ["2027-02-01", "2027-02-02"],
            "temperature_2m_min": [7, None],
            "temperature_2m_max": [13, None],
            "precipitation_sum": [0.2, None],
            "precipitation_probability_max": [20, None],
            "weather_code": [2, None],
        },
        "daily_units": {
            "temperature_2m_min": "°C",
            "temperature_2m_max": "°C",
            "precipitation_sum": "mm",
            "precipitation_probability_max": "%",
            "weather_code": "wmo code",
        },
    }


@pytest.fixture
def harness():
    calls = []
    responses = {
        "geocoding-api.open-meteo.com": fixture("cities.json"),
        "api.open-meteo.com": forecast(),
        "overpass-api.de": fixture("places.json"),
        "overpass.private.coffee": fixture("places.json"),
    }

    def handler(request):
        calls.append(request)
        value = responses[request.url.host]
        if isinstance(value, Exception):
            raise value
        if callable(value):
            return value(request)
        if isinstance(value, httpx.Response):
            return value
        return httpx.Response(200, json=copy.deepcopy(value))

    settings = Settings(
        _env_file=None,
        meteo_min_interval_seconds=0,
        overpass_min_interval_seconds=0,
        places_provider="overpass",
    )
    with TestClient(
        create_app(settings, transport=httpx.MockTransport(handler), now=lambda: NOW)
    ) as client:
        yield client, calls, responses


def select(client):
    result = client.get("/api/destinations", params={"q": "Paris"})
    assert result.status_code == 200
    return result.json()["destinations"][0]["id"]


def weather_params(identifier, **overrides):
    return {
        "destination_id": identifier,
        "start_date": "2027-02-01",
        "end_date": "2027-02-02",
        **overrides,
    }


def test_ambiguous_cities_are_returned_and_cached(harness):
    client, calls, _ = harness
    first = client.get("/api/destinations", params={"q": "Paris"}).json()
    second = client.get("/api/destinations", params={"q": "Paris"}).json()
    assert len(first["destinations"]) == 2
    assert {d["country_code"] for d in first["destinations"]} == {"FR", "US"}
    assert second["metadata"]["cached"] is True
    assert first["metadata"]["fetched_at"] == second["metadata"]["fetched_at"]
    assert len(calls) == 1
    assert calls[0].url.params["count"] == "10"


def test_country_filter_and_no_results(harness):
    client, calls, responses = harness
    value = client.get("/api/destinations", params={"q": "Paris", "country_code": "FR"})
    assert len(value.json()["destinations"]) == 1
    assert calls[0].url.params["countryCode"] == "FR"
    responses["geocoding-api.open-meteo.com"] = {}
    empty = client.get("/api/destinations", params={"q": "nonexistent"})
    assert empty.status_code == 200
    assert empty.json()["destinations"] == []


def test_forecast_dates_units_nulls_and_cache(harness):
    client, calls, _ = harness
    identifier = select(client)
    response = client.get("/api/weather", params=weather_params(identifier))
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "partial"
    assert result["timezone"] == "Europe/Paris"
    assert result["units"]["temperature"] == "°C"
    assert result["days"][0]["temperature_max"] == 13
    assert result["days"][1]["available"] is False
    assert result["days"][1]["reason"] == "missing_data"
    cached = client.get("/api/weather", params=weather_params(identifier)).json()
    assert cached["metadata"]["cached"] is True
    assert len(calls) == 2


def test_partial_horizon_only_fetches_supported_dates(harness):
    client, calls, _ = harness
    identifier = select(client)
    result = client.get(
        "/api/weather",
        params=weather_params(identifier, start_date="2027-01-31", end_date="2027-02-01"),
    ).json()
    assert result["days"][0]["reason"] == "outside_forecast_horizon"
    assert result["days"][1]["available"] is True
    assert calls[-1].url.params["start_date"] == "2027-02-01"


def test_far_future_never_calls_forecast(harness):
    client, calls, _ = harness
    identifier = select(client)
    result = client.get(
        "/api/weather",
        params=weather_params(identifier, start_date="2028-01-01", end_date="2028-01-03"),
    ).json()
    assert result["status"] == "unavailable"
    assert len(result["days"]) == 3
    assert all(d["reason"] == "outside_forecast_horizon" for d in result["days"])
    assert result["metadata"]["fetched_at"] is None
    assert len(calls) == 1


@pytest.mark.parametrize("broken", ["timezone", "units", "length", "duplicate"])
def test_malformed_forecasts_are_not_presented_as_real_weather(harness, broken):
    client, _, responses = harness
    data = responses["api.open-meteo.com"]
    if broken == "timezone":
        data["timezone"] = "America/Chicago"
    elif broken == "units":
        data["daily_units"]["temperature_2m_max"] = "°F"
    elif broken == "length":
        data["daily"]["temperature_2m_max"] = []
    else:
        data["daily"]["time"] = ["2027-02-01", "2027-02-01"]
    response = client.get("/api/weather", params=weather_params(select(client)))
    assert response.status_code == 503
    assert response.json()["code"] == "provider_invalid_response"


def test_osm_parsing_provenance_deduplication_and_missing_coordinates(harness):
    client, calls, _ = harness
    identifier = select(client)
    response = client.get(
        "/api/places", params={"destination_id": identifier, "categories": ["museum", "park"]}
    )
    assert response.status_code == 200
    result = response.json()
    assert len(result["places"]) == 4
    by_id = {place["id"]: place for place in result["places"]}
    assert "osm:way:2" not in by_id
    assert by_id["osm:node:1"]["classification_basis"] == "osm_tag"
    assert by_id["osm:way:3"]["coordinate_kind"] == "geometry_center"
    assert by_id["osm:way:3"]["classification_basis"] == "category_inference"
    assert by_id["osm:relation:4"]["latitude"] is None
    assert by_id["osm:way:7"]["coordinate_kind"] == "unknown"
    assert result["skipped_records"] == 2
    assert result["metadata"]["source"] == "© OpenStreetMap contributors"
    query = parse_qs(calls[-1].content.decode())["data"][0]
    assert '["tourism"="museum"]' in query
    assert "out center 120" in query
    assert "around:1500" in query


def test_dense_categories_use_bounded_overpass_filters(harness):
    client, calls, _ = harness
    identifier = select(client)
    response = client.get(
        "/api/places",
        params={"destination_id": identifier, "categories": ["historic", "restaurant"]},
    )
    assert response.status_code == 200
    query = parse_qs(calls[-1].content.decode())["data"][0]
    assert 'node(around:1500' in query
    assert '["historic"]' not in query
    assert 'monument|memorial|castle' in query
    assert "maxsize:4194304" in query


def test_wikimedia_places_are_real_typed_and_attributed():
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.host == "geocoding-api.open-meteo.com":
            return httpx.Response(200, json=fixture("cities.json"))
        if request.url.host == "en.wikipedia.org":
            return httpx.Response(
                200,
                json={
                    "query": {
                        "pages": [
                            {
                                "title": "Fixture Museum",
                                "pageprops": {"wikibase_item": "Q100"},
                                "coordinates": [{"lat": 48.851, "lon": 2.35}],
                            },
                            {
                                "title": "Fixture Restaurant",
                                "pageprops": {"wikibase_item": "Q200"},
                                "coordinates": [{"lat": 48.852, "lon": 2.351}],
                            },
                        ]
                    }
                },
            )
        if request.url.host == "query.wikidata.org":
            return httpx.Response(
                200,
                json={
                    "results": {
                        "bindings": [
                            {
                                "item": {"value": "http://www.wikidata.org/entity/Q100"},
                                "root": {"value": "http://www.wikidata.org/entity/Q33506"},
                            },
                            {
                                "item": {"value": "http://www.wikidata.org/entity/Q200"},
                                "root": {"value": "http://www.wikidata.org/entity/Q11707"},
                            },
                        ]
                    }
                },
            )
        raise AssertionError(f"unexpected provider: {request.url.host}")

    settings = Settings(
        _env_file=None,
        places_provider="wikimedia",
        meteo_min_interval_seconds=0,
        wikimedia_min_interval_seconds=0,
    )
    with TestClient(create_app(settings, transport=httpx.MockTransport(handler))) as client:
        identifier = select(client)
        result = client.get(
            "/api/places",
            params={
                "destination_id": identifier,
                "categories": ["museum", "restaurant"],
            },
        )
    assert result.status_code == 200
    payload = result.json()
    assert {place["id"] for place in payload["places"]} == {
        "wikidata:Q100",
        "wikidata:Q200",
    }
    assert payload["metadata"]["source"] == "Wikidata and Wikipedia contributors"
    museum = next(place for place in payload["places"] if place["id"] == "wikidata:Q100")
    assert museum["source_url"] == "https://www.wikidata.org/wiki/Q100"
    assert calls[1].url.params["colimit"] == "max"
    assert [request.url.host for request in calls] == [
        "geocoding-api.open-meteo.com",
        "en.wikipedia.org",
        "query.wikidata.org",
    ]


def test_empty_and_truncated_places_are_explicit(harness):
    client, _, responses = harness
    identifier = select(client)
    responses["overpass-api.de"] = {"elements": []}
    response = client.get(
        "/api/places", params={"destination_id": identifier, "categories": "museum"}
    )
    assert response.json()["places"] == []
    elements = [fixture("places.json")["elements"][0]] * 120
    responses["overpass-api.de"] = {"elements": elements}
    response = client.get(
        "/api/places",
        params={"destination_id": identifier, "categories": "museum", "radius_m": 1000},
    )
    assert response.json()["truncated"] is True


def test_multi_category_place_matches_requested_category(harness):
    client, _, responses = harness
    identifier = select(client)
    element = fixture("places.json")["elements"][0]
    element["tags"]["historic"] = "building"
    responses["overpass-api.de"] = {"elements": [element]}
    result = client.get(
        "/api/places", params={"destination_id": identifier, "categories": "historic"}
    ).json()
    assert len(result["places"]) == 1
    assert result["places"][0]["category"] == "historic"


def test_overpass_runtime_error_is_not_an_empty_success(harness):
    client, _, responses = harness
    identifier = select(client)
    responses["overpass-api.de"] = {"elements": [], "remark": "runtime timeout"}
    response = client.get(
        "/api/places", params={"destination_id": identifier, "categories": "museum"}
    )
    assert response.status_code == 503


def test_overpass_uses_one_fallback_after_transport_timeout(harness):
    client, calls, responses = harness
    identifier = select(client)
    responses["overpass-api.de"] = httpx.ReadTimeout("timeout")
    result = client.get(
        "/api/places",
        params={"destination_id": identifier, "categories": "museum", "radius_m": 1500},
    )
    assert result.status_code == 200
    assert result.json()["places"][0]["name"] == "Fixture Museum"
    assert [call.url.host for call in calls if "overpass" in call.url.host] == [
        "overpass-api.de",
        "overpass.private.coffee",
    ]


def test_overpass_rate_limit_does_not_rotate(harness):
    client, calls, responses = harness
    identifier = select(client)
    responses["overpass-api.de"] = httpx.Response(429, headers={"Retry-After": "60"})
    result = client.get(
        "/api/places",
        params={"destination_id": identifier, "categories": "museum", "radius_m": 1500},
    )
    assert result.status_code == 429
    assert [call.url.host for call in calls if "overpass" in call.url.host] == [
        "overpass-api.de"
    ]


@pytest.mark.parametrize(
    "params",
    [
        {"categories": "raw_query"},
        {"categories": "museum", "radius_m": 3001},
        {"categories": "museum", "radius_m": -1},
        {"categories": "museum", "mode": "paid"},
    ],
)
def test_invalid_place_queries_make_no_provider_calls(harness, params):
    client, calls, _ = harness
    response = client.get("/api/places", params={"destination_id": "arbitrary", **params})
    assert response.status_code == 422
    assert not calls


def test_invalid_dates_and_unknown_destinations_do_not_fetch(harness):
    client, calls, _ = harness
    invalid = client.get("/api/weather", params=weather_params("unknown", end_date="2027-01-01"))
    expired = client.get("/api/weather", params=weather_params("unknown"))
    assert invalid.status_code == 422
    assert expired.status_code == 409
    assert expired.json()["code"] == "destination_expired"
    assert not calls


def test_demo_is_offline_and_separate_from_live_identity(harness):
    client, calls, _ = harness
    data = client.get("/api/destinations", params={"q": "Paris", "mode": "demo"}).json()
    assert len(data["destinations"]) == 2
    identifier = data["destinations"][0]["id"]
    weather = client.get("/api/weather", params=weather_params(identifier, mode="demo")).json()
    places = client.get(
        "/api/places", params={"destination_id": identifier, "categories": "museum", "mode": "demo"}
    ).json()
    assert weather["metadata"]["mode"] == "demo"
    assert weather["metadata"]["source_url"] is None
    assert places["places"][0]["source_url"] is None
    assert client.get("/api/weather", params=weather_params(identifier)).status_code == 409
    assert not calls


def test_destination_local_date_uses_timezone():
    def reject_network(_request):
        raise AssertionError("demo must not use network")

    now = datetime(2027, 1, 31, 22, 30, tzinfo=UTC)  # Already February 1 in Istanbul.
    with TestClient(
        create_app(
            Settings(_env_file=None), transport=httpx.MockTransport(reject_network), now=lambda: now
        )
    ) as c:
        identifier = c.get("/api/destinations", params={"q": "İstanbul", "mode": "demo"})
        result = c.get(
            "/api/weather",
            params=weather_params(
                identifier.json()["destinations"][0]["id"], mode="demo", start_date="2027-01-31"
            ),
        ).json()
        assert result["days"][0]["reason"] == "outside_forecast_horizon"
        assert result["days"][1]["available"] is True


def test_429_honors_retry_after_and_does_not_retry_or_rotate(harness):
    client, calls, responses = harness
    responses["geocoding-api.open-meteo.com"] = httpx.Response(429, headers={"Retry-After": "120"})
    first = client.get("/api/destinations", params={"q": "Paris"})
    second = client.get("/api/destinations", params={"q": "Barcelona"})
    assert first.status_code == second.status_code == 429
    assert first.json()["retry_after_seconds"] == 120
    assert int(second.headers["Retry-After"]) > 0
    assert len(calls) == 1


@pytest.mark.parametrize(
    "response,code",
    [
        (httpx.Response(200, text="not json"), "provider_invalid_response"),
        (httpx.Response(200, content=b"x" * 2_000_001), "provider_response_too_large"),
        (httpx.ReadTimeout("timeout"), "provider_timeout"),
        (httpx.ConnectError("offline"), "provider_unavailable"),
    ],
)
def test_safe_provider_failures(harness, response, code):
    client, _, responses = harness
    responses["geocoding-api.open-meteo.com"] = response
    result = client.get("/api/destinations", params={"q": "Paris"})
    assert result.status_code == 503
    assert result.json()["code"] == code
    assert "Traceback" not in result.text


def test_transient_error_retries_at_most_once(harness):
    client, calls, responses = harness
    responses["geocoding-api.open-meteo.com"] = httpx.Response(503)
    result = client.get("/api/destinations", params={"q": "Paris"})
    assert result.status_code == 503
    assert len(calls) == 2


def test_retry_after_on_final_transient_failure_is_respected(harness):
    client, calls, responses = harness
    responses["geocoding-api.open-meteo.com"] = lambda _request: (
        httpx.Response(503) if len(calls) == 1
        else httpx.Response(503, headers={"Retry-After": "120"})
    )
    result = client.get("/api/destinations", params={"q": "Paris"})
    assert result.status_code == 503
    assert result.json()["retry_after_seconds"] == 120
    assert client.get("/api/destinations", params={"q": "Barcelona"}).status_code == 429
    assert len(calls) == 2


def test_process_call_budget_stops_uncached_requests():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={})

    settings = Settings(_env_file=None, provider_hourly_limit=1, meteo_min_interval_seconds=0)
    with TestClient(create_app(settings, transport=httpx.MockTransport(handler))) as client:
        assert client.get("/api/destinations", params={"q": "first"}).status_code == 200
        assert client.get("/api/destinations", params={"q": "first"}).status_code == 200
        result = client.get("/api/destinations", params={"q": "second"})
        assert result.status_code == 429
        assert result.json()["code"] == "local_request_limit"
        assert len(calls) == 1

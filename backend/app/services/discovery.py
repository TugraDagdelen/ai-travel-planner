import asyncio
import math
import time
import unicodedata
from collections import OrderedDict
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import ValidationError

from app.schemas.discovery import (
    Category,
    Destination,
    DestinationResponse,
    Mode,
    Place,
    PlacesResponse,
    SourceMetadata,
    WeatherDay,
    WeatherResponse,
)
from app.services.demo import DEMO_DESTINATIONS
from app.services.gateway import Gateway, ProviderError

CATEGORY_FILTERS = {
    "museum": ('nwr', '["tourism"="museum"]'),
    # Avoid every historic-tagged building in dense cities. These values are useful
    # visitor destinations and keep the public Overpass query within a sane budget.
    "historic": (
        'nwr',
        '["historic"~"^(monument|memorial|castle|archaeological_site|ruins|city_gate|fort|manor|palace)$"]',
    ),
    "park": ('nwr', '["leisure"="park"]'),
    "attraction": ('nwr', '["tourism"="attraction"]'),
    # Restaurant areas/buildings are numerous and nodes provide enough candidates.
    "restaurant": ('node', '["amenity"="restaurant"]'),
}
WIKIDATA_ROOTS = {
    "museum": ("Q33506",),
    "historic": ("Q839954",),
    "park": ("Q22698", "Q179049"),
    # Broad natural and settlement roots keep region-defining destinations such as
    # Termal, waterfalls, beaches and hot springs in small-city discovery.
    "attraction": (
        "Q570116",
        "Q3957",
        "Q34038",
        "Q23397",
        "Q177380",
        "Q40080",
        "Q8502",
    ),
    "restaurant": ("Q11707",),
}
WEATHER_FIELDS = {
    "temperature_2m_min": ("temperature_min", -100, 70, "°C"),
    "temperature_2m_max": ("temperature_max", -100, 70, "°C"),
    "precipitation_sum": ("precipitation_mm", 0, 3000, "mm"),
    "precipitation_probability_max": ("precipitation_probability", 0, 100, "%"),
    "weather_code": ("weather_code", 0, 99, "wmo code"),
}


def normalized(value: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(c)
    ).strip()


def distance(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (
        math.sin((p2 - p1) / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    )
    return round(6_371_000 * 2 * math.asin(math.sqrt(min(1, a))))


class DiscoveryService:
    def __init__(self, gateway: Gateway, now=None):
        self.gateway = gateway
        self.now = now or (lambda: datetime.now(UTC))
        self.destinations: OrderedDict[tuple[str, str], tuple[float, Destination]] = OrderedDict()

    def remember(self, destinations: list[Destination], mode: Mode):
        for destination in destinations:
            key = (mode, destination.id)
            self.destinations[key] = (time.monotonic() + 86400, destination)
            self.destinations.move_to_end(key)
        while len(self.destinations) > 500:
            self.destinations.popitem(last=False)

    def resolve(self, destination_id: str, mode: Mode) -> Destination:
        record = self.destinations.get((mode, destination_id))
        if not record or record[0] < time.monotonic():
            raise ProviderError("destination_expired", "geocoding", False)
        return record[1]

    @staticmethod
    def city_radius(destination: Destination) -> int:
        """Use a 50 km diameter around the selected city center."""
        return 25_000

    @staticmethod
    def metadata(mode: Mode, source: str, url: str, payload=None) -> SourceMetadata:
        return SourceMetadata(
            mode=mode,
            source="Synthetic demo" if mode == "demo" else source,
            source_url=None if mode == "demo" else url,
            fetched_at=payload.fetched_at if payload else None,
            cached=payload.cached if payload else False,
        )

    async def search(self, query: str, country_code: str | None, language: str, mode: Mode):
        if mode == "demo":
            term = normalized(query).replace("barselona", "barcelona")
            destinations = [
                d
                for d in DEMO_DESTINATIONS
                if term in normalized(d.name)
                and (not country_code or d.country_code == country_code)
            ]
            metadata = self.metadata(mode, "", "")
        else:
            params = {"name": query, "count": 10, "language": language, "format": "json"}
            if country_code:
                params["countryCode"] = country_code
            payload = await self.gateway.request("geocoding", params, ttl=86400)
            results = payload.data.get("results", [])
            if not isinstance(results, list):
                raise ProviderError("provider_invalid_response", "geocoding", False)
            destinations = []
            for item in results[:10]:
                try:
                    if not isinstance(item, dict):
                        continue
                    # Only populated places, not arbitrary terrain or administrative regions.
                    if not str(item.get("feature_code", "")).startswith("PPL"):
                        continue
                    ZoneInfo(item["timezone"])
                    identifier = int(item["id"])
                    if identifier <= 0:
                        continue
                    destination = Destination(
                        id=f"geonames:{identifier}",
                        name=item["name"][:120],
                        country=item.get("country", item["country_code"])[:120],
                        country_code=item["country_code"],
                        region=item.get("admin1"),
                        latitude=item["latitude"],
                        longitude=item["longitude"],
                        timezone=item["timezone"],
                        population=(
                            int(item["population"])
                            if type(item.get("population")) in (int, float)
                            and item["population"] >= 0
                            else None
                        ),
                        source_url=f"https://www.geonames.org/{identifier}",
                    )
                    if not country_code or destination.country_code == country_code:
                        destinations.append(destination)
                except (KeyError, ValueError, TypeError, ZoneInfoNotFoundError, ValidationError):
                    continue
            if results and not destinations:
                # A nonempty unusable response is not proof that the city does not exist.
                raise ProviderError("provider_invalid_response", "geocoding", False)
            metadata = self.metadata(
                mode,
                "Open-Meteo / GeoNames",
                "https://open-meteo.com/en/docs/geocoding-api",
                payload,
            )
        self.remember(destinations, mode)
        return DestinationResponse(destinations=destinations, metadata=metadata)

    async def weather(self, destination: Destination, start: date, end: date, mode: Mode):
        today = self.now().astimezone(ZoneInfo(destination.timezone)).date()
        horizon_end = today + timedelta(days=15)
        dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]
        supported = [d for d in dates if today <= d <= horizon_end]
        metadata = self.metadata(mode, "Open-Meteo", "https://open-meteo.com/")
        parsed: dict[date, dict] = {}
        if supported and mode == "demo":
            for index, day in enumerate(supported):
                parsed[day] = {
                    "temperature_min": 12 + index % 3,
                    "temperature_max": 19 + index % 4,
                    "precipitation_mm": 4 if index % 2 else 0,
                    "precipitation_probability": 70 if index % 2 else 10,
                    "weather_code": 61 if index % 2 else 1,
                }
        elif supported:
            payload = await self.gateway.request(
                "forecast",
                {
                    "latitude": destination.latitude,
                    "longitude": destination.longitude,
                    "timezone": destination.timezone,
                    "start_date": supported[0].isoformat(),
                    "end_date": supported[-1].isoformat(),
                    "daily": ",".join(WEATHER_FIELDS),
                    "temperature_unit": "celsius",
                    "precipitation_unit": "mm",
                },
                ttl=900,
            )
            metadata = self.metadata(mode, "Open-Meteo", "https://open-meteo.com/", payload)
            parsed = self.parse_weather(payload.data, destination.timezone)
        days = []
        for day in dates:
            values = parsed.get(day, {})
            available = any(v is not None for v in values.values())
            reason = (
                None
                if available
                else ("missing_data" if day in supported else "outside_forecast_horizon")
            )
            days.append(WeatherDay(date=day, available=available, reason=reason, **values))
        count = sum(day.available for day in days)
        return WeatherResponse(
            destination_id=destination.id,
            timezone=destination.timezone,
            days=days,
            status="ok" if count == len(days) else "partial" if count else "unavailable",
            metadata=metadata,
        )

    @staticmethod
    def parse_weather(data: dict, timezone: str) -> dict[date, dict]:
        try:
            if data.get("timezone") != timezone:
                raise ValueError("timezone mismatch")
            daily, units = data["daily"], data["daily_units"]
            times = daily["time"]
            if not isinstance(times, list) or len(times) > 16:
                raise ValueError("invalid dates")
            result = {}
            for index, time_value in enumerate(times):
                day = date.fromisoformat(time_value)
                if day in result:
                    raise ValueError("duplicate date")
                result[day] = {}
                for key, (field, minimum, maximum, unit) in WEATHER_FIELDS.items():
                    if units.get(key) != unit or not isinstance(daily[key], list):
                        raise ValueError("invalid units or series")
                    if len(daily[key]) != len(times):
                        raise ValueError("unaligned series")
                    value = daily[key][index]
                    if value is not None and (
                        type(value) not in (int, float)
                        or not math.isfinite(value)
                        or not minimum <= value <= maximum
                    ):
                        value = None
                    if key == "weather_code" and value is not None and value != int(value):
                        value = None
                    result[day][field] = value
            return result
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError("provider_invalid_response", "forecast", False) from exc

    async def places(
        self,
        destination: Destination,
        categories: list[Category],
        radius: int,
        mode: Mode,
        language: str = "tr",
    ):
        categories = sorted(set(categories))
        if mode == "demo":
            places = [
                Place(
                    id=f"demo:{category}:{variant + 1}",
                    name=f"Demo · {category} {variant + 1}",
                    category=category,
                    latitude=destination.latitude + (i * 2 + variant + 1) * 0.001,
                    longitude=destination.longitude + variant * 0.001,
                    coordinate_kind="synthetic",
                    distance_m=111 * (i * 2 + variant + 1),
                    classification_basis="synthetic",
                )
                for i, category in enumerate(categories)
                for variant in range(2)
                if 111 * (i * 2 + variant + 1) <= radius
            ]
            return PlacesResponse(
                destination_id=destination.id,
                places=places,
                radius_m=radius,
                metadata=self.metadata(mode, "", ""),
            )
        if self.gateway.settings.places_provider == "wikimedia":
            try:
                wikimedia = await self.wikimedia_places(
                    destination, categories, radius, mode, language
                )
            except ProviderError:
                # Keep one independent real-data fallback. Demo data is never mixed in.
                return await self.overpass_places(destination, categories, radius, mode)
            try:
                osm = await self.nominatim_places(
                    destination, categories, radius, mode, language
                )
            except ProviderError:
                try:
                    osm = await self.overpass_places(destination, categories, radius, mode)
                except ProviderError:
                    return wikimedia
            if not osm.places:
                return wikimedia
            combined = list(wikimedia.places)
            for candidate in osm.places:
                duplicate = any(
                    normalized(place.name) == normalized(candidate.name)
                    and place.category == candidate.category
                    and (
                        place.latitude is None
                        or place.longitude is None
                        or candidate.latitude is None
                        or candidate.longitude is None
                        or distance(
                            place.latitude,
                            place.longitude,
                            candidate.latitude,
                            candidate.longitude,
                        )
                        < 150
                    )
                    for place in combined
                )
                if not duplicate:
                    combined.append(candidate)
            combined.sort(
                key=lambda place: (
                    place.distance_m if place.distance_m is not None else 10**9,
                    place.name.casefold(),
                )
            )
            source = (
                "Wikipedia, Wikidata ve OpenStreetMap"
                if language == "tr"
                else "Wikipedia, Wikidata and OpenStreetMap"
            )
            return wikimedia.model_copy(
                update={
                    "places": combined[:100],
                    "truncated": wikimedia.truncated
                    or osm.truncated
                    or len(combined) > 100,
                    "skipped_records": wikimedia.skipped_records + osm.skipped_records,
                    "metadata": wikimedia.metadata.model_copy(
                        update={
                            "source": source,
                            "source_url": "https://www.openstreetmap.org/copyright",
                        }
                    ),
                }
            )
        return await self.overpass_places(destination, categories, radius, mode)

    async def nominatim_places(
        self,
        destination: Destination,
        categories: list[Category],
        radius: int,
        mode: Mode,
        language: str,
    ) -> PlacesResponse:
        terms = {
            "tr": {
                "museum": ("müze",),
                "historic": ("tarihi yer", "köşk", "anıt"),
                "park": ("park", "tabiat parkı", "mesire alanı"),
                "attraction": (
                    "turistik yer",
                    "termal",
                    "kaplıca",
                    "şelale",
                    "plaj",
                    "seyir noktası",
                ),
                "restaurant": ("restoran",),
            },
            "en": {
                "museum": ("museum",),
                "historic": ("historic site", "monument"),
                "park": ("park", "nature park", "picnic area"),
                "attraction": (
                    "tourist attraction",
                    "thermal spa",
                    "hot spring",
                    "waterfall",
                    "beach",
                    "viewpoint",
                ),
                "restaurant": ("restaurant",),
            },
        }[language]
        latitude_delta = radius / 111_320
        longitude_scale = max(0.2, math.cos(math.radians(destination.latitude)))
        longitude_delta = radius / (111_320 * longitude_scale)
        viewbox = ",".join(
            f"{value:.6f}"
            for value in (
                destination.longitude - longitude_delta,
                destination.latitude + latitude_delta,
                destination.longitude + longitude_delta,
                destination.latitude - latitude_delta,
            )
        )
        allowed_types = {
            "museum": {("tourism", "museum")},
            "historic": {
                ("historic", item)
                for item in (
                    "archaeological_site",
                    "castle",
                    "city_gate",
                    "fort",
                    "manor",
                    "memorial",
                    "monument",
                    "palace",
                    "ruins",
                )
            },
            "park": {("leisure", "park"), ("leisure", "garden")},
            "attraction": {
                ("tourism", "attraction"),
                ("tourism", "viewpoint"),
                ("tourism", "theme_park"),
                ("tourism", "picnic_site"),
                ("leisure", "spa"),
                ("natural", "hot_spring"),
                ("natural", "waterfall"),
                ("natural", "beach"),
                ("amenity", "public_bath"),
                ("place", "town"),
                ("place", "village"),
            },
            "restaurant": {("amenity", "restaurant")},
        }
        places: list[Place] = []
        skipped = 0
        payloads = []
        last_error: ProviderError | None = None
        for category in categories:
            for term in terms[category]:
                try:
                    payload = await self.gateway.request(
                        "nominatim_search",
                        {
                            "q": f"{term} {destination.name}",
                        "format": "jsonv2",
                        "limit": 30,
                        "addressdetails": 1,
                        "extratags": 1,
                        "namedetails": 1,
                        "accept-language": language,
                        "viewbox": viewbox,
                        "bounded": 1,
                        },
                        ttl=86400,
                    )
                except ProviderError as exc:
                    last_error = exc
                    continue
                payloads.append(payload)
                records = payload.data.get("results", [])
                if not isinstance(records, list):
                    skipped += 1
                    continue
                for record in records:
                    try:
                        source_type = (record["category"], record["type"])
                        if source_type not in allowed_types[category]:
                            continue
                        kind = record["osm_type"]
                        identifier = int(record["osm_id"])
                        if kind not in {"node", "way", "relation"} or identifier <= 0:
                            raise ValueError("invalid OSM identity")
                        namedetails = record.get("namedetails", {})
                        name = (
                            namedetails.get(f"name:{language}")
                            or record.get("name")
                            or namedetails.get("name")
                        )
                        if not isinstance(name, str) or not name.strip():
                            raise ValueError("missing place name")
                        lat, lon = float(record["lat"]), float(record["lon"])
                        meters = distance(
                            destination.latitude, destination.longitude, lat, lon
                        )
                        if meters > radius:
                            continue
                        identity = f"osm:{kind}:{identifier}"
                        if any(place.id == identity for place in places):
                            continue
                        display_name = record.get("display_name")
                        places.append(
                            Place(
                                id=identity,
                                name=name.strip()[:200],
                                category=category,
                                latitude=lat,
                                longitude=lon,
                                coordinate_kind=(
                                    "node" if kind == "node" else "geometry_center"
                                ),
                                distance_m=meters,
                                indoor=(
                                    "indoor"
                                    if category == "museum"
                                    else (
                                        "outdoor"
                                        if category in {"park", "attraction"}
                                        else "unknown"
                                    )
                                ),
                                classification_basis="osm_tag",
                                source_url=f"https://www.openstreetmap.org/{kind}/{identifier}",
                                description=(
                                    display_name.strip()[:600]
                                    if isinstance(display_name, str)
                                    else None
                                ),
                                tags={
                                    "osm_category": source_type[0],
                                    "osm_type": source_type[1],
                                },
                            )
                        )
                    except (KeyError, TypeError, ValueError, AttributeError):
                        skipped += 1
        if not payloads:
            if last_error is not None:
                raise last_error
            raise ProviderError("provider_unavailable", "nominatim")
        places.sort(
            key=lambda place: (
                place.distance_m if place.distance_m is not None else 10**9,
                place.name.casefold(),
            )
        )
        return PlacesResponse(
            destination_id=destination.id,
            places=places[:100],
            radius_m=radius,
            truncated=any(len(item.data.get("results", [])) >= 30 for item in payloads)
            or len(places) > 100,
            skipped_records=skipped,
            metadata=self.metadata(
                mode,
                "© OpenStreetMap contributors",
                "https://www.openstreetmap.org/copyright",
                payloads[-1],
            ),
        )

    async def overpass_places(
        self, destination: Destination, categories: list[Category], radius: int, mode: Mode
    ):
        elements = []
        payloads = []
        last_error: ProviderError | None = None
        category_order = ["museum", "historic", "park", "attraction", "restaurant"]
        latitude_delta = radius / 111_320
        longitude_scale = max(0.2, math.cos(math.radians(destination.latitude)))
        longitude_delta = radius / (111_320 * longitude_scale)
        bounds = (
            destination.latitude - latitude_delta,
            destination.longitude - longitude_delta,
            destination.latitude + latitude_delta,
            destination.longitude + longitude_delta,
        )
        bbox = ",".join(f"{value:.6f}" for value in bounds)
        for category in (item for item in category_order if item in categories):
            query = (
                "[out:json][timeout:15][maxsize:2097152];"
                f"{CATEGORY_FILTERS[category][0]}({bbox})"
                f'{CATEGORY_FILTERS[category][1]}["name"];'
                "out center 30;"
            )
            try:
                async with asyncio.timeout(12):
                    payload = await self.gateway.request(
                        "overpass", {"data": query}, ttl=3600
                    )
            except ProviderError as exc:
                last_error = exc
                continue
            except TimeoutError:
                last_error = ProviderError("provider_timeout", "overpass")
                continue
            batch = payload.data.get("elements")
            if not isinstance(batch, list):
                last_error = ProviderError("provider_invalid_response", "overpass", False)
                continue
            payloads.append(payload)
            elements.extend(batch)
        if not payloads:
            if last_error is not None:
                raise last_error
            raise ProviderError("provider_unavailable", "overpass")
        payload = payloads[-1]
        places, skipped = self.parse_places(elements[:150], destination, categories, radius)
        return PlacesResponse(
            destination_id=destination.id,
            places=places[:100],
            radius_m=radius,
            truncated=any(len(item.data.get("elements", [])) >= 30 for item in payloads)
            or len(elements) >= 150
            or len(places) > 100,
            skipped_records=skipped,
            metadata=self.metadata(
                mode,
                "© OpenStreetMap contributors",
                "https://www.openstreetmap.org/copyright",
                payload,
            ),
        )

    async def wikimedia_places(
        self,
        destination: Destination,
        categories: list[Category],
        radius: int,
        mode: Mode,
        language: str = "tr",
        allow_supplement: bool = True,
    ):
        wikipedia_geo = "wikipedia_geo_tr" if language == "tr" else "wikipedia_geo"
        wikipedia_details = (
            "wikipedia_details_tr" if language == "tr" else "wikipedia_details"
        )
        anchors = [(destination.latitude, destination.longitude)]
        scan_radius = radius
        if radius > 5000:
            longitude_scale = max(0.2, math.cos(math.radians(destination.latitude)))
            for fraction in (0.2, 0.5):
                offset_m = radius * fraction
                latitude_offset = offset_m / 111_320
                longitude_offset = offset_m / (111_320 * longitude_scale)
                anchors.extend(
                    [
                        (destination.latitude + latitude_offset, destination.longitude),
                        (destination.latitude - latitude_offset, destination.longitude),
                        (destination.latitude, destination.longitude + longitude_offset),
                        (destination.latitude, destination.longitude - longitude_offset),
                    ]
                )
            scan_radius = min(10000, round(radius * 0.8))

        geo_payloads = []
        pages = []
        scan_truncated = False
        geo_error: ProviderError | None = None
        for latitude, longitude in anchors:
            try:
                geo = await self.gateway.request(
                    wikipedia_geo,
                    {
                        "action": "query",
                        "generator": "geosearch",
                        "ggsprimary": "primary",
                        "ggsnamespace": 0,
                        "ggsradius": scan_radius,
                        "ggscoord": f"{latitude}|{longitude}",
                        "ggslimit": 100,
                        "prop": "coordinates|pageprops",
                        "colimit": "max",
                        "format": "json",
                        "formatversion": 2,
                    },
                    ttl=86400,
                )
            except ProviderError as exc:
                # One temporarily busy scan cell must not discard the other city zones.
                geo_error = exc
                continue
            geo_payloads.append(geo)
            batch = geo.data.get("query", {}).get("pages", [])
            if not isinstance(batch, list):
                raise ProviderError("provider_invalid_response", "wikimedia", False)
            pages.extend(batch)
            scan_truncated = scan_truncated or len(batch) >= 100
        if not geo_payloads:
            if geo_error is not None:
                raise geo_error
            raise ProviderError("provider_unavailable", "wikimedia")
        geo = geo_payloads[0]
        candidates: dict[str, tuple[int, str, float, float]] = {}
        skipped = 0
        for page in pages[:900]:
            try:
                page_id = int(page["pageid"])
                qid = page["pageprops"]["wikibase_item"]
                coordinates = page["coordinates"][0]
                name = page["title"].strip()[:200]
                lat, lon = float(coordinates["lat"]), float(coordinates["lon"])
                if (
                    page_id <= 0
                    or not name
                    or not isinstance(qid, str)
                    or not qid.startswith("Q")
                    or not qid[1:].isdigit()
                    or not -90 <= lat <= 90
                    or not -180 <= lon <= 180
                ):
                    raise ValueError("invalid Wikimedia place")
                candidates[qid] = (page_id, name, lat, lon)
            except (KeyError, IndexError, TypeError, ValueError, AttributeError):
                skipped += 1
        if not candidates:
            empty_response = PlacesResponse(
                destination_id=destination.id,
                places=[],
                radius_m=radius,
                skipped_records=skipped,
                metadata=self.metadata(
                    mode,
                    "Wikidata and Wikipedia contributors",
                    "https://www.wikidata.org/wiki/Wikidata:Licensing",
                    geo,
                ),
            )
            if language == "tr" and allow_supplement:
                try:
                    english = await self.wikimedia_places(
                        destination,
                        categories,
                        radius,
                        mode,
                        "en",
                        allow_supplement=False,
                    )
                except ProviderError:
                    return empty_response
                return english.model_copy(
                    update={
                        "metadata": english.metadata.model_copy(
                            update={"source": "İngilizce Wikipedia ile Wikidata"}
                        )
                    }
                )
            return empty_response
        roots = {
            qid: category for category in categories for qid in WIKIDATA_ROOTS[category]
        }
        root_values = " ".join(f"wd:{qid}" for qid in roots)
        bindings = []
        typed_payloads = []
        candidate_ids = list(candidates)
        for start in range(0, len(candidate_ids), 200):
            item_values = " ".join(
                f"wd:{qid}" for qid in candidate_ids[start : start + 200]
            )
            query = (
                "SELECT DISTINCT ?item ?root WHERE { "
                f"VALUES ?item {{ {item_values} }} VALUES ?root {{ {root_values} }} "
                "?item wdt:P31/wdt:P279* ?root. }"
            )
            typed = await self.gateway.request(
                "wikidata_types", {"query": query, "format": "json"}, ttl=86400
            )
            typed_payloads.append(typed)
            batch = typed.data.get("results", {}).get("bindings", [])
            if not isinstance(batch, list):
                raise ProviderError("provider_invalid_response", "wikimedia", False)
            bindings.extend(batch)
        typed = typed_payloads[-1]
        places: list[Place] = []
        identities: set[str] = set()
        for binding in bindings:
            try:
                qid = binding["item"]["value"].rsplit("/", 1)[-1]
                root = binding["root"]["value"].rsplit("/", 1)[-1]
                if qid in identities or qid not in candidates or root not in roots:
                    continue
                _page_id, name, lat, lon = candidates[qid]
                meters = distance(destination.latitude, destination.longitude, lat, lon)
                if meters > radius:
                    continue
                category = roots[root]
                identities.add(qid)
                places.append(
                    Place(
                        id=f"wikidata:{qid}",
                        name=name,
                        category=category,
                        latitude=lat,
                        longitude=lon,
                        coordinate_kind="node",
                        distance_m=meters,
                        indoor=(
                            "indoor"
                            if category == "museum"
                            else ("outdoor" if category == "park" else "unknown")
                        ),
                        classification_basis="category_inference",
                        source_url=f"https://www.wikidata.org/wiki/{qid}",
                        tags={"wikidata": qid, "wikidata_root": root},
                    )
                )
            except (KeyError, TypeError, ValueError, AttributeError):
                skipped += 1
        total_place_count = len(places)
        nearby_groups = {category: [] for category in categories}
        for place in places:
            nearby_groups[place.category].append(place)
        for values in nearby_groups.values():
            values.sort(
                key=lambda place: (
                    place.distance_m if place.distance_m is not None else 10**9,
                    place.id,
                )
            )
        places = []
        while any(nearby_groups.values()) and len(places) < 300:
            for category in categories:
                if nearby_groups[category] and len(places) < 300:
                    places.append(nearby_groups[category].pop(0))

        if places:
            try:
                by_page_id = {
                    candidates[place.id.split(":", 1)[1]][0]: place for place in places
                }
                page_ids = list(by_page_id)
                for start in range(0, len(page_ids), 50):
                    popularity = await self.gateway.request(
                        wikipedia_details,
                        {
                            "action": "query",
                            "pageids": "|".join(str(item) for item in page_ids[start : start + 50]),
                            "prop": "pageviews",
                            "pvipdays": 30,
                            "format": "json",
                            "formatversion": 2,
                        },
                        ttl=21600,
                    )
                    batch = popularity.data.get("query", {}).get("pages", [])
                    if not isinstance(batch, list):
                        raise ValueError("invalid Wikipedia popularity")
                    for page in batch:
                        place = by_page_id.get(page.get("pageid"))
                        pageviews = page.get("pageviews", {})
                        if place is not None and isinstance(pageviews, dict):
                            place.pageviews_30d = sum(
                                value
                                for value in pageviews.values()
                                if type(value) is int and value >= 0
                            )
            except (ProviderError, KeyError, TypeError, ValueError, AttributeError):
                # Popularity enriches ranking, but its absence must not turn verified
                # coordinates and categories into an outage.
                pass

        grouped = {category: [] for category in categories}
        for place in places:
            grouped[place.category].append(place)
        for values in grouped.values():
            values.sort(
                key=lambda place: (
                    -(place.pageviews_30d if place.pageviews_30d is not None else -1),
                    place.distance_m if place.distance_m is not None else 10**9,
                    place.id,
                )
            )
        places = []
        while any(grouped.values()) and len(places) < 100:
            for category in categories:
                if grouped[category] and len(places) < 100:
                    places.append(grouped[category].pop(0))

        if places:
            try:
                by_page_id = {
                    candidates[place.id.split(":", 1)[1]][0]: place for place in places
                }
                detail_pages = []
                page_ids = list(by_page_id)
                for start in range(0, len(page_ids), 50):
                    details = await self.gateway.request(
                        wikipedia_details,
                        {
                            "action": "query",
                            "pageids": "|".join(
                                str(item) for item in page_ids[start : start + 50]
                            ),
                            "prop": "extracts|pageimages|info",
                            "inprop": "url",
                            "exintro": 1,
                            "explaintext": 1,
                            "exsentences": 2,
                            "exlimit": "max",
                            "piprop": "thumbnail",
                            "pithumbsize": 480,
                            "pilimit": "max",
                            "format": "json",
                            "formatversion": 2,
                        },
                        ttl=21600,
                    )
                    batch = details.data.get("query", {}).get("pages", [])
                    if not isinstance(batch, list):
                        raise ValueError("invalid Wikipedia details")
                    detail_pages.extend(batch)
                for page in detail_pages:
                    place = by_page_id.get(page.get("pageid"))
                    if place is None:
                        continue
                    extract = page.get("extract")
                    full_url = page.get("fullurl")
                    thumbnail = page.get("thumbnail", {}).get("source")
                    if isinstance(extract, str) and extract.strip():
                        place.description = extract.strip()[:600]
                    if isinstance(full_url, str) and full_url.startswith("https://"):
                        place.source_url = full_url[:1000]
                    if isinstance(thumbnail, str) and thumbnail.startswith("https://"):
                        place.image_url = thumbnail[:1000]
            except (ProviderError, KeyError, TypeError, ValueError, AttributeError):
                pass
        response = PlacesResponse(
            destination_id=destination.id,
            places=sorted(
                places,
                key=lambda place: (
                    place.distance_m if place.distance_m is not None else 10**9,
                    place.name.casefold(),
                ),
            )[:100],
            radius_m=radius,
            truncated=scan_truncated or total_place_count > 100,
            skipped_records=skipped,
            metadata=self.metadata(
                mode,
                "Wikidata and Wikipedia contributors",
                "https://www.wikidata.org/wiki/Wikidata:Licensing",
                typed,
            ),
        )
        if language == "tr" and allow_supplement and len(response.places) < 20:
            try:
                english = await self.wikimedia_places(
                    destination,
                    categories,
                    radius,
                    mode,
                    "en",
                    allow_supplement=False,
                )
            except ProviderError:
                return response
            merged = {place.id: place for place in english.places}
            # Turkish records win when the same Wikidata identity exists in both editions.
            merged.update({place.id: place for place in response.places})
            combined = sorted(
                merged.values(),
                key=lambda place: (
                    place.distance_m if place.distance_m is not None else 10**9,
                    place.name.casefold(),
                ),
            )
            return response.model_copy(
                update={
                    "places": combined[:100],
                    "truncated": response.truncated
                    or english.truncated
                    or len(combined) > 100,
                    "skipped_records": response.skipped_records
                    + english.skipped_records,
                    "metadata": response.metadata.model_copy(
                        update={"source": "Türkçe ve İngilizce Wikipedia ile Wikidata"}
                    ),
                }
            )
        return response

    @staticmethod
    def parse_places(elements, destination, categories, radius):
        places: list[Place] = []
        identities = set()
        skipped = 0
        for element in elements:
            try:
                kind = element["type"]
                identifier = int(element["id"])
                if kind not in {"node", "way", "relation"} or identifier <= 0:
                    raise ValueError("invalid identity")
                tags = element["tags"]
                name = tags["name"].strip()[:200]
                if not name:
                    raise ValueError("missing name")
                matches = {
                    "museum": tags.get("tourism") == "museum",
                    "historic": bool(tags.get("historic")),
                    "park": tags.get("leisure") == "park",
                    "restaurant": tags.get("amenity") == "restaurant",
                    "attraction": tags.get("tourism") == "attraction",
                }
                category = next(
                    (
                        key for key, matches_tag in matches.items()
                        if matches_tag and key in categories
                    ),
                    None,
                )
                if category is None:
                    continue
                identity = f"osm:{kind}:{identifier}"
                if identity in identities:
                    continue
                identities.add(identity)
                point = element if kind == "node" else element.get("center", {})
                lat, lon = point.get("lat"), point.get("lon")
                valid_coordinates = (
                    type(lat) in (int, float)
                    and type(lon) in (int, float)
                    and math.isfinite(lat)
                    and math.isfinite(lon)
                    and -90 <= lat <= 90
                    and -180 <= lon <= 180
                )
                lat, lon = (lat, lon) if valid_coordinates else (None, None)
                meters = (
                    distance(destination.latitude, destination.longitude, lat, lon)
                    if valid_coordinates
                    else None
                )
                if meters is not None and meters > radius:
                    skipped += 1
                    continue
                if valid_coordinates and any(
                    normalized(p.name) == normalized(name)
                    and p.category == category
                    and p.latitude is not None
                    and distance(lat, lon, p.latitude, p.longitude) < 50
                    for p in places
                ):
                    continue
                indoor, basis = "unknown", "unknown"
                if tags.get("indoor") in {"yes", "no"}:
                    indoor = "indoor" if tags["indoor"] == "yes" else "outdoor"
                    basis = "osm_tag"
                elif category in {"museum", "park"}:
                    indoor = "indoor" if category == "museum" else "outdoor"
                    basis = "category_inference"
                places.append(
                    Place(
                        id=identity,
                        name=name,
                        category=category,
                        latitude=lat,
                        longitude=lon,
                        coordinate_kind=("node" if kind == "node" else "geometry_center")
                        if valid_coordinates
                        else "unknown",
                        distance_m=meters,
                        indoor=indoor,
                        classification_basis=basis,
                        source_url=f"https://www.openstreetmap.org/{kind}/{identifier}",
                        tags={
                            k: str(tags[k])[:120]
                            for k in ("tourism", "historic", "leisure", "amenity", "indoor")
                            if k in tags
                        },
                    )
                )
            except (KeyError, TypeError, ValueError, AttributeError):
                skipped += 1
        places.sort(
            key=lambda p: (p.distance_m if p.distance_m is not None else float("inf"), p.id)
        )
        return places, skipped

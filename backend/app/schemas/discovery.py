from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

Mode = Literal["live", "demo"]
Category = Literal["museum", "historic", "park", "attraction", "restaurant"]


class SourceMetadata(BaseModel):
    mode: Mode
    source: str
    source_url: str | None
    fetched_at: datetime | None
    cached: bool = False


class Destination(BaseModel):
    id: str
    name: str
    country: str
    country_code: str
    region: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str
    source_url: str | None = None


class DestinationResponse(BaseModel):
    destinations: list[Destination]
    metadata: SourceMetadata


class WeatherDay(BaseModel):
    date: date
    available: bool = False
    reason: Literal["outside_forecast_horizon", "missing_data"] | None = None
    temperature_min: float | None = None
    temperature_max: float | None = None
    precipitation_mm: float | None = None
    precipitation_probability: float | None = None
    weather_code: int | None = None


class WeatherResponse(BaseModel):
    destination_id: str
    timezone: str
    days: list[WeatherDay]
    status: Literal["ok", "partial", "unavailable"]
    units: dict[str, str] = {"temperature": "°C", "precipitation": "mm", "probability": "%"}
    metadata: SourceMetadata


class Place(BaseModel):
    id: str
    name: str
    category: Category
    latitude: float | None = None
    longitude: float | None = None
    coordinate_kind: Literal["node", "geometry_center", "unknown", "synthetic"]
    distance_m: int | None = None
    indoor: Literal["indoor", "outdoor", "unknown"] = "unknown"
    classification_basis: Literal["osm_tag", "category_inference", "unknown", "synthetic"]
    source_url: str | None = None
    tags: dict[str, str] = {}


class PlacesResponse(BaseModel):
    destination_id: str
    places: list[Place]
    radius_m: int
    result_limit: int = 40
    truncated: bool = False
    skipped_records: int = 0
    metadata: SourceMetadata

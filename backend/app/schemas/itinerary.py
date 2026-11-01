from datetime import UTC, date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.discovery import Destination, Mode, Place, SourceMetadata, WeatherDay
from app.schemas.trip import TripRequest

GenerationMode = Literal["ai", "deterministic", "demo"]
Period = Literal["morning", "afternoon", "evening"]


class GenerateTripRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request: TripRequest
    destination_id: str = Field(min_length=1, max_length=80)
    data_mode: Mode = "live"
    generation_mode: GenerationMode = "deterministic"
    idempotency_key: UUID

    @model_validator(mode="after")
    def modes_match(self) -> "GenerateTripRequest":
        if self.generation_mode == "demo" and self.data_mode != "demo":
            raise ValueError("demo_requires_demo_data")
        if self.generation_mode != "demo" and self.data_mode == "demo":
            raise ValueError("demo_data_requires_demo_generation")
        return self


class ProposedActivity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    period: Period
    place_id: str = Field(min_length=1, max_length=120)
    reason: str = Field(min_length=2, max_length=240)


class ProposedDay(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: date
    activities: list[ProposedActivity] = Field(min_length=1, max_length=3)
    alternative_place_ids: list[str] = Field(default_factory=list, max_length=2)

    @field_validator("alternative_place_ids")
    @classmethod
    def unique_alternatives(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("duplicate_alternative")
        return value


class PlanProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=2, max_length=120)
    days: list[ProposedDay] = Field(min_length=1, max_length=14)
    warnings: list[str] = Field(default_factory=list, max_length=8)


class ItineraryActivity(BaseModel):
    period: Period
    place: Place
    reason: str


class ItineraryDay(BaseModel):
    date: date
    weather: WeatherDay
    activities: list[ItineraryActivity]
    alternatives: list[Place] = []


class AgentActivity(BaseModel):
    kind: Literal["tool", "model", "validation", "storage", "reuse"]
    name: str
    status: Literal["success", "partial", "failed", "reused"]
    duration_ms: int = Field(ge=0)
    cached: bool = False
    summary: str = Field(max_length=240)


class RevisionEntry(BaseModel):
    instruction: str = Field(min_length=3, max_length=500)
    result_summary: str = Field(min_length=2, max_length=240)
    version: int = Field(ge=2)
    created_at: datetime


class EvidenceBundle(BaseModel):
    destination: Destination
    weather: list[WeatherDay]
    places: list[Place]
    sources: list[SourceMetadata]


class TripRecord(BaseModel):
    id: str
    title: str
    request: TripRequest
    destination: Destination
    generation_mode: GenerationMode
    data_mode: Mode
    days: list[ItineraryDay]
    sources: list[SourceMetadata]
    warnings: list[str] = []
    agent_activity: list[AgentActivity] = []
    revisions: list[RevisionEntry] = []
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime


class TripSummary(BaseModel):
    id: str
    title: str
    destination_name: str
    start_date: date
    end_date: date
    generation_mode: GenerationMode
    version: int
    updated_at: datetime


class TripList(BaseModel):
    trips: list[TripSummary]
    total: int


class ReviseTripRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    instruction: str = Field(min_length=3, max_length=500)


class RenameTripRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(min_length=2, max_length=120)


class StoredTripPayload(BaseModel):
    record: TripRecord
    evidence: EvidenceBundle
    revision_instructions: list[str] = Field(default_factory=list, max_length=20)
    idempotency_key: str | None = Field(default=None, max_length=36)


def utc_now() -> datetime:
    return datetime.now(UTC)

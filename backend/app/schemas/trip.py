from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Interest = Literal["culture", "nature", "food", "art"]


class TripRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    destination: str = Field(min_length=2, max_length=120)
    start_date: date
    end_date: date
    interests: list[Interest] = Field(min_length=1, max_length=4)
    budget: Literal["economy", "balanced", "flexible"] = "balanced"
    pace: Literal["relaxed", "balanced", "active"] = "balanced"
    language: Literal["tr", "en"] = "tr"
    notes: str = Field(default="", max_length=1000)

    @field_validator("interests")
    @classmethod
    def distinct_interests(cls, value: list[Interest]) -> list[Interest]:
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def valid_dates(self) -> "TripRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_before_start")
        if self.duration_days > 14:
            raise ValueError("trip_too_long")
        return self

    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days + 1


class ValidatedTripRequest(BaseModel):
    request: TripRequest
    duration_days: int
    status: Literal["preferences_validated"] = "preferences_validated"
    itinerary_generated: Literal[False] = False

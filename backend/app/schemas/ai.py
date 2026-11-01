from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ConnectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: Literal["tr", "en"] = "tr"


class ConnectionReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ok"]
    message: str = Field(min_length=1, max_length=240)


class ConnectionResult(BaseModel):
    mode: Literal["live"] = "live"
    status: Literal["connected"] = "connected"
    model: str
    message: str
    checked_at: datetime
    itinerary_generated: Literal[False] = False
    tool_calls_executed: Literal[0] = 0


class AICapability(BaseModel):
    enabled: bool
    reason: str
    model: str
    key_configured: bool
    account_verification: Literal["unverified", "operator_attested"]
    live_verified_this_process: bool
    last_success_at: datetime | None = None
    policy_reviewed_at: str = "2026-10-30"


class ResearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["google_maps", "google_search"]


class ResearchCapability(BaseModel):
    enabled: Literal[False] = False
    requested: bool
    reason: Literal["disabled_by_configuration", "not_free_for_reviewed_model"]


class ResearchResult(BaseModel):
    provider: Literal["google_maps", "google_search"]
    status: Literal["unavailable"] = "unavailable"
    reason: str
    fallback: Literal["osm_discovery"] = "osm_discovery"
    citations: list[str] = Field(default_factory=list)
    source_support: None = None
    # No content or ranking score is fabricated when the source is unavailable.

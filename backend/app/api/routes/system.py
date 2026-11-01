from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["System"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["ai-travel-planner"] = "ai-travel-planner"
    version: str = "0.6.0"
    phase: int = 6


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Local process health only; never contacts external providers."""
    return HealthResponse()


@router.get("/capabilities")
def capabilities(request: Request) -> dict:
    providers = {
        "gemini": request.app.state.gemini.capability().model_dump(mode="json"),
        **{
            key: adapter.capability().model_dump()
            for key, adapter in request.app.state.research.items()
        },
        **{
            name: {"enabled": True, "reason": "integration_ready_not_a_reachability_check"}
            for name in ("open_meteo", "overpass")
        },
    }
    return {
        "phase": 6,
        "demo_available": True,
        "max_trip_days": request.app.state.settings.max_trip_days,
        "preference_validation": True,
        "itinerary_generation": True,
        "function_calling": request.app.state.gemini.capability().enabled,
        "persistence": True,
        "providers": providers,
    }

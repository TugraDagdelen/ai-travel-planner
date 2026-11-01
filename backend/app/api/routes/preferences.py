from fastapi import APIRouter, HTTPException, Request

from app.schemas.trip import TripRequest, ValidatedTripRequest

router = APIRouter(prefix="/api/trip-requests", tags=["Trip preferences"])


@router.post("/validate", response_model=ValidatedTripRequest)
def validate_preferences(payload: TripRequest, request: Request) -> ValidatedTripRequest:
    """Validate preferences without generating, saving, or calling providers."""
    if payload.duration_days > request.app.state.settings.max_trip_days:
        raise HTTPException(status_code=422, detail="trip_too_long")
    return ValidatedTripRequest(request=payload, duration_days=payload.duration_days)

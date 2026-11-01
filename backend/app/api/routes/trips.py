from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response, status

from app.schemas.itinerary import (
    GenerateTripRequest,
    RenameTripRequest,
    ReviseTripRequest,
    TripList,
    TripRecord,
    utc_now,
)

router = APIRouter(prefix="/api/trips", tags=["Trips"])


@router.post("/generate", response_model=TripRecord, status_code=status.HTTP_201_CREATED)
async def generate(body: GenerateTripRequest, request: Request):
    return await request.app.state.itineraries.generate(body)


@router.get("", response_model=TripList)
def list_trips(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return request.app.state.trips.list(limit, offset)


@router.get("/{trip_id}", response_model=TripRecord)
def get_trip(trip_id: str, request: Request):
    stored = request.app.state.trips.get(trip_id)
    if not stored:
        raise HTTPException(404, "trip_not_found")
    return stored.record


@router.post("/{trip_id}/revise", response_model=TripRecord)
async def revise(trip_id: str, body: ReviseTripRequest, request: Request):
    try:
        return await request.app.state.itineraries.revise(trip_id, body.instruction)
    except KeyError:
        raise HTTPException(404, "trip_not_found") from None


@router.patch("/{trip_id}", response_model=TripRecord)
def rename(trip_id: str, body: RenameTripRequest, request: Request):
    stored = request.app.state.trips.get(trip_id)
    if not stored:
        raise HTTPException(404, "trip_not_found")
    stored.record.title = body.title
    stored.record.version += 1
    stored.record.updated_at = utc_now()
    request.app.state.trips.save(stored)
    return stored.record


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(trip_id: str, request: Request):
    if not request.app.state.trips.delete(trip_id):
        raise HTTPException(404, "trip_not_found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

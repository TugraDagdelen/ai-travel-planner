from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request

from app.schemas.discovery import (
    Category,
    DestinationResponse,
    Mode,
    PlacesResponse,
    WeatherResponse,
)

router = APIRouter(prefix="/api", tags=["Discovery"])


@router.get("/destinations", response_model=DestinationResponse)
async def destinations(
    request: Request,
    q: Annotated[str, Query(min_length=2, max_length=120)],
    country_code: Annotated[str | None, Query(pattern="^[A-Z]{2}$")] = None,
    language: Literal["tr", "en"] = "tr",
    mode: Mode = "live",
):
    query = q.strip()
    if len(query) < 2:
        raise HTTPException(422, "invalid_destination_query")
    return await request.app.state.discovery.search(query, country_code, language, mode)


@router.get("/weather", response_model=WeatherResponse)
async def weather(
    request: Request,
    destination_id: Annotated[str, Query(min_length=1, max_length=80)],
    start_date: date,
    end_date: date,
    mode: Mode = "live",
):
    duration = (end_date - start_date).days + 1
    if not 1 <= duration <= request.app.state.settings.max_trip_days:
        raise HTTPException(422, "invalid_date_range")
    service = request.app.state.discovery
    destination = service.resolve(destination_id, mode)
    return await service.weather(destination, start_date, end_date, mode)


@router.get("/places", response_model=PlacesResponse)
async def places(
    request: Request,
    destination_id: Annotated[str, Query(min_length=1, max_length=80)],
    categories: Annotated[list[Category], Query(min_length=1, max_length=5)],
    radius_m: Annotated[int, Query(ge=250, le=10000)] = 10000,
    mode: Mode = "live",
):
    service = request.app.state.discovery
    destination = service.resolve(destination_id, mode)
    return await service.places(destination, categories, radius_m, mode)

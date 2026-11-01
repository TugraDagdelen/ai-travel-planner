from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException

from app.api.routes import ai, discovery, preferences, system, trips
from app.core.config import Settings
from app.db import create_database
from app.models import Base
from app.repository import TripRepository
from app.services.discovery import DiscoveryService
from app.services.gateway import Gateway, ProviderError
from app.services.gemini import AIError, GeminiService
from app.services.itinerary import ItineraryService
from app.services.research import GoogleMapsResearch, GoogleSearchResearch


def create_app(
    settings: Settings | None = None,
    *,
    transport=None,
    now=None,
    gemini_transport=None,
    frontend_dist: Path | None = None,
) -> FastAPI:
    settings = settings or Settings()
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        engine, session_factory = create_database(settings.database_url)
        Base.metadata.create_all(engine)
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(20, connect=5),
            follow_redirects=False,
            headers={"User-Agent": "Rota-Educational-Local/0.6", "Accept": "application/json"},
            transport=transport,
        ) as client:
            application.state.discovery = DiscoveryService(Gateway(client, settings), now=now)
            application.state.gemini = GeminiService(settings, gemini_transport)
            application.state.trips = TripRepository(session_factory)
            application.state.itineraries = ItineraryService(
                settings,
                application.state.discovery,
                application.state.gemini,
                application.state.trips,
            )
            application.state.research = {
                "google_maps": GoogleMapsResearch(settings),
                "google_search": GoogleSearchResearch(settings),
            }
            try:
                yield
            finally:
                await application.state.gemini.aclose()
                engine.dispose()

    application = FastAPI(
        title="AI Travel Planner API",
        version="0.6.0",
        lifespan=lifespan,
        description="Bounded itinerary generation from live or explicit demo evidence.",
    )
    application.state.settings = settings
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @application.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, exc: RequestValidationError) -> JSONResponse:
        # Omit raw input: notes and other user content must not be echoed into errors.
        return JSONResponse(
            status_code=422,
            content={
                "code": "validation_error",
                "message": "Please check the submitted preferences.",
                "retryable": False,
                "details": [
                    {"field": ".".join(map(str, e["loc"][1:])), "type": e["type"]}
                    for e in exc.errors()
                ],
            },
        )

    @application.exception_handler(HTTPException)
    async def http_error(_request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": str(exc.detail), "message": str(exc.detail), "retryable": False},
        )

    @application.exception_handler(ProviderError)
    async def provider_error(_request: Request, exc: ProviderError) -> JSONResponse:
        status = (
            409
            if exc.code == "destination_expired"
            else (429 if exc.code in {"provider_rate_limited", "local_request_limit"} else 503)
        )
        return JSONResponse(
            status_code=status,
            headers={"Retry-After": str(exc.retry_after)} if exc.retry_after else {},
            content={
                "code": exc.code,
                "message": "Data source unavailable; please try again later.",
                "retryable": exc.retryable,
                "provider": exc.provider,
                "retry_after_seconds": exc.retry_after,
            },
        )

    @application.exception_handler(AIError)
    async def ai_error(_request: Request, exc: AIError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status,
            headers={"Retry-After": str(exc.retry_after)} if exc.retry_after else {},
            content={
                "code": exc.code,
                "message": "The requested itinerary operation could not be completed.",
                "retryable": exc.status in {429, 503},
                "retry_after_seconds": exc.retry_after,
            },
        )

    application.include_router(ai.router)
    application.include_router(system.router)
    application.include_router(preferences.router)
    application.include_router(discovery.router)
    application.include_router(trips.router)

    # Production can run as one same-origin service. API routes stay authoritative,
    # while React Router paths fall back to the built index page.
    static_root = (frontend_dist or Path(__file__).resolve().parents[2] / "frontend" / "dist")
    static_root = static_root.resolve()
    index_file = static_root / "index.html"
    if index_file.is_file():

        @application.get("/{full_path:path}", include_in_schema=False)
        async def frontend(full_path: str):
            if full_path == "api" or full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="Not Found")
            candidate = (static_root / full_path).resolve()
            if static_root in candidate.parents and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(index_file)

    return application


app = create_app()

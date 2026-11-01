from fastapi import APIRouter, Request

from app.schemas.ai import ConnectionRequest, ConnectionResult, ResearchRequest, ResearchResult

router = APIRouter(prefix="/api", tags=["AI connection"])


@router.get("/ai/status")
def status(request: Request):
    return {
        "gemini": request.app.state.gemini.capability(),
        "research": {
            key: adapter.capability() for key, adapter in request.app.state.research.items()
        },
        "itinerary_generation": True,
        "function_calling": request.app.state.gemini.capability().enabled,
    }


@router.post("/ai/check", response_model=ConnectionResult)
async def check(body: ConnectionRequest, request: Request):
    return await request.app.state.gemini.check(body.language)


@router.post("/research", response_model=ResearchResult)
async def research(body: ResearchRequest, request: Request):
    return await request.app.state.research[body.provider].research()

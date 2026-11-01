from app.core.config import Settings
from app.schemas.ai import ResearchCapability, ResearchResult


class GoogleMapsResearch:
    provider = "google_maps"

    def __init__(self, settings: Settings):
        self.requested = settings.enable_google_maps_grounding

    def capability(self) -> ResearchCapability:
        # Official pricing reviewed 2026-10-30: no API free tier for the selected model.
        # Flags never bypass this gate. No SDK tool is instantiated or advertised.
        return ResearchCapability(
            requested=self.requested,
            reason="not_free_for_reviewed_model" if self.requested else "disabled_by_configuration",
        )

    async def research(self) -> ResearchResult:
        return ResearchResult(provider=self.provider, reason=self.capability().reason)


class GoogleSearchResearch(GoogleMapsResearch):
    provider = "google_search"

    def __init__(self, settings: Settings):
        self.requested = settings.enable_google_search_grounding

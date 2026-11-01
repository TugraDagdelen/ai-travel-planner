# Teacher demonstration — 6–8 minutes

This script is reproducible without API keys or external providers.

1. **Architecture (45 seconds).** Open the README diagram. Explain React → FastAPI → allowlisted tools → validation → SQLite. Point out that demo mode is explicitly synthetic and never a fallback disguised as live data.
2. **Preferences (45 seconds).** Start the app and enter `Paris, France`, dates `2026-11-03` to `2026-11-04`, culture and food. Submit to show shared frontend/backend validation.
3. **Ambiguous destination (45 seconds).** Select **Offline demo**, search Paris, and show France and Texas as separate choices. Choose France. Mention that no city is guessed automatically.
4. **Evidence (60 seconds).** Show date-aligned weather, place categories, coordinate caveats and the synthetic-source label. Explain that unavailable weather is left unavailable.
5. **Generation (75 seconds).** Generate the demo itinerary. Show the daily explanations, interactive list/marker selection, activity record and local-save badge. Explain idempotency and backend validation.
6. **Persistence and revision (60 seconds).** Open the saved trip, request `2. günü değiştir`, and show version 2 plus revision history. Confirm that day 1 stays unchanged.
7. **CRUD and resilience (45 seconds).** Open My Trips, rename the title, then show the delete confirmation without completing it if the record should be kept. Explain that a tile failure leaves the itinerary usable.
8. **Quality evidence (45 seconds).** Show `scripts/verify.ps1`, the offline GitHub Actions workflow, test counts and repository safety scan. State the live limitations: Gemini has no configured eligible key here, and Overpass was not reachable during the recorded live check.

## Suggested closing

“The project does not claim that AI output is evidence. Providers return evidence, the bounded model proposes a plan from allowlisted results, and the backend validates every successful save. The same journey remains demonstrable offline through clearly labelled synthetic fixtures.”

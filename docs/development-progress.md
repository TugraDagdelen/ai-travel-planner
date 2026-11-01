# Development progress

Updated: **2026-11-01**, version **0.6.0**.

| Phase | Status | Evidence / remaining work |
|---|---|---|
| 1 — Foundation | Complete | Real React → FastAPI validation; responsive TR/EN UI; dependencies and setup docs |
| 2 — Free data integrations | Implemented | City/weather/place APIs, provenance, caching, budgets, explicit demo and UI. Open-Meteo live verified; Overpass live unavailable here |
| 3 — Gemini and optional research | Implemented, connection live verified | Official SDK connection path returned `connected` locally and from Docker with an operator-confirmed Free Tier project; no key stored. Grounding remains disabled |
| 4 — Agent and itineraries | Implemented, offline agent verified | Bounded function calling, validated itinerary, SQLite and evidence-reusing revisions; full live tool-calling itinerary remains provider-dependent |
| 5 — Complete product | Complete | Leaflet route, daily timeline/weather, citations, saved-trip CRUD UI and revision history |
| 6 — Final portfolio QA | Complete | Offline end-to-end journey, real screenshots, repository scan, clean-source install and GitHub-ready docs |

## Phase 6 delivery

- Added fixture-backed full demo journeys at the API and React screen levels; neither can contact a provider.
- Added explicit map/timeline selection and citation/navigation-link coverage.
- Captured reviewed desktop and 390 × 844 mobile screenshots from the real local app; mobile QA found and fixed an overflowing management action.
- Added `scripts/verify.ps1` for one-command repository scan, backend checks and frontend checks.
- Added a CI repository-safety job, explicit TypeScript check and cache-free pytest execution.
- Added purpose/learning objectives, function-calling sequence, attribution/data-use notes, roadmap, MIT license and teacher demonstration script.
- Verified a clean source extraction and dependency installation separately from the development directories.
- 83 backend and 25 frontend tests pass; repository scan, lint, dependency checks, typecheck and production build pass.

## Phase 5 delivery

- Shared itinerary detail renders daily weather, recommendation reasons, alternatives, provenance and factual agent activity.
- Lazy-loaded React Leaflet map keeps list interaction usable when map tiles fail and omits navigation for synthetic coordinates.
- “My Trips” includes loading/error/empty/list/detail views, reopen, inline rename and confirmed delete.
- Revision chat keeps instruction/result/version history; deterministic/demo commands can target one day while preserving all other days.
- Generation UUIDs are idempotent under duplicate submits and serialized server-side before persistence.
- 79 backend and 22 frontend tests pass; lint, dependency check and production build pass.

## Phase 4 delivery

- Allowlisted `get_weather` and `search_places` registry with strict Pydantic arguments, request-scoped cache and factual activity records.
- Manual Gemini function loop with automatic execution disabled, 6-step/6-tool/75-second limits and preserved provider quota handling.
- Model output contains only dates, returned place IDs and explanations; the server materializes provider-owned names, coordinates and sources.
- Deterministic alternative uses documented interest/source/distance/weather scoring and refuses insufficient evidence.
- Exact date, unique period, known ID, alternative and no-duplicate checks run before every save/revision.
- SQLAlchemy-backed local SQLite create/list/read/rename/delete storage with versioned revisions.
- React planner generation/revision panel distinguishes AI, deterministic and synthetic demo behavior.
- Phase 4 coverage remains in the full Phase 5 suite.

## Phase 3 delivery

- Official `google-genai` SDK 2.34.0 with one fixed, structured connection request.
- Reviewed model allowlist contains only `gemini-3.5-flash-lite`; arbitrary aliases and paid models fail closed.
- Calls require free-only mode, a server-side key and explicit operator confirmation of an unbilled Free-tier project.
- Safe status and connection routes; keys and provider error details are never returned.
- Process-local daily/minute budgets, one concurrent call, overall timeout, bounded response, no SDK retries and quota cooldown.
- Output requires valid structured JSON, one normal candidate and no function call. A connection check never becomes an itinerary.
- Google Maps/Search adapters independently return unavailable with OSM fallback; flags cannot bypass the reviewed free-tier decision.
- Turkish/English connection panel separates a read-only status check from the explicit live model request.
- The bounded Gemini connection check returned `connected` locally and inside Docker on 2026-11-01 with an operator-confirmed Free Tier project; the key remains local and ignored.
- Phase 3 coverage remains in the full Phase 4 suite.

## Earlier Phase 2 delivery

- Explicit city selection with country/region/time-zone disambiguation.
- Weather preserves requested dates, validates units and series, and marks missing/out-of-horizon values.
- Bounded OSM queries with stable IDs, links, attribution and coordinate/classification evidence.
- Memory cache, serialized requests, timeouts, limited retries and local call budgets.
- Independent weather/place failures; city/mode changes cancel and ignore stale results.
- Opt-in demo is clearly synthetic and isolated from live provider calls.
- Phase 2 discovery coverage remains in the full suite. Details: [testing](testing.md).
- Desktop and 390 × 844 mobile discovery flow inspected; real local backend served demo responses.

## Remaining limits

The earlier live Overpass query timed out and live place retrieval has not yet been demonstrated here. The app reports failure and offers an explicit demo choice. It now tries one documented public fallback after a transport or transient service failure, but never after rate limiting; this behavior is covered offline and still needs a live probe.

The Gemini connection path is live-verified with the user's eligible local key. The complete tool loop remains verified through an offline fake-model contract and real parser/provider fixtures; a connection check alone does not prove a full live itinerary. Draft forms, caches, limits and selected-city IDs reset with the corresponding process. Process-local limits are not provider billing controls. OpenStreetMap tiles and external source/navigation links still require internet; their failure does not remove the saved itinerary.

The public GitHub repository and remote GitHub Actions run are complete. Docker production serving is verified locally with a named SQLite volume. No Render service was created, and Google grounding remains disabled. The Render Free Blueprint remains optional; hosted SQLite would be explicitly ephemeral. The original specification remains in `CODEX_MASTER_PROMPT.md`.

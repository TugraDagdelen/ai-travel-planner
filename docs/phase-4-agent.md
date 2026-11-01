# Phase 4 — bounded itinerary agent

Updated: **2026-11-01**. The implementation is local and single-user. Automated tests remain offline. A complete live two-day Paris itinerary was also verified in Docker with the operator-confirmed Free Tier key, Open-Meteo weather and Wikimedia/Wikidata places.

## Generation modes

| Mode | Data | Model call | Persistence |
|---|---|---|---|
| `ai` | Live Open-Meteo + Wikimedia/Wikidata (Overpass fallback) | Gemini, only after free-tier gates pass | SQLite |
| `deterministic` | Live Open-Meteo/OSM | None | SQLite |
| `demo` | Explicit synthetic fixtures | None | SQLite, clearly labelled demo |

Modes never change automatically. `demo` requires `data_mode=demo`; the other modes require `data_mode=live`. Provider or model failures stay visible instead of silently producing synthetic results.

## Function-calling loop

The server uses the official `google-genai` SDK with automatic function execution disabled. The model first receives two declarations: `get_weather` and `search_places`. Each requested call is restricted to the chosen destination, exact dates, server-owned categories and a 10 km city-wide radius, then dispatched by the local registry. Tool responses return to the model; after both evidence tools complete, a separate no-tool turn requests the schema-constrained final JSON. Separating function calling from structured output avoids the model/API request rejection seen when both modes were combined.

The whole run is limited to 6 model turns, 6 tool calls and 75 seconds by default. The SDK has no automatic retry. Process-local minute/day budgets, one concurrent Gemini request, quota cooldown, endpoint/model allowlists and a 256 KiB transport response cap remain active. Unknown tools, invalid arguments, incomplete evidence, malformed model JSON, step/tool limits and timeouts fail before storage.

## Output validation

The model returns only a proposal: title, exact dates, time periods, returned `place_id` values, short reasons and optional alternative IDs. The backend owns all names, categories, coordinates, links and source metadata. Before materializing the response it checks:

- every requested date appears exactly once and in order;
- each day has one to three activities with unique periods;
- every place and alternative exists in the retrieved evidence;
- a place is not repeated across the itinerary;
- an alternative is not also a scheduled activity that day;
- both weather and place tools completed.

Nothing is saved when a check fails.

## Deterministic planner

The non-AI planner ranks only returned places. Available factors are interest/category fit (35), source/classification support (20), distance (20) and rain/indoor suitability (15). Missing factors are omitted and remaining weights are renormalized. Budget has no weight because current providers do not supply reliable price evidence. Ties use stable place IDs. It reserves at least one unused place for every remaining day and refuses to invent or repeat places when evidence is insufficient.

Weather is date aligned. Rain is detected from precipitation probability, precipitation amount or WMO rain/storm codes. An indoor alternative is attached only when the provider evidence classifies a still-unused place as indoor. Otherwise no alternative is fabricated.

## SQLite and revisions

SQLAlchemy creates one local `trips` table. Each row includes indexed summary fields and one Pydantic-validated JSON payload containing the request, final itinerary, evidence, provenance, activity log and revision instructions. Create/update/delete operations use transactions. The database is excluded from Git.

AI revision receives the current proposal and saved allowlisted place IDs, makes no discovery-provider call and rejects any attempted function call. Deterministic/demo revision is intentionally limited and predictable: it swaps the first two saved stops. Both paths re-run the same itinerary consistency checks, increment the version and append a `saved_evidence` activity entry.

## API

- `POST /api/trips/generate`
- `GET /api/trips`
- `GET /api/trips/{id}`
- `POST /api/trips/{id}/revise`
- `PATCH /api/trips/{id}`
- `DELETE /api/trips/{id}`

Generated trips expose a factual activity log for tool, model, validation, storage and evidence-reuse steps. Secrets, raw provider error bodies and hidden model reasoning are never returned or stored.

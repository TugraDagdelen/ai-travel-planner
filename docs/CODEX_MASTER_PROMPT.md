# AI Travel Planner — Codex Master Prompt

> Kullanım: Bu dosyayı Codex'e ekle ve “Bu dosyadaki talimatlara göre Aşama 1'i uygula” yaz. Prompt İngilizcedir; uygulama Türkçe ve İngilizceyi desteklemeli, geliştirme açıklamaları Türkçe olmalıdır.
>
> Kaynak notu: Önceki “Proje Yol Haritası” konuşmasının aktarımında master promptun yazı bloğu eksik olduğundan bu dosya, erişilebilen ayrıntılı yol haritası ve son kullanıcı isteği temel alınarak yeniden oluşturulmuştur. Birebir transkript değildir. Ücretsiz servis koşulları uygulama sırasında yeniden doğrulanmalıdır.

---

## 1. Your role and objective

Act as a senior full-stack engineer and a clear technical mentor. Build **AI Travel Planner**, an individual AI education project that will also become a well-documented GitHub portfolio project.

The application must demonstrate Python, real external API integrations, an LLM, genuine function calling, a React frontend, and a FastAPI backend. The central learning outcome is that the model requests tools, the backend executes those tools, and the model builds an itinerary from their results.

Deliver working software incrementally. Explain important implementation decisions in Turkish, keep code identifiers in English, and make the product usable in Turkish and English. Do not replace the agreed stack with Streamlit, Next.js, a hosted app builder, or a paid AI service.

Read the existing repository and its applicable instructions before changing files. Preserve unrelated work. If the repository is empty, establish the structure below. Use compatible stable dependencies and record the versions actually installed; consult official documentation rather than copying obsolete setup commands.

## 2. Non-negotiable free-service policy

This is a local, educational, non-commercial project. **No paid APIs, billing activation, paid upgrades, credit-card requirements, or trial credits that can expire into paid usage.** A published free allowance attached to a paid billing account is not sufficient for this project.

- Use Gemini only through a confirmed eligible free-tier project and a model supporting function calling. The originally preferred model is `gemini-2.5-flash`; verify its current availability and eligibility before choosing it. Keep the model configurable. If unavailable, document a suitable verified free alternative within Gemini, or leave live AI unavailable rather than silently switching to paid access.
- Model tokens, Google Search grounding, and Google Maps grounding are separate capabilities. Verify each independently for the exact model, account tier, region, and current terms. Never assume free model inference means free grounding.
- **Google Maps/Search grounding must be disabled by default.** Enable each only when official documentation and the user's project eligibility establish genuinely free use without billing activation. If that cannot be established, keep it disabled and implement the OSM-based path.
- Do not use billable Google Places, Routes, Directions, Geocoding, Maps JavaScript, Vertex AI, OpenAI, or other paid APIs as a fallback.
- Never enable billing, upgrade a project, rotate accounts or keys to evade quotas, or automatically migrate to a paid model.
- Enforce bounded request counts, tool iterations, timeouts, and response sizes. Exhausted quotas must produce a clear message and an appropriate fallback, never a paid retry.
- An application configuration flag or budget counter does not prove an account cannot incur charges. Document this limitation and require appropriate free-tier account setup before live calls. If account status cannot be verified programmatically, explain the provider-console check without requesting secrets in chat.
- Use caching only where the relevant provider permits it. Respect retention, attribution, licensing, and public-service usage limits.
- Local development and a local demonstration must remain possible without paid hosting. Do not provision or deploy paid infrastructure.

Before implementing live integrations, create `docs/free-services.md` with a dated table of provider, purpose, model if relevant, official evidence URL, applicable limits, account requirements, verification status, and fallback. Mark unknown conditions as unknown, not free. Do not hard-code old claims such as “500 free requests per day.”

Official starting points:

- [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Gemini function calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [Google Search grounding](https://ai.google.dev/gemini-api/docs/google-search)
- [Google Maps grounding](https://ai.google.dev/gemini-api/docs/maps-grounding)
- [Gemini API additional terms](https://ai.google.dev/gemini-api/terms)

These are sources to recheck during implementation, not a guarantee of future availability.

## 3. Required technology stack

| Layer | Technology and purpose |
|---|---|
| Frontend | React, Vite, TypeScript in strict mode |
| Styling | Tailwind CSS, responsive reusable components, Lucide icons if useful |
| Navigation and requests | React Router and a typed Axios client |
| Interactive map | Leaflet with React Leaflet and appropriately used OpenStreetMap tiles |
| Backend | Python, FastAPI, Uvicorn |
| Validation/configuration | Pydantic and pydantic-settings |
| HTTP integrations | HTTPX with explicit timeouts and bounded retries |
| AI | Official `google-genai` Python SDK; verified Gemini free-tier function calling |
| Weather and city lookup | Open-Meteo Forecast and Geocoding |
| Place data and map coordinates | OpenStreetMap through a policy-compliant Overpass adapter |
| Optional research | Gemini Google Maps/Search grounding, independently gated |
| Navigation links | Google Maps URLs, without a Maps API key |
| Persistence | SQLite with SQLAlchemy; keep a later PostgreSQL migration possible |
| Tests | pytest, frontend component tests, and a small browser end-to-end suite |
| Portfolio | Git, GitHub-ready documentation and offline CI checks |

Avoid unnecessary orchestration frameworks, microservices, queues, authentication systems, or infrastructure. Implement the tool loop explicitly so a student can understand and demonstrate it.

## 4. Product behavior and user journey

A user can enter a structured request and/or a natural-language message such as:

> “Barselona'da dört gün geçireceğim. Tarihi yapılar, müzeler ve yerel yemeklerle ilgileniyorum. Bütçem orta. Yağışlı günlerde kapalı mekânları tercih ediyorum.”

Collect destination city and optional country, start and end dates, interests, budget preference, preferred pace, and output language. Budget is initially a qualitative preference, not a live price quote. Optional accessibility, dietary, and mobility preferences may be represented without claiming independently verified suitability.

The application must:

1. Validate and normalize the request. Resolve ambiguous city names using actual geocoding candidates; ask the user to choose when necessary.
2. Resolve destination coordinates and timezone.
3. Fetch weather for supported dates and mark unsupported dates individually.
4. Find real candidate places from OSM and, only when permitted and enabled, grounded Google research.
5. Deduplicate candidates, retain provenance, assess interest fit, and verify map coordinates from an allowed source.
6. Produce a realistic itinerary grouped by day and morning/afternoon/evening, accounting for proximity, weather, interests, pace, and known constraints.
7. Show explanations, weather context, source links, and uncertainties for recommendations.
8. Show suitable places on a Leaflet map and provide Google Maps view/directions links.
9. Save, reopen, edit, and delete trips in SQLite.
10. Allow a follow-up request such as “İkinci günün müzelerini değiştir”; reuse existing valid data and change only the requested parts unless consistency requires more changes.

Do not invent ratings, exact prices, opening hours, coordinates, travel times, ticket availability, restaurant dietary compliance, or current weather. Unknown information must remain unknown. LLM-derived classifications and estimates must be distinguished from provider facts.

## 5. Architecture and repository organization

Keep API keys, provider integrations, orchestration, validation, and persistence in FastAPI. React calls the backend and renders validated responses; it never calls Gemini directly or contains its secret key. Browser tile requests and external navigation links are expected exceptions to backend-mediated data access.

```text
ai-travel-planner/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/api.ts
│   │   ├── types/
│   │   ├── i18n/
│   │   └── App.tsx
│   ├── tests/
│   ├── .env.example
│   ├── package.json
│   └── vite.config.ts
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   ├── core/
│   │   ├── schemas/
│   │   ├── models/
│   │   ├── services/
│   │   ├── agents/
│   │   ├── tools/
│   │   ├── prompts/
│   │   ├── db/
│   │   └── main.py
│   ├── tests/
│   │   └── fixtures/
│   ├── .env.example
│   └── pyproject.toml
├── docs/
│   ├── architecture.md
│   ├── free-services.md
│   ├── development-progress.md
│   ├── testing.md
│   ├── demo.md
│   └── screenshots/
├── .github/workflows/ci.yml
├── .gitignore
├── README.md
└── README.tr.md
```

Adjust details when justified, but preserve clear separation between routes, business logic, external providers, database models, API schemas, and the agent. Use reproducible dependency files and a frontend lockfile.

## 6. Provider implementations and truthful fallbacks

### Open-Meteo

Implement city geocoding and daily weather adapters. Preserve the destination timezone, units, forecast retrieval timestamp, and the dates actually returned. Include daily minimum/maximum temperature, precipitation information, and weather codes where available.

Validate date order and a documented maximum trip length. Handle trips partially or completely outside the forecast horizon. Never substitute today's forecast for a future date, call historical observations a forecast, or present seasonal assumptions as measured predictions. Unsupported days should still receive a flexible itinerary with “Forecast unavailable for this date.”

The free hosted service is subject to non-commercial use and request limits. Verify eligibility and provide attribution. Sources: [Open-Meteo docs](https://open-meteo.com/en/docs), [Geocoding](https://open-meteo.com/en/docs/geocoding-api), [terms](https://open-meteo.com/en/terms).

### OpenStreetMap, Overpass, and Leaflet

Query a bounded area around the selected destination for museums, historic attractions, parks, tourism points, and restaurants. Use category allowlists and bounded radii; never interpolate arbitrary user-supplied Overpass programs. Handle node coordinates and way/relation centers explicitly, recognizing that a geometry center may not be an entrance.

Retain OSM type/id, name, tags used, coordinates, attribution, source URL, and retrieval timestamp. Deduplicate by stable identity and cautious proximity/name checks. Handle missing names and incomplete tags without fabricating facts. Apply low concurrency, caching where allowed, result limits, and backoff; do not overload public instances or switch endpoints to evade limits.

Use independently sourced OSM coordinates for Leaflet markers. A Google suggestion without a reliable OSM match may remain a research card with its source link; do not manufacture a pin. Keep provenance separate when records are matched. Matching a Google result to an OSM record does not automatically authorize storing or redistributing the Google content.

Show visible OpenStreetMap attribution. Respect tile caching and request rules, and avoid bulk downloads or offline prefetch. The interface must remain useful if tiles fail. Sources: [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API), [tile usage policy](https://operations.osmfoundation.org/policies/tiles/), [OSM attribution and copyright](https://www.openstreetmap.org/copyright).

### Optional Google Maps and Search grounding

Create separate provider adapters and independent capability flags. If a feature is not verified free, disabled, unsupported, or quota-exhausted, return a structured unavailable result and continue with OSM where possible. The rest of the product must work without Google research.

Keep grounded research separate from the custom function-calling request unless the exact model and API explicitly support their combination. The conservative design is a custom research tool whose backend implementation makes a separately gated grounding call. Bound these nested calls under the same request budget.

Preserve returned citation metadata and required attribution or display elements. Link claims to their actual sources; never invent citations or treat grounded prose as a guaranteed structured Places API response. Verify language support and, if needed, research in supported English and produce the final Turkish itinerary separately while retaining citations and place names.

Review provider restrictions for storage, caching, rendering alongside non-Google maps, and source presentation before implementing those features. If a restriction is incompatible with the planned screen, omit that content or feature and document the limitation. Do not scrape Google Maps or Google Search as a workaround.

### Google Maps navigation links

Provide “Google Maps'te Gör / View on Google Maps” and “Yol Tarifi Al / Get Directions” links using the documented URL interface. URL-encode destination text, include `api=1`, and use actual place IDs only when supplied by a legitimate source. Do not request current user location unless the user opts in. External links need appropriate safe browsing attributes.

Maps URLs do not require an API key; see the [official Maps URLs guide](https://developers.google.com/maps/documentation/urls/get-started). A working navigation link does not mean Google research or routing data was fetched by this application.

## 7. Genuine Gemini function calling

Implement an explicit, bounded model–tool–model loop using the official SDK and model-compatible function schemas. Suggested tools are:

```text
resolve_destination(city, country?)
get_weather(latitude, longitude, start_date, end_date, timezone)
search_tourist_places(latitude, longitude, categories, radius_m)
get_place_coordinates(place_name, destination_id)
research_google_places(destination, interests)    # only if capability enabled
research_google_web(query, destination)          # only if capability enabled
```

Schema details should use validated types and documented bounds. Do not expose arbitrary HTTP, shell execution, filesystem access, or SQL to the model. Disabled tools should be absent from the advertised tool list and also rejected by dispatch if requested unexpectedly.

Required execution flow:

1. Validate user input and create a planning context.
2. Send the model the user request, system instructions, and available function declarations.
3. Inspect actual function-call objects returned by the SDK; a model-written description of a call is not a tool call.
4. Check the tool name against the registry and validate arguments before execution.
5. Execute the backend function, normalizing successful, partial, and failed results into typed envelopes.
6. Return each function result with the correct model conversation structure and call identifiers where required. Preserve SDK-required metadata according to the current model documentation.
7. Continue until final output or a strict iteration/request/time limit is reached. Detect repeated identical calls and reuse allowed cached results.
8. Validate final output against the itinerary schema and cross-check all referenced place/source IDs against retrieved evidence. Reject fabricated references. Allow only a bounded repair attempt.
9. Return a valid plan or a clear actionable error; never store invalid model output as a successful trip.

Use structured output where supported by the chosen model and request mode. If combined tool use and structured generation are unsupported, use a separate final formatting request within the budget.

Treat external content and user-supplied place descriptions as data, not instructions. Research content must not override the system rules, expose secrets, expand tool permissions, or alter the free-service policy.

Record an inspectable **AI Activity** log with tool name, status, duration, cache hit, and a short redacted result summary. This is a factual execution log, not hidden chain-of-thought. Never fabricate completed activity steps or expose keys/raw sensitive payloads.

If no Gemini key or free quota is available, distinguish these modes clearly:

- Live AI: actual Gemini function calls and external provider results.
- Non-AI fallback: a deterministic plan from available OSM/weather data, explicitly labeled.
- Demo mode: bundled, synthetic fixtures, visibly labeled and usable without network or credentials.

Mocked tests or demo fixtures do not prove live Gemini function calling works. Record live verification separately and honestly.

## 8. Planning and recommendation logic

Keep essential constraints deterministic and testable; use the model for interpretation and explanations.

- Allocate dates inclusively in the destination timezone, without duplicate or missing days.
- Prefer nearby places on the same day. Use a simple documented distance heuristic rather than claiming route optimization.
- A Haversine distance is straight-line distance, not a road route or exact travel duration. Label any estimates and avoid promising accurate transit or opening-time feasibility without supporting data.
- Balance daily activity counts and rest/meal opportunities according to pace. Do not fill sparse results with imaginary attractions.
- Prefer indoor or sheltered alternatives when supported forecasts indicate rain, and consider temperature and precipitation amount as well as probability. Treat thresholds as configurable planning heuristics, not meteorological guarantees.
- Consider budget only where evidence supports it. Missing price data must not be interpreted as free admission.
- Avoid repeating the same place across days unless explicitly requested.
- Explain why each place was selected using known interests, location, weather, and available evidence.

Use these initial, configurable ranking weights from the roadmap: interest fit 35%, source support 20%, proximity 20%, weather suitability 15%, and budget fit 10%. Source support should remain meaningful with OSM when Google is disabled. Explain handling of missing factors, for example renormalizing known factors and reporting reduced evidence coverage. Do not turn an internal score into a fabricated public rating.

## 9. Data contracts and persistence

Define Pydantic request/response schemas and matching TypeScript types. Suggested entities:

- `TripRequest`: destination query or selected candidate, dates, interests, budget, pace, language, and optional natural-language instructions.
- `Destination`: stable local identity, city, country, coordinates, timezone, and source.
- `Place`: stable ID, name, category, optional address, optional verified coordinates, coordinate source, indoor/outdoor/unknown classification, classification basis, evidence links, optional sourced price/opening information, and recommendation explanation.
- `WeatherDay`: date, forecast availability, nullable measurements, units, timezone, source, and fetched timestamp.
- `ItineraryDay`: date, weather, ordered activities, optional alternatives, and warnings.
- `Trip`: ID, title, normalized request, days, referenced places/sources, generation mode, warnings, and created/updated timestamps.
- `ToolActivity`: tool name, status, duration, cached flag, and safe summary.
- `ProviderCapability`: provider feature, enabled status, availability, and non-sensitive reason.

Validate coordinate ranges, enum values, IDs, safe source URLs, date order, text lengths, and trip duration. Preserve unknown values as null/explicit unknown states instead of plausible defaults.

Use SQLite transactions for saving and updating. Store validated application-owned itinerary data and only provider content whose retention is permitted. If a source forbids retaining some data, do not place it in persisted JSON, logs, or fixtures. Keep generated explanations distinguishable from source content.

Support listing, reopening, modifying, and deleting trips. Keep IDs stable during edits where appropriate. Provide a documented schema initialization or migration process. Use an isolated temporary database in tests. The initial app is single-user/local; document this scope and do not imply its saved trips are safe to expose publicly without authentication.

## 10. FastAPI API

Implement the agreed routes with documented schemas:

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/health` | Local backend health; no external API call |
| GET | `/api/capabilities` | Safe provider and demo/live availability |
| GET | `/api/destinations` | Resolve city candidates |
| GET | `/api/weather` | Validated forecast request |
| GET | `/api/places` | Bounded place discovery |
| POST | `/api/trips/generate` | Generate and save a validated trip |
| GET | `/api/trips` | Paginated saved trip summaries |
| GET | `/api/trips/{id}` | Load a saved trip |
| PATCH | `/api/trips/{id}` | Validated manual updates |
| POST | `/api/trips/{id}/revise` | Natural-language revision using existing context |
| DELETE | `/api/trips/{id}` | Delete a saved trip |

If generation returns a saved trip, do not save a duplicate in the frontend. Specify retry/idempotency behavior for generation and revision. Protect against accidental duplicate submissions. A simple synchronous implementation is acceptable initially if timeouts are bounded; add background work or streaming only when justified.

Use consistent error envelopes such as `code`, `message`, `retryable`, and safe details. Distinguish invalid input, not found, missing configuration, quota exhaustion, provider failure, and invalid AI output. Keep tracebacks and secrets out of client responses. Configure CORS for explicit local development origins.

## 11. React experience and design

Build three main pages:

1. **Home**: destination, dates, interests, budget, pace, language, and optional free-text request; inline validation and useful examples.
2. **Travel Planner**: daily itinerary beside the interactive map on desktop, a readable stacked/tabbed layout on mobile, day selection, weather cards, source links, AI Activity, and a follow-up chat panel.
3. **My Trips**: saved trip cards, destination/date summaries, reopening, editing, and deletion with a clear confirmation.

Suggested components: `Navbar`, `TravelForm`, `TripCard`, `DayTimeline`, `PlaceCard`, `WeatherCard`, `TravelMap`, `ChatPanel`, and `ToolActivity`.

Use a clean travel-product visual style: clear typography, restrained color, consistent spacing, readable cards, and a strong itinerary/map relationship. Avoid a generic dashboard overloaded with unnecessary metrics. Use licensed assets or simple CSS illustrations; paid image services are unnecessary.

Synchronize cards and map markers: selecting a place highlights and focuses the matching marker; selecting a marker reveals its card. Filter or distinguish places by day. Do not draw lines that imply real roads or navigation routes unless actual permitted routing data exists; a schematic connection must be labeled.

Provide keyboard operation, visible focus, semantic labels, adequate contrast, touch-friendly controls, reduced-motion support, and non-map access to every place. All core product labels and validation/error messages must support Turkish and English. Format dates and units appropriately and preserve proper names.

Show real loading/error/empty/partial states. Display missing forecasts, unavailable sources, rate limits, missing coordinates, and demo mode honestly. Do not display fabricated progress percentages or simulated tool executions as live activity. Preserve user form input after errors.

## 12. Configuration and operational safeguards

Provide `.env.example` files with placeholders only. Suggested backend settings:

```dotenv
APP_ENV=development
DATABASE_URL=sqlite:///./data/travel_planner.db
GEMINI_API_KEY=
GEMINI_MODEL=
FREE_ONLY_MODE=true
ENABLE_GOOGLE_MAPS_GROUNDING=false
ENABLE_GOOGLE_SEARCH_GROUNDING=false
DEMO_MODE=false
CORS_ORIGINS=["http://localhost:5173"]
REQUEST_TIMEOUT_SECONDS=20
MAX_AGENT_STEPS=8
MAX_TRIP_DAYS=14
```

These limits are application defaults, not claims about provider quotas. Add separately documented conservative limits for provider requests, retries, query radius, and result count. `GEMINI_MODEL` stays empty until a free eligible model is selected. Use validated booleans and settings; do not treat a literal string `false` as truthy.

Frontend configuration should contain only public settings such as `VITE_API_BASE_URL`. Never use a `VITE_` variable for a secret. Ignore `.env`, virtual environments, local databases, generated caches, and sensitive logs in Git. Validate provider base URLs from trusted configuration, not from user/model arbitrary URLs.

Use bounded retries for transient failures and honor rate-limit information. Do not endlessly retry authentication errors or exhausted quota. Include nested grounding calls in request accounting. Avoid blocking network SDK calls inside the FastAPI event loop; use supported asynchronous clients or appropriate isolation.

## 13. Incremental implementation phases

**Default working scope: implement Phase 1 first and stop after its completion report.** The whole document defines the final destination; it is not a request to generate every feature in one unreviewed pass. When the user explicitly asks to continue through multiple phases, follow that scope and retain the phase checkpoints. Do not request routine approvals for ordinary local implementation choices.

For each phase: inspect current progress, briefly state the objective, implement a complete vertical slice, run relevant checks, fix issues, update documentation, and report what works plus any blocked external verification. Do not label a phase complete while its essential behavior is a placeholder. A clearly recorded external blocker must not prevent unrelated local progress.

### Phase 1 — Full-stack foundation

- Set up React/Vite/TypeScript/Tailwind and FastAPI with compatible dependencies.
- Create initial routing, shared layout, typed API client, settings, `.env.example`, and `.gitignore`.
- Implement `/api/health` and display its actual response and failure state in React.
- Establish basic validation/test tooling and local setup documentation for Windows PowerShell and macOS/Linux.
- Prepare the free-service verification checklist; do not require an API key to start the UI/backend.

Acceptance: both applications start using the README, the browser reaches the real backend, health failures are visible, and basic checks pass. Report exact commands and files changed, then stop by default.

### Phase 2 — Free data integrations

- Implement Open-Meteo geocoding/weather and OSM/Overpass place discovery as independently testable adapters.
- Add validated destination/weather/place routes, provenance, caching, bounded calls, and useful failures.
- Handle ambiguous destinations, missing coordinates, empty results, and forecast horizons.
- Add mock fixtures and demo infrastructure; verify live providers only when available and permitted.

Acceptance: destination, weather, and place JSON are available through FastAPI. Test İstanbul, Barcelona, Paris, nonexistent cities, unsupported dates, and provider outages without needing Gemini.

### Phase 3 — Gemini and optional Google research

- Configure the official Gemini SDK and a verified free model; implement a minimal real request and honest key/quota errors.
- Verify Google Maps and Search grounding separately and record the result in `docs/free-services.md`.
- Implement optional research adapters, citation handling, data-use rules, and ranking inputs.
- Keep disabled grounding fully supported through the OSM path.

Acceptance: eligible live Gemini access is demonstrated or precisely marked unverified; optional Google research either works with required attribution or is explicitly disabled. No billing account is activated and no paid fallback is used.

### Phase 4 — AI agent and itinerary generation

- Implement the genuine bounded function-calling loop and tool registry.
- Add validated structured itinerary output, deterministic consistency checks, ranking, date allocation, and weather-aware alternatives.
- Add factual AI Activity records, `/api/trips/generate`, SQLite persistence, and natural-language revision.
- Keep fallback/demo behavior separate from live AI behavior.

Acceptance: a request produces a valid daily plan using actual tool results; a revision reuses appropriate existing data; invalid calls/output and quota failures are handled safely. Offline tests verify the dispatch loop and constraints; live verification is separately documented.

### Phase 5 — Complete React product

- Finish Home, Travel Planner, and My Trips.
- Add itinerary/map interaction, daily weather, recommendation explanations, citations, navigation links, saved-trip CRUD, and the revision chat panel.
- Complete Turkish/English support, accessibility, mobile layouts, and loading/error/empty/partial states.

Acceptance: a user can create, view, save, reopen, revise, and delete a trip through the UI. All visible controls work. The demo path works without API keys, and map/source failures do not break the itinerary.

### Phase 6 — Tests, GitHub documentation, and demonstration

- Complete targeted integration and end-to-end tests and fix real failures.
- Add reproducible offline CI, architecture diagram, actual screenshots, service limitations, setup guidance, and a short teacher demonstration script.
- Verify clean-clone setup and review tracked files for credentials/local data.
- Prepare a GitHub-ready repository locally; publish, push, or deploy only if the user requests it.

Acceptance: documented local setup is reproducible, checks pass, demo behavior is honest, and README clearly explains the function-calling workflow and free-service restrictions.

## 14. Test strategy and required scenarios

Default automated tests must be deterministic, use mocked provider responses, and require no network, credentials, or billable services. Put live smoke tests behind an explicit opt-in, with very small request budgets. Use synthetic fixtures or data allowed for storage; never commit restricted provider payloads or personal information.

Backend coverage must include input validation, destination ambiguity, timezone/date handling, partial forecast availability, OSM parsing/deduplication, ranking with missing evidence, tool dispatch/arguments, loop termination, nested-call budgets, structured output validation, disabled-provider behavior, errors, and transactional CRUD.

Frontend tests must cover form validation, API errors, unavailable weather, map/list selection behavior, source links, language changes, saved trips, and demo labels. Use a small Playwright or equivalent suite for the main user journey with fixture-backed services; browser tests should not depend on live tile servers or third-party quotas.

| Scenario | Expected result |
|---|---|
| Barcelona, four-day cultural trip | Four coherent days, evidence-backed places, no duplicates |
| Amsterdam, rainy forecast fixture | Indoor alternatives with a clear explanation |
| Paris, low budget and unknown admission prices | Prefer supported affordable options; no invented free admission |
| İstanbul / Turkish input | Correct Unicode handling, city choice, and Turkish output |
| Ambiguous or nonexistent city | Selection or validation message; no guessed destination |
| Reversed dates or excessive duration | Validation error before external calls |
| Partly/outside forecast horizon | Only supported dates get forecasts; no fabricated weather |
| Google grounding disabled | No Google grounding network request; OSM flow remains usable |
| Gemini quota exhausted or key absent | Clear state, no paid fallback; labeled demo/non-AI option |
| Missing/malformed model tool arguments | Rejected safely; bounded correction or error |
| Repeated tool calls or invalid final JSON | Bounded termination; no invalid successful save |
| Missing coordinate / wrong-city name match | No fabricated or mismatched pin |
| Provider timeout, 429, or malformed response | Bounded retry and truthful partial/error result |
| Edit only day two | Other days preserved unless a documented constraint requires change |
| Duplicate generate submission | No accidental duplicate saved trip |
| Saved-trip lifecycle | Generate, reopen, revise, and delete work consistently |

Run backend tests, frontend type checks, lint checks, production build, and relevant UI tests. Report what actually ran and its result; never claim a test passed merely because it was written. Avoid expanding tests into repetitive checks that only mirror implementation details.

## 15. GitHub documentation and final definition of done

Write a clear English `README.md` and Turkish `README.tr.md`, including:

- Project purpose, educational objectives, implemented features, and honest limitations.
- Stack and a small architecture diagram showing React → FastAPI → tools/providers → validated itinerary → SQLite.
- A function-calling sequence explaining model requests, backend execution, function responses, and final validation.
- Supported runtime versions, dependency installation, environment setup, database initialization, and frontend/backend start commands.
- Gemini free-tier setup without requesting that the user disclose a secret; independent grounding eligibility and disabled defaults.
- Demo mode, non-AI fallback, and live mode differences.
- API documentation location and useful example requests.
- Test/build commands and offline CI behavior.
- Weather horizon, estimated distances, incomplete place data, provider quotas, and local single-user scope.
- Attribution, data licensing, privacy considerations, and provider retention restrictions.
- Actual application screenshots, a reproducible demonstration scenario, and a short future roadmap.

Use `docs/development-progress.md` to record phase status, implemented behavior, checks run, and unresolved limitations. Optional later features such as PDF export, accounts, PostgreSQL, advanced routing, and public deployment belong in the future roadmap; they must not delay the agreed MVP or introduce paid dependencies.

The final project is complete only when the full-stack journey works, real function calling is implemented, results are validated and sourced, disabled Google grounding is a normal supported state, SQLite persistence works, Turkish/English UI is usable, appropriate tests pass, and a new reader can run the documented local/demo setup.

## 16. Begin now

Inspect the workspace and applicable instructions. Briefly summarize the implementation approach in Turkish. Then implement **Phase 1** completely, verify it, update the README and progress file, and report:

1. What now works.
2. How to run it locally.
3. Which checks ran and their results.
4. Any concrete blocker or unverified external assumption.
5. What Phase 2 will add.

Do not request an API key for Phase 1, and do not claim later phases are complete. If the user has explicitly requested a different phase or several phases, use that requested scope instead.

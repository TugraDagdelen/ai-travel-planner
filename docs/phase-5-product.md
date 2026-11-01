# Phase 5 — complete local product flow

## User flow

The React application now supports the complete local lifecycle: validate preferences, select a resolved city, generate once, persist to SQLite, reopen from My Trips, rename, revise from stored evidence and delete. A UUID generated when the planner panel mounts is sent as `idempotency_key`; repeated submissions with the same UUID return the original record.

`ItineraryView` is shared by the planner result and saved-trip detail page. It renders date-aligned weather, recommendation explanations, rain alternatives, tool activity and source metadata. `RevisionPanel` stores and displays each instruction, localized result summary, resulting version and timestamp.

## Map and links

React Leaflet 5 and Leaflet 1.9 render OpenStreetMap tiles and one marker per unique itinerary place. Selecting a daily stop focuses the corresponding marker. The map is lazy-loaded so the rest of the itinerary appears first. Tile errors show a local message and never remove the daily list.

Verified live coordinates may open a keyless Google Maps directions URL. Synthetic demo coordinates intentionally have no navigation link. OSM source URLs come from backend evidence and open in a new tab with safe `rel` attributes.

## States and accessibility

Saved-trip screens cover loading, retryable error, empty, not-found and populated states in Turkish and English. Semantic headings, labelled fields, pressed stop controls, an accessible map region, focus-on-route navigation and reduced-motion support remain enabled. The mobile check at 390 × 844 has no horizontal overflow.

## Persistence rules

- The local database is the only trip store.
- Generation is serialized and idempotency is checked before provider/model work.
- Rename and revision increment the version.
- Deterministic/demo targeted revision recognizes `day N` and `N. gün`; only that day's first activity period changes.
- Unsupported offline natural-language instructions fail explicitly instead of inventing a result.
- Delete returns 204 and the UI navigates back to My Trips after confirmation.

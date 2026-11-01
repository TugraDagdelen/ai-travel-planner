# Phase 5 demonstration

## Offline without API keys

1. Start both services using the README; confirm Connection ready / Bağlantı hazır.
2. Enter `Paris, France`, a four-day range beginning today and culture/nature interests. Submit preferences.
3. Choose **Offline demo / Çevrimdışı demo** in discovery. The banner labels synthetic weather and places.
4. Search Paris. France and Texas appear; neither is chosen automatically. Select France.
5. Inspect weather and places. Synthetic provenance is visible and no external source links or provider requests are used.
6. Switch TR/EN. Return to editing; preferences remain in memory.
7. Try dates beyond the next 16 days. Weather is unavailable; place discovery remains usable.
8. In **Planını oluştur / Build your itinerary**, choose the only available demo generation mode and generate. Inspect exact dates, synthetic place labels, activity log and local-save badge.
9. Enter a revision such as “İlk iki durağın sırasını değiştir”. Demo revision reorders saved evidence, increments the version and does not call a provider.
10. Open the saved-plan link, revise day 2, and verify day 1 is unchanged and revision history records version 2.
11. Open **My Trips / Seyahatlerim**, reopen the card, rename it and exercise the deletion confirmation. Refreshing resets only the draft; saved trips remain in SQLite.
12. Select an itinerary stop to focus its map marker. Demo coordinates are labelled synthetic and intentionally have no navigation URL.

Demo cities: İstanbul, Barcelona, Paris (France), Paris (Texas). City positions are public city coordinates; weather and nearby records are synthetic examples.

## Live sources

1. Choose **Live data / Canlı veriler**, search İstanbul or Barcelona and explicitly choose the correct region/country.
2. Use dates in the next few days. Weather and places load independently; source, retrieval time and cache labels identify the results.
3. Inspect source links and coordinate/classification caveats. Category inference is not a verified building attribute.
4. Try Paris with country code FR, then a nonexistent city to see the empty state.
5. If a provider fails or limits requests, keep the error visible and honor the wait before retrying. Demo requires an explicit mode change.

Open-Meteo and Wikimedia/Wikidata live checks passed. Paris returned 18 typed, coordinate-backed places in about four seconds. Overpass remains a bounded fallback if Wikimedia is temporarily unavailable.

Choose the deterministic planner after live discovery to generate without Gemini. It uses the same tool results and documented scoring rules; it does not silently switch to demo when a provider fails. Personal notes stay with the local backend in deterministic mode.

## Gemini connection

1. Without a key, open **Yapay zekâ bağlantısı / AI connection** and choose the status button. The real backend reports that the key is missing; no Google request occurs.
2. If you have followed [gemini-setup.md](gemini-setup.md), restart the backend, refresh status and explicitly choose the live connection test.
3. A successful card shows the exact configured model, checked time and the short model greeting.
4. Select **Gemini tool calling** under itinerary generation. The model must request both allowlisted discovery tools; the server validates the final plan before saving it.
5. Revise the plan in natural language. The revision reuses stored evidence and rejects new tool calls.
6. Quota, invalid-key, model-access, invalid tool/output and timeout messages remain errors; there is no paid, model or demo retry.

This development session verified a complete two-day Paris itinerary with live Open-Meteo weather, Wikimedia/Wikidata places and Gemini tool calling. Google Maps/Search research remains disabled because it is outside the reviewed API Free tier.

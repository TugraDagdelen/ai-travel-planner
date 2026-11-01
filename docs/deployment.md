# Free portfolio deployment

Reviewed **2026-11-01**. `render.yaml` defines one Render Free web service. The build installs the locked Python and Node dependencies, builds React with `VITE_API_BASE_URL=/api`, and lets FastAPI serve the resulting SPA and API from one HTTPS origin.

## Before deployment

1. Run `powershell -NoProfile -File .\scripts\verify.ps1` locally.
2. Push the repository to GitHub without `.env`, SQLite files, or API keys.
3. In Render, create a Blueprint from the repository and confirm that the selected plan is **Free** before creating the service.
4. Keep `GEMINI_FREE_TIER_CONFIRMED=false` and omit `GEMINI_API_KEY` for the first deployment. Demo and deterministic modes remain usable.

The Blueprint uses `/api/health` for health checks and waits for GitHub checks before automatic deployment. The public service starts with:

```text
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Gemini after the demo is live

Only add `GEMINI_API_KEY` in Render's secret environment settings after checking the key's project has no billing and is eligible for Gemini's Free tier. Then set `GEMINI_FREE_TIER_CONFIRMED=true` and redeploy. Never commit the key or place it in a `VITE_` variable. Google Search and Maps grounding remain disabled because the reviewed `gemini-3.5-flash-lite` Free tier does not include them.

## Free-host limitations

Render's Free web service sleeps after 15 minutes without inbound traffic and can take about a minute to wake. Its filesystem is ephemeral, so SQLite trips can disappear after a restart, spin-down, or redeploy. The deployment is therefore a portfolio demonstration, not durable storage. Render Free Postgres currently expires after 30 days, so it is not configured as a false promise of permanent storage.

The service also depends on shared Open-Meteo, Wikimedia/Wikidata, Overpass fallback, and OpenStreetMap tile infrastructure. Requests remain bounded, cached and attributed. Overpass remains a secondary real-data path and never rotates after a rate-limit response.

Official references: [Render Free limits](https://render.com/docs/free), [Render Blueprint schema](https://render.com/docs/blueprint-spec), [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing), [Overpass public instances](https://wiki.openstreetmap.org/wiki/Overpass_API#Public_Overpass_API_instances).

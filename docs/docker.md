# Docker presentation guide

Docker packages the React production build and FastAPI API in one image. The application is available at `http://localhost:8000`; API routes remain under `/api`. A named Docker volume keeps SQLite trips between ordinary container restarts on the same computer.

## Fast demo without Gemini

Install Docker Desktop, clone the repository, and run from the repository root:

```bash
git clone https://github.com/TugraDagdelen/ai-travel-planner.git
cd ai-travel-planner
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000) and choose demo generation. Stop the application with `Ctrl+C`; remove the stopped container with `docker compose down`.

## Run with Gemini Free Tier

Create `backend/.env` from `backend/.env.example`, add the key locally, and confirm the associated AI Studio project displays **Free Tier**. Never commit this file.

```env
GEMINI_API_KEY=your_new_key
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_FREE_TIER_CONFIRMED=true
```

Pass that file to Compose only for local variable substitution:

```bash
docker compose --env-file backend/.env up --build
```

Compose sends only the declared variables into the container. The container allows up to 60 seconds for a Gemini response because Docker networking can be slower on its first request; request-count and free-tier safeguards remain active. Google Maps and Search grounding remain disabled. Check the connection in the application before the presentation.

## Presentation-day checklist

1. Start Docker Desktop and wait until its engine is ready.
2. Run `git pull` in the existing clone, or clone the repository on the presentation computer.
3. Run `docker compose up --build` for the keyless demo, or use the `--env-file` command for Gemini.
4. Wait for the line containing `Uvicorn running on http://0.0.0.0:8000`.
5. Open `http://localhost:8000/api/health`, then `http://localhost:8000`.
6. Keep one saved demo itinerary ready in case a public data provider is temporarily unavailable.

The first build downloads Node, Python and project dependencies and therefore needs internet access. Build the image before the presentation when possible. Later starts reuse the image and are much faster.

## Data and cleanup

`travel-data` is a local named volume. `docker compose down` keeps it. To intentionally remove saved trips as well, run:

```bash
docker compose down --volumes
```

Do not use the volume-removal command when saved presentation trips must be preserved.

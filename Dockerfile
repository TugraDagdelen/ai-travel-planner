FROM node:24.12.0-bookworm-slim AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
ENV VITE_API_BASE_URL=/api
RUN npm run build


FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    APP_ENV=production \
    CORS_ORIGINS='[]' \
    FREE_ONLY_MODE=true \
    ENABLE_GOOGLE_MAPS_GROUNDING=false \
    ENABLE_GOOGLE_SEARCH_GROUNDING=false \
    GEMINI_MODEL=gemini-3.5-flash-lite \
    GEMINI_FREE_TIER_CONFIRMED=false \
    GEMINI_TIMEOUT_SECONDS=60 \
    DATABASE_URL=sqlite:////app/data/travel_planner.db

WORKDIR /app

COPY backend/requirements-lock.txt ./backend/requirements-lock.txt
RUN python -m pip install --no-cache-dir -r backend/requirements-lock.txt

COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist/

RUN mkdir -p /app/data

EXPOSE 8000

WORKDIR /app/backend
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

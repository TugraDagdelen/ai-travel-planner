from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    free_only_mode: bool = True
    enable_google_maps_grounding: bool = False
    enable_google_search_grounding: bool = False
    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_free_tier_confirmed: bool = False
    gemini_timeout_seconds: float = Field(default=25, ge=1, le=60)
    gemini_daily_limit: int = Field(default=10, ge=1, le=50)
    gemini_minute_limit: int = Field(default=6, ge=1, le=10)
    database_url: str = f"sqlite:///{(BACKEND_ROOT / 'data' / 'travel_planner.db').as_posix()}"
    agent_max_steps: int = Field(default=6, ge=2, le=8)
    agent_max_tool_calls: int = Field(default=6, ge=2, le=10)
    agent_timeout_seconds: float = Field(default=75, ge=10, le=120)
    max_trip_days: int = Field(default=14, ge=1, le=14)
    provider_timeout_seconds: float = Field(default=25, ge=1, le=45)
    provider_hourly_limit: int = Field(default=120, ge=1, le=500)
    provider_daily_limit: int = Field(default=600, ge=1, le=2000)
    meteo_min_interval_seconds: float = Field(default=1, ge=0, le=10)
    overpass_min_interval_seconds: float = Field(default=3, ge=0, le=30)

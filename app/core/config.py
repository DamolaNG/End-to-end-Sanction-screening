"""Application configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: str = Field(
        default="postgresql+psycopg://sanctionsight:sanctionsight@localhost:5432/sanctionsight",
        alias="DATABASE_URL",
    )
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="sanctionsight", alias="POSTGRES_DB")
    postgres_user: str = Field(default="sanctionsight", alias="POSTGRES_USER")
    postgres_password: str = Field(default="sanctionsight", alias="POSTGRES_PASSWORD")
    sample_data_mode: bool = Field(default=True, alias="SAMPLE_DATA_MODE")
    allow_live_fetch: bool = Field(default=False, alias="ALLOW_LIVE_FETCH")
    blackrock_source_file: Path = Field(
        default=Path("/Users/damolang/Downloads/BlackRock-UnitedKingdom.xml"),
        alias="BLACKROCK_SOURCE_FILE",
    )
    raw_data_dir: Path = Field(default=Path("./data/raw"), alias="RAW_DATA_DIR")
    cache_data_dir: Path = Field(default=Path("./data/cache"), alias="CACHE_DATA_DIR")
    sample_data_dir: Path = Field(default=Path("./data/sample"), alias="SAMPLE_DATA_DIR")
    dbt_profiles_dir: Path = Field(default=Path("./dbt"), alias="DBT_PROFILES_DIR")
    dbt_project_dir: Path = Field(default=Path("./dbt"), alias="DBT_PROJECT_DIR")
    match_high_threshold: int = Field(default=92, alias="MATCH_HIGH_THRESHOLD")
    match_medium_threshold: int = Field(default=84, alias="MATCH_MEDIUM_THRESHOLD")
    match_low_threshold: int = Field(default=72, alias="MATCH_LOW_THRESHOLD")
    stale_source_hours: int = Field(default=72, alias="STALE_SOURCE_HOURS")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    streamlit_port: int = Field(default=8501, alias="STREAMLIT_PORT")

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def resolve_path(self, value: Path) -> Path:
        return value if value.is_absolute() else (self.project_root / value).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object."""

    settings = Settings()
    settings.raw_data_dir = settings.resolve_path(settings.raw_data_dir)
    settings.cache_data_dir = settings.resolve_path(settings.cache_data_dir)
    settings.sample_data_dir = settings.resolve_path(settings.sample_data_dir)
    settings.blackrock_source_file = settings.resolve_path(settings.blackrock_source_file)
    settings.dbt_profiles_dir = settings.resolve_path(settings.dbt_profiles_dir)
    settings.dbt_project_dir = settings.resolve_path(settings.dbt_project_dir)
    return settings

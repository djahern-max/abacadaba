from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    cors_origins: str
    spaces_key: str
    spaces_secret: str
    spaces_region: str
    spaces_bucket: str
    spaces_endpoint: str
    site_url: str = "http://localhost:5173"
    session_cookie_secure: bool = False
    session_cookie_domain: str | None = None
    environment: str = "development"
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @field_validator("database_url")
    @classmethod
    def use_psycopg3_driver(cls, value: str) -> str:
        # Managed Postgres hands out a URL starting with "postgresql://", which
        # SQLAlchemy resolves to psycopg2. We only install psycopg 3, so name the
        # driver explicitly. This lives in config rather than db.py because
        # alembic/env.py reads settings.database_url directly.
        if value.startswith("postgresql+"):
            return value
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return f"postgresql+psycopg://{value[len(prefix):]}"
        return value


settings = Settings()

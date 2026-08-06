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

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

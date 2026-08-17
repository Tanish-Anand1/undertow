from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://undertow:undertow@localhost:5433/undertow"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "dev-secret-change-me"
    public_base_url: str = "https://www.trysudo.in"
    require_email_verify: bool = False
    digest_skip_empty: bool = True
    max_keywords_per_user: int = 200
    scan_cooldown_minutes: int = 5
    auth_login_max_attempts: int = 8
    auth_login_window_seconds: int = 300
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "https://undertow-api.vercel.app/auth/google/callback"
    anthropic_api_key: str = ""
    nvidia_api_key: str = ""
    nvidia_model: str = "meta/llama-3.1-70b-instruct"
    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct"
    fireworks_api_key: str = ""
    fireworks_model: str = "accounts/fireworks/models/llama-v3p3-70b-instruct"
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "undertow-research/0.1"
    reddit_redirect_uri: str = "http://localhost:8080"
    x_bearer_token: str = ""
    x_consumer_key: str = ""
    x_consumer_secret: str = ""
    x_access_token: str = ""
    x_access_token_secret: str = ""
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "digest@undertow.app"
    ingest_interval_minutes: int = 20
    digest_hour_utc: int = 8
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "https://www.trysudo.in,https://trysudo.in,"
        "https://undertow-zeta.vercel.app"
    )
    product_description: str = (
        "Sudo listens for customer pain across Hacker News, GitHub, and X."
    )
    access_token_expire_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"
    admin_password: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        raw = (self.cors_origins or "").strip()
        if not raw:
            raw = (
                "http://localhost:5173,http://127.0.0.1:5173,"
                "https://www.trysudo.in,https://trysudo.in,"
                "https://undertow-zeta.vercel.app"
            )
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def sqlalchemy_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        if url.startswith("postgresql://") and "+psycopg2" not in url:
            url = "postgresql+psycopg2://" + url[len("postgresql://") :]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()

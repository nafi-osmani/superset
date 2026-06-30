"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    devin_api_key: str = ""
    devin_org_id: str = ""
    github_webhook_secret: str = "dev-local-secret"
    github_token: str = ""
    github_repo: str = "your-user/superset"
    max_acu_limit: int | None = 10
    poll_interval_sec: int = 30
    trigger_label: str = "devin-autofix"
    dry_run: bool = False
    database_path: str = "/app/data/remediator.db"


settings = Settings()

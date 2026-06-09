from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    secret_key: str
    frontend_url: str
    app_env: str = "local"
    smtp_host: str = "mailhog"
    smtp_port: int = 1025
    email_from: str = "noreply@chorequest.local"
    resend_api_key: str | None = None

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


settings = Settings()

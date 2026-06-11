from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
import socket


def detect_lan_ip() -> str:
    """Best-effort LAN address for email links when FRONTEND_URL=auto."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(1)
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    secret_key: str
    frontend_url: str
    app_env: str = "local"

    smtp_host: str = "smtp.ionos.co.uk"
    smtp_port: int = 587
    smtp_use_tls: bool = True
    smtp_username: str
    smtp_password: SecretStr
    email_from: str
    email_from_name: str = "Chore Quest"
    email_reply_to: str | None = None

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def public_frontend_url(self) -> str:
        """URL for password-reset and notification emails."""
        raw = self.frontend_url.strip()
        if raw.lower() == "auto":
            return f"http://{detect_lan_ip()}:5173"
        return raw.split(",")[0].strip().rstrip("/")

    @property
    def cors_origins(self) -> list[str]:
        """FRONTEND_URL may be comma-separated; localhost is always allowed in local dev."""
        origins = [
            origin.strip()
            for origin in self.frontend_url.split(",")
            if origin.strip() and origin.strip().lower() != "auto"
        ]
        if not self.is_production and "http://localhost:5173" not in origins:
            origins.append("http://localhost:5173")
        return origins

    @property
    def reply_to(self) -> str:
        return self.email_reply_to or self.email_from


settings = Settings()

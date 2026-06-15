from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def _normalize_database_url(url: str | None) -> str | None:
    """Normaliza URL do Postgres para SQLAlchemy + psycopg.

    Aceita:
    - postgresql://...
    - postgres://...
    - postgresql+psycopg://...

    Para Supabase/Streamlit Cloud, prefira:
    postgresql+psycopg://...?...sslmode=require
    """
    if not url:
        return None

    url = str(url).strip().strip('"').strip("'")
    if not url:
        return None

    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]

    return url


@dataclass(frozen=True)
class Settings:
    # Online / Supabase / Streamlit Cloud
    database_url_env: str | None = _normalize_database_url(os.getenv("DATABASE_URL"))

    # Local / .env
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "radar_pescados_ia")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "postgres")
    app_env: str = os.getenv("APP_ENV", "local")
    data_inicio_padrao: str = os.getenv("DATA_INICIO_PADRAO", "2000-01-01")

    @property
    def database_url(self) -> str:
        if self.database_url_env:
            return self.database_url_env

        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()

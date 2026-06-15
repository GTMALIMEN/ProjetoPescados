from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config.settings import settings


def get_engine() -> Engine:
    """Cria engine SQLAlchemy.

    Compatível com:
    - PostgreSQL local via DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD
    - Supabase/Streamlit Cloud via DATABASE_URL

    Para Supabase, o projeto desativa prepared statements para reduzir conflito com pooler.
    """
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={"prepare_threshold": None},
    )


def test_connection() -> bool:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))
    return True


def execute_sql_file(path: str) -> None:
    engine = get_engine()
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()

    with engine.begin() as conn:
        conn.execute(text(sql))

from pathlib import Path

p = Path("src/database/connection.py")

novo = r'''from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool

from src.config.settings import settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Cria uma única engine SQLAlchemy para o app.

    Ajuste para Streamlit Cloud + Supabase:
    - evita criar engine nova a cada chamada;
    - usa NullPool para não segurar conexões abertas;
    - desativa prepared statements para reduzir conflito com pooler.
    """
    return create_engine(
        settings.database_url,
        poolclass=NullPool,
        pool_pre_ping=True,
        pool_recycle=300,
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
'''

p.write_text(novo, encoding="utf-8")
print("✅ connection.py corrigido para Streamlit Cloud + Supabase.")

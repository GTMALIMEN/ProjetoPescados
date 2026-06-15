import pytest
from sqlalchemy import text

from src.database.connection import get_engine


def test_database_connection():
    engine = get_engine()

    with engine.begin() as conn:
        result = conn.execute(text("SELECT 1")).scalar()

    assert result == 1


@pytest.mark.db
def test_required_schemas_exist():
    engine = get_engine()

    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name IN ('raw', 'staging', 'dw', 'app')
        """)).fetchall()

    schemas = {row[0] for row in rows}

    assert {"raw", "staging", "dw", "app"}.issubset(schemas)

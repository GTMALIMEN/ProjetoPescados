from sqlalchemy import text

from src.database.connection import get_engine


def test_pipeline_tables_exist():
    engine = get_engine()

    with engine.begin() as conn:
        pipeline_execucao = conn.execute(
            text("SELECT to_regclass('app.pipeline_execucao') IS NOT NULL")
        ).scalar()
        pipeline_etapa = conn.execute(
            text("SELECT to_regclass('app.pipeline_etapa_execucao') IS NOT NULL")
        ).scalar()

    assert pipeline_execucao
    assert pipeline_etapa


def test_pipeline_view_is_queryable():
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            SELECT *
            FROM app.vw_pipeline_ultimas_execucoes
            LIMIT 1
        """)).fetchall()

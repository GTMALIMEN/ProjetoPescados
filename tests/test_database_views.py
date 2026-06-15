from sqlalchemy import text

from src.database.connection import get_engine


REQUIRED_VIEWS = [
    "app.mv_score_regional_atual",
    "app.mv_recomendacao_atual",
    "app.mv_indice_setorial_atual",
    "app.vw_alertas_ativos_atual",
    "app.vw_relatorios_executivos_recentes",
    "app.vw_pipeline_ultimas_execucoes",
]


def test_required_views_exist():
    engine = get_engine()

    with engine.begin() as conn:
        for view in REQUIRED_VIEWS:
            exists = conn.execute(
                text("SELECT to_regclass(:view) IS NOT NULL"),
                {"view": view},
            ).scalar()

            assert exists, f"View/materialized view ausente: {view}"

from sqlalchemy import text

from src.database.connection import get_engine


REQUIRED_OBJECTS = [
    "dw.fato_serie_historica",
    "dw.dim_geografia",
    "dw.fato_vendas",
    "dw.fato_indicador_setorial",
    "app.fato_score_regional",
    "app.fato_recomendacao",
    "app.fato_alerta_ativo",
    "app.fato_relatorio_executivo",
    "app.pipeline_execucao",
]


def test_required_database_objects_exist():
    engine = get_engine()

    with engine.begin() as conn:
        for obj in REQUIRED_OBJECTS:
            exists = conn.execute(
                text("SELECT to_regclass(:obj) IS NOT NULL"),
                {"obj": obj},
            ).scalar()

            assert exists, f"Objeto ausente no banco: {obj}"

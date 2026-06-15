from sqlalchemy import text

from src.database.connection import get_engine


def test_active_score_weights_do_not_exceed_one_by_score_version():
    engine = get_engine()

    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT
                nome_score,
                versao,
                ROUND(SUM(peso)::numeric, 6) AS soma_pesos
            FROM app.config_pesos_score
            WHERE ativo = TRUE
            GROUP BY nome_score, versao
        """)).fetchall()

    for row in rows:
        soma = float(row.soma_pesos)
        assert soma <= 1.000001, (
            f"Pesos acima de 1 para {row.nome_score} / {row.versao}: {soma}"
        )


def test_active_score_weights_are_positive():
    engine = get_engine()

    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT nome_score, variavel, peso
            FROM app.config_pesos_score
            WHERE ativo = TRUE
        """)).fetchall()

    for row in rows:
        assert float(row.peso) >= 0, f"Peso negativo: {row.nome_score} / {row.variavel}"

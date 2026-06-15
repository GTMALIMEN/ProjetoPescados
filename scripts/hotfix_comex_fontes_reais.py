from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine
from src.utils.logs import get_logger

logger = get_logger(__name__)

SQL = """
CREATE OR REPLACE VIEW app.vw_indicador_setorial_mensal AS
SELECT
    DATE_TRUNC('month', data)::DATE AS mes,
    fonte,
    uf,
    categoria,
    subcategoria,
    produto,
    indicador,
    unidade,
    AVG(valor) AS valor_medio,
    MIN(valor) AS valor_minimo,
    MAX(valor) AS valor_maximo,
    COUNT(*) AS qtd_observacoes
FROM dw.fato_indicador_setorial
GROUP BY
    DATE_TRUNC('month', data)::DATE,
    fonte,
    uf,
    categoria,
    subcategoria,
    produto,
    indicador,
    unidade;
"""

def main():
    engine = get_engine()
    with engine.begin() as conn:
        logger.info("Aplicando hotfix Comex/Fontes Reais...")
        conn.execute(text(SQL))

        checks = [
            "dw.fato_indicador_setorial",
            "app.vw_indicador_setorial_mensal",
            "app.config_ncm_pescado",
            "raw.comexstat_payload",
            "app.etl_fonte_real_resumo",
        ]

        for name in checks:
            exists = conn.execute(text("SELECT to_regclass(:name) IS NOT NULL"), {"name": name}).scalar()
            print(f"{name}: {exists}")

    logger.info("Hotfix aplicado com sucesso.")

if __name__ == "__main__":
    main()

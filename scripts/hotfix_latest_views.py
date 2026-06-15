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
-- ============================================================
-- Hotfix 7.2
-- Corrige views atuais para usar último cálculo, não maior data_referencia.
-- ============================================================

DROP MATERIALIZED VIEW IF EXISTS app.mv_recomendacao_atual;
DROP MATERIALIZED VIEW IF EXISTS app.mv_score_regional_atual;

CREATE MATERIALIZED VIEW app.mv_score_regional_atual AS
WITH ranked AS (
    SELECT
        s.*,
        ROW_NUMBER() OVER (
            PARTITION BY
                s.uf,
                s.regiao_comercial,
                s.municipio,
                s.produto,
                s.proteina
            ORDER BY
                s.data_calculo DESC,
                s.data_referencia DESC,
                s.id DESC
        ) AS rn
    FROM app.fato_score_regional s
)
SELECT
    id,
    data_referencia,
    pais,
    uf,
    regiao_ibge,
    regiao_comercial,
    municipio,
    produto,
    proteina,
    score_oportunidade,
    score_risco,
    score_pressao_custo,
    score_competitividade,
    score_sensibilidade_dolar,
    score_final,
    cenario_1_10,
    confianca,
    metodo,
    principais_fatores,
    data_calculo
FROM ranked
WHERE rn = 1;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_score_regional_atual
ON app.mv_score_regional_atual (
    uf,
    regiao_comercial,
    municipio,
    produto,
    proteina
);

CREATE MATERIALIZED VIEW app.mv_recomendacao_atual AS
WITH ranked AS (
    SELECT
        r.*,
        ROW_NUMBER() OVER (
            PARTITION BY
                r.uf,
                r.regiao_comercial,
                r.municipio,
                r.produto,
                r.proteina,
                r.tipo_recomendacao
            ORDER BY
                r.data_criacao DESC,
                r.data_referencia DESC,
                r.id DESC
        ) AS rn
    FROM app.fato_recomendacao r
)
SELECT
    id,
    id_score,
    data_referencia,
    pais,
    uf,
    regiao_comercial,
    municipio,
    produto,
    proteina,
    cenario_1_10,
    tipo_recomendacao,
    acao_sugerida,
    justificativa,
    confianca,
    impacto_estimado,
    roi_estimado,
    score_vendedor,
    score_promotor,
    score_campanha,
    status,
    principais_fatores,
    data_criacao
FROM ranked
WHERE rn = 1;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_recomendacao_atual
ON app.mv_recomendacao_atual (
    uf,
    regiao_comercial,
    municipio,
    produto,
    proteina,
    tipo_recomendacao
);
"""

def main():
    engine = get_engine()
    with engine.begin() as conn:
        logger.info("Aplicando hotfix das materialized views atuais...")
        conn.execute(text(SQL))
    logger.info("Hotfix aplicado com sucesso.")

if __name__ == "__main__":
    main()

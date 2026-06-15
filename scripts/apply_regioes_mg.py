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
-- Limpa o cadastro automático de MG para recriar de forma controlada
DELETE FROM app.dim_regiao_comercial
WHERE uf = 'MG';

-- Insere regiões comerciais iniciais de MG com base na mesorregião IBGE.
-- Esta é uma primeira regra de negócio. Depois pode ser ajustada manualmente.
INSERT INTO app.dim_regiao_comercial (
    uf,
    regiao_comercial,
    municipio,
    codigo_ibge,
    prioridade,
    ativo
)
SELECT
    uf,
    CASE
        WHEN mesorregiao = 'Metropolitana de Belo Horizonte' THEN 'Grande BH / Central'
        WHEN mesorregiao = 'Central Mineira' THEN 'Central Mineira'
        WHEN mesorregiao = 'Norte de Minas' THEN 'Norte de MG'
        WHEN mesorregiao = 'Noroeste de Minas' THEN 'Noroeste de MG'
        WHEN mesorregiao = 'Triângulo Mineiro/Alto Paranaíba' THEN 'Triângulo / Alto Paranaíba'
        WHEN mesorregiao = 'Sul/Sudoeste de Minas' THEN 'Sul de MG'
        WHEN mesorregiao = 'Oeste de Minas' THEN 'Oeste de MG'
        WHEN mesorregiao = 'Zona da Mata' THEN 'Zona da Mata'
        WHEN mesorregiao = 'Campo das Vertentes' THEN 'Campo das Vertentes'
        WHEN mesorregiao = 'Vale do Rio Doce' THEN 'Vale do Aço / Rio Doce'
        WHEN mesorregiao IN ('Jequitinhonha', 'Vale do Mucuri') THEN 'Jequitinhonha / Mucuri'
        ELSE 'MG - Não Classificado'
    END AS regiao_comercial,
    municipio,
    codigo_ibge,
    CASE
        WHEN mesorregiao = 'Metropolitana de Belo Horizonte' THEN 1
        WHEN mesorregiao = 'Triângulo Mineiro/Alto Paranaíba' THEN 2
        WHEN mesorregiao = 'Sul/Sudoeste de Minas' THEN 3
        WHEN mesorregiao = 'Zona da Mata' THEN 4
        WHEN mesorregiao = 'Vale do Rio Doce' THEN 5
        ELSE 9
    END AS prioridade,
    TRUE AS ativo
FROM dw.dim_geografia
WHERE uf = 'MG'
ON CONFLICT (uf, regiao_comercial, municipio)
DO UPDATE SET
    codigo_ibge = EXCLUDED.codigo_ibge,
    prioridade = EXCLUDED.prioridade,
    ativo = TRUE;

-- Atualiza a dimensão geográfica com a região comercial cadastrada
UPDATE dw.dim_geografia g
SET
    regiao_comercial = r.regiao_comercial,
    data_atualizacao = NOW()
FROM app.dim_regiao_comercial r
WHERE g.codigo_ibge = r.codigo_ibge
  AND g.uf = 'MG'
  AND r.uf = 'MG';
"""


def main():
    engine = get_engine()

    with engine.begin() as conn:
        logger.info("Aplicando regiões comerciais iniciais de MG...")
        conn.execute(text(SQL))

        resumo = conn.execute(text("""
            SELECT
                regiao_comercial,
                COUNT(*) AS qtd_municipios
            FROM app.dim_regiao_comercial
            WHERE uf = 'MG'
            GROUP BY regiao_comercial
            ORDER BY regiao_comercial
        """)).fetchall()

    logger.info("Regiões comerciais de MG aplicadas com sucesso.")
    print("\nRegiões comerciais de MG:")
    for regiao, qtd in resumo:
        print(f"- {regiao}: {qtd} municípios")


if __name__ == "__main__":
    main()

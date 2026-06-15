from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine
from src.utils.logs import get_logger

logger = get_logger(__name__)
ROOT = Path(__file__).resolve().parents[1]

SQL_IBGE = ROOT / "src/database/ibge_indicadores.sql"
SQL_AUDITORIA = ROOT / "src/database/auditoria.sql"

CHECK_SQL = """
SELECT
    to_regclass('staging.ibge_sidra_municipal') IS NOT NULL AS has_staging,
    to_regclass('dw.fato_indicador_municipal') IS NOT NULL AS has_dw,
    to_regclass('app.fato_potencial_regional') IS NOT NULL AS has_potencial,
    to_regclass('app.mv_potencial_regional_atual') IS NOT NULL AS has_mv,
    to_regclass('app.vw_saude_sistema') IS NOT NULL AS has_saude;
"""


def _exec_file(engine, sql_file: Path):
    logger.info("Aplicando SQL: %s", sql_file)
    with engine.begin() as conn:
        conn.execute(text(sql_file.read_text(encoding="utf-8")))


def main():
    engine = get_engine()

    # Rodar em transações separadas evita que uma falha posterior desfaça a criação das tabelas da etapa 8.
    _exec_file(engine, SQL_IBGE)
    _exec_file(engine, SQL_AUDITORIA)

    with engine.begin() as conn:
        row = conn.execute(text(CHECK_SQL)).mappings().first()

    print("\n✅ Hotfix Etapa 8.3 aplicado.")
    print("Objetos verificados:")
    print(f"- staging.ibge_sidra_municipal: {row['has_staging']}")
    print(f"- dw.fato_indicador_municipal: {row['has_dw']}")
    print(f"- app.fato_potencial_regional: {row['has_potencial']}")
    print(f"- app.mv_potencial_regional_atual: {row['has_mv']}")
    print(f"- app.vw_saude_sistema: {row['has_saude']}")


if __name__ == "__main__":
    main()

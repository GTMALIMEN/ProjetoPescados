from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pathlib import Path
from sqlalchemy import text

from src.database.connection import get_engine


def aplicar_preflight_views(conn, root_dir):
    """Remove views antigas que conflitam com CREATE OR REPLACE VIEW.

    Sem isso, um banco já inicializado em versão anterior pode falhar no
    PostgreSQL quando a nova view muda nomes/ordem de colunas.
    """
    sql_path = root_dir / "src" / "database" / "preflight_drop_conflicting_views.sql"
    if sql_path.exists():
        conn.execute(text(sql_path.read_text(encoding="utf-8")))

from src.utils.logs import get_logger


logger = get_logger(__name__)

ROOT = Path(__file__).resolve().parents[1]

SQL_FILES = [
    ROOT / "src/database/create_schemas.sql",
    ROOT / "src/database/models.sql",
    ROOT / "src/database/indexes.sql",
    ROOT / "src/database/geografia.sql",
    ROOT / "src/database/vendas.sql",
    ROOT / "src/database/scores.sql",
    ROOT / "src/database/recommendations.sql",
    ROOT / "src/database/ibge_indicadores.sql",
    ROOT / "src/database/expansao_v2_publica.sql",
    ROOT / "src/database/fontes_automaticas_idh_ceagesp.sql",
    ROOT / "src/database/importadores_manuais_v2.sql",
    ROOT / "src/database/etapa9_potencial_scores.sql",
    ROOT / "src/database/setorial.sql",
    ROOT / "src/database/fontes_reais.sql",
    ROOT / "src/database/etapa12_setorial_scores.sql",
    ROOT / "src/database/etapa13_whatif.sql",
    ROOT / "src/database/etapa14_alertas_ativos.sql",
    ROOT / "src/database/etapa15_relatorio_executivo.sql",
    ROOT / "src/database/etapa16_pipeline.sql",
    ROOT / "src/database/auditoria.sql",
    ROOT / "src/database/materialized_views.sql",
    ROOT / "src/database/seeds.sql",
]


def main():
    engine = get_engine()

    with engine.begin() as conn:
        aplicar_preflight_views(conn, ROOT_DIR)
        for sql_file in SQL_FILES:
            logger.info("Executando SQL: %s", sql_file)
            sql = sql_file.read_text(encoding="utf-8")
            conn.execute(text(sql))

    logger.info("Banco inicializado com sucesso.")


if __name__ == "__main__":
    main()

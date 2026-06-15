from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine
from src.utils.logs import get_logger

logger = get_logger(__name__)


def main():
    sql_file = ROOT_DIR / "src/database/etapa16_pipeline.sql"
    engine = get_engine()

    with engine.begin() as conn:
        logger.info("Aplicando Etapa 16: %s", sql_file)
        conn.execute(text(sql_file.read_text(encoding="utf-8")))

        checks = [
            "app.pipeline_execucao",
            "app.pipeline_etapa_execucao",
            "app.vw_pipeline_ultimas_execucoes",
            "app.vw_pipeline_etapas_recentes",
            "app.vw_pipeline_saude",
        ]

        for name in checks:
            exists = conn.execute(text("SELECT to_regclass(:name) IS NOT NULL"), {"name": name}).scalar()
            print(f"{name}: {exists}")

    logger.info("Etapa 16 aplicada com sucesso.")


if __name__ == "__main__":
    main()

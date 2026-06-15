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
    sql_file = ROOT_DIR / "src/database/etapa9_potencial_scores.sql"

    engine = get_engine()
    with engine.begin() as conn:
        logger.info("Aplicando Etapa 9: %s", sql_file)
        conn.execute(text(sql_file.read_text(encoding="utf-8")))

        checks = [
            "app.fato_score_regional",
            "app.fato_recomendacao",
            "app.mv_score_regional_atual",
            "app.mv_recomendacao_atual",
        ]

        for name in checks:
            exists = conn.execute(text("SELECT to_regclass(:name) IS NOT NULL"), {"name": name}).scalar()
            print(f"{name}: {exists}")

    logger.info("Etapa 9 aplicada com sucesso.")


if __name__ == "__main__":
    main()

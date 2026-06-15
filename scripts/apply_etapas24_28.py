
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine


def main():
    sql_path = ROOT_DIR / "src" / "database" / "etapas24_28.sql"
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(sql_path.read_text(encoding="utf-8")))
    print("✅ Estrutura das Etapas 24 a 28 aplicada.")


if __name__ == "__main__":
    main()

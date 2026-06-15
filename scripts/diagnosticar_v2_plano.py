
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from sqlalchemy import text
from src.database.connection import get_engine


def main():
    engine = get_engine()
    with engine.begin() as conn:
        exists = conn.execute(text("SELECT to_regclass('app.vw_diagnostico_v2_plano') IS NOT NULL")).scalar()

        if not exists:
            print("❌ View app.vw_diagnostico_v2_plano não existe. Rode:")
            print("python scripts/apply_expansao_v2_publica.py")
            return

        df = pd.read_sql(text("SELECT * FROM app.vw_diagnostico_v2_plano ORDER BY item"), conn)

    print("\nDiagnóstico V2 — Plano x Dados")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()

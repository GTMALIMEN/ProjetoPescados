from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine


def main():
    engine = get_engine()

    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT
                COALESCE(fonte, '') AS fonte,
                COALESCE(categoria, '') AS categoria,
                COALESCE(produto, '') AS produto,
                COALESCE(uf, '') AS uf,
                COUNT(*) AS qtd,
                MIN(data) AS primeira_data,
                MAX(data) AS ultima_data
            FROM dw.fato_indicador_setorial
            GROUP BY fonte, categoria, produto, uf
            ORDER BY categoria, produto, fonte, uf
        """)).fetchall()

    if not rows:
        print("Nenhum indicador setorial encontrado.")
        return

    print("\nDiagnóstico de fontes setoriais:\n")
    for row in rows:
        print(
            f"- fonte={row.fonte} | categoria={row.categoria} | produto={row.produto} | "
            f"uf={row.uf} | qtd={row.qtd} | periodo={row.primeira_data} até {row.ultima_data}"
        )


if __name__ == "__main__":
    main()

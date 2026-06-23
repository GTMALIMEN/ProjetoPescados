from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from src.database.connection import get_engine

BASE_VIEW = "vw_idc_completo_atual_base_demografia"
WRAPPER_VIEW = "vw_idc_completo_atual"

def rel_exists(conn, relname):
    return conn.execute(
        text("SELECT to_regclass(:relname) IS NOT NULL"),
        {"relname": relname}
    ).scalar()

def get_columns(conn, schema, table):
    rows = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = :schema
          AND table_name = :table
        ORDER BY ordinal_position
    """), {"schema": schema, "table": table}).fetchall()
    return [r[0] for r in rows]

def main():
    engine = get_engine()

    with engine.begin() as conn:
        cols_exp = get_columns(conn, "app", "fato_expansao_municipio")

        micro_col = None
        for c in ["microrregiao", "microregiao", "regiao_comercial"]:
            if c in cols_exp:
                micro_col = c
                break

        if micro_col is None:
            raise RuntimeError(
                "Não encontrei coluna de microrregião em app.fato_expansao_municipio."
            )

        current_exists = rel_exists(conn, "app.vw_idc_completo_atual")
        base_exists = rel_exists(conn, f"app.{BASE_VIEW}")

        if current_exists:
            viewdef = conn.execute(
                text("SELECT pg_get_viewdef('app.vw_idc_completo_atual'::regclass, true)")
            ).scalar() or ""

            # Se a view atual ainda não é wrapper, transforma ela em base.
            if BASE_VIEW not in viewdef:
                conn.execute(text(f"DROP VIEW IF EXISTS app.{BASE_VIEW} CASCADE;"))
                conn.execute(text(f"ALTER VIEW app.{WRAPPER_VIEW} RENAME TO {BASE_VIEW};"))
                print(f"✅ View original renomeada para app.{BASE_VIEW}")
        elif not base_exists:
            raise RuntimeError("Não existe app.vw_idc_completo_atual nem base anterior.")

        base_cols = get_columns(conn, "app", BASE_VIEW)

        desejadas = {
            "pop_masculina": "dem.pop_masculina",
            "pop_feminina": "dem.pop_feminina",
            "pop_0_14": "dem.pop_0_14",
            "pop_15_29": "dem.pop_15_29",
            "pop_30_44": "dem.pop_30_44",
            "pop_45_59": "dem.pop_45_59",
            "pop_60_plus": "dem.pop_60_plus",
            "pct_masculina": "dem.pct_masculina",
            "pct_feminina": "dem.pct_feminina",
            "pct_0_14": "dem.pct_0_14",
            "pct_15_29": "dem.pct_15_29",
            "pct_30_44": "dem.pct_30_44",
            "pct_45_59": "dem.pct_45_59",
            "pct_60_plus": "dem.pct_60_plus",
            "fonte_demografia_censo": "dem.fonte_demografia_censo",
        }

        # Só adiciona na wrapper o que a base ainda não possui.
        extras = [
            f"{expr} AS {col}"
            for col, expr in desejadas.items()
            if col not in base_cols
        ]

        if not extras:
            print("✅ A view base já possui todas as colunas demográficas necessárias.")
            return

        extras_sql = ",\n    ".join(extras)

        sql = f"""
        CREATE OR REPLACE VIEW app.{WRAPPER_VIEW} AS
        WITH dem AS (
            SELECT
                e.uf AS estado,
                e."{micro_col}"::text AS microrregiao,

                SUM(COALESCE(d.pop_masculina, 0)) AS pop_masculina,
                SUM(COALESCE(d.pop_feminina, 0)) AS pop_feminina,
                SUM(COALESCE(d.pop_0_14, 0)) AS pop_0_14,
                SUM(COALESCE(d.pop_15_29, 0)) AS pop_15_29,
                SUM(COALESCE(d.pop_30_44, 0)) AS pop_30_44,
                SUM(COALESCE(d.pop_45_59, 0)) AS pop_45_59,
                SUM(COALESCE(d.pop_60_plus, 0)) AS pop_60_plus,

                CASE WHEN SUM(COALESCE(d.populacao, 0)) > 0
                    THEN SUM(COALESCE(d.pop_masculina, 0)) / SUM(COALESCE(d.populacao, 0)) * 100
                    ELSE NULL END AS pct_masculina,

                CASE WHEN SUM(COALESCE(d.populacao, 0)) > 0
                    THEN SUM(COALESCE(d.pop_feminina, 0)) / SUM(COALESCE(d.populacao, 0)) * 100
                    ELSE NULL END AS pct_feminina,

                CASE WHEN SUM(COALESCE(d.populacao, 0)) > 0
                    THEN SUM(COALESCE(d.pop_0_14, 0)) / SUM(COALESCE(d.populacao, 0)) * 100
                    ELSE NULL END AS pct_0_14,

                CASE WHEN SUM(COALESCE(d.populacao, 0)) > 0
                    THEN SUM(COALESCE(d.pop_15_29, 0)) / SUM(COALESCE(d.populacao, 0)) * 100
                    ELSE NULL END AS pct_15_29,

                CASE WHEN SUM(COALESCE(d.populacao, 0)) > 0
                    THEN SUM(COALESCE(d.pop_30_44, 0)) / SUM(COALESCE(d.populacao, 0)) * 100
                    ELSE NULL END AS pct_30_44,

                CASE WHEN SUM(COALESCE(d.populacao, 0)) > 0
                    THEN SUM(COALESCE(d.pop_45_59, 0)) / SUM(COALESCE(d.populacao, 0)) * 100
                    ELSE NULL END AS pct_45_59,

                CASE WHEN SUM(COALESCE(d.populacao, 0)) > 0
                    THEN SUM(COALESCE(d.pop_60_plus, 0)) / SUM(COALESCE(d.populacao, 0)) * 100
                    ELSE NULL END AS pct_60_plus,

                'IBGE SIDRA Censo 2022 tabela 9514' AS fonte_demografia_censo

            FROM app.fato_expansao_municipio e
            JOIN app.fato_demografia_renda_municipio d
              ON e.codigo_ibge::text = d.codigo_ibge
            WHERE e.uf IN ('MG','SP','RJ','ES')
            GROUP BY e.uf, e."{micro_col}"::text
        )
        SELECT
            b.*,
            {extras_sql}
        FROM app.{BASE_VIEW} b
        LEFT JOIN dem
          ON dem.estado = b.estado
         AND dem.microrregiao = b.microrregiao;
        """

        conn.execute(text(sql))

    print("✅ View app.vw_idc_completo_atual atualizada com faixas etárias do Censo.")

    # Deixa o apply_etapas41 chamando este hotfix automaticamente no futuro.
    apply_path = ROOT / "scripts" / "apply_etapas41.py"

    if apply_path.exists():
        txt = apply_path.read_text(encoding="utf-8")

        marker = "hotfix_vw_idc_demografia_faixas.py"

        if marker not in txt:
            old = "execute_sql_file(str(sql_path))"

            new = """execute_sql_file(str(sql_path))

    hotfix = ROOT_DIR / "scripts" / "hotfix_vw_idc_demografia_faixas.py"
    if hotfix.exists():
        import subprocess
        subprocess.run([sys.executable, str(hotfix)], check=True)"""

            if old in txt:
                txt = txt.replace(old, new)
                apply_path.write_text(txt, encoding="utf-8")
                print("✅ apply_etapas41.py atualizado para reaplicar este hotfix automaticamente.")

if __name__ == "__main__":
    main()

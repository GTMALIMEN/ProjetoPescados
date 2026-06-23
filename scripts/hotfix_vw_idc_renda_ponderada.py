from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from src.database.connection import get_engine

BASE_VIEW = "vw_idc_completo_atual_base_renda"
FINAL_VIEW = "vw_idc_completo_atual"

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

def q(col):
    return '"' + col.replace('"', '""') + '"'

def main():
    engine = get_engine()

    with engine.begin() as conn:
        cols_exp = get_columns(conn, "app", "fato_expansao_municipio")

        micro_col = None
        for c in ["microrregiao", "microregiao", "regiao_comercial"]:
            if c in cols_exp:
                micro_col = c
                break

        if not micro_col:
            raise RuntimeError("Não encontrei coluna de microrregião em app.fato_expansao_municipio.")

        if not rel_exists(conn, f"app.{FINAL_VIEW}") and not rel_exists(conn, f"app.{BASE_VIEW}"):
            raise RuntimeError("Não encontrei app.vw_idc_completo_atual.")

        if rel_exists(conn, f"app.{FINAL_VIEW}"):
            viewdef = conn.execute(
                text("SELECT pg_get_viewdef('app.vw_idc_completo_atual'::regclass, true)")
            ).scalar() or ""

            if BASE_VIEW not in viewdef:
                conn.execute(text(f"DROP VIEW IF EXISTS app.{BASE_VIEW} CASCADE;"))
                conn.execute(text(f"ALTER VIEW app.{FINAL_VIEW} RENAME TO {BASE_VIEW};"))
                print(f"✅ View atual renomeada para app.{BASE_VIEW}")

        base_cols = get_columns(conn, "app", BASE_VIEW)

        select_cols = []

        for col in base_cols:
            if col == "renda_media":
                select_cols.append("r.renda_media AS renda_media")
            elif col == "renda_mediana":
                select_cols.append("r.renda_mediana AS renda_mediana")
            elif col == "fonte_renda":
                select_cols.append("COALESCE(r.fonte_renda, b.fonte_renda) AS fonte_renda")
            else:
                select_cols.append(f"b.{q(col)} AS {q(col)}")

        if "renda_media" not in base_cols:
            select_cols.append("r.renda_media AS renda_media")

        if "renda_mediana" not in base_cols:
            select_cols.append("r.renda_mediana AS renda_mediana")

        if "fonte_renda" not in base_cols:
            select_cols.append("r.fonte_renda AS fonte_renda")

        select_sql = ",\n            ".join(select_cols)

        sql = f"""
        CREATE OR REPLACE VIEW app.{FINAL_VIEW} AS
        WITH renda AS (
            SELECT
                e.uf AS estado,
                e.{q(micro_col)}::text AS microrregiao,

                CASE
                    WHEN SUM(
                        CASE
                            WHEN d.renda_media IS NOT NULL
                            THEN COALESCE(NULLIF(d.populacao, 0), NULLIF(e.populacao, 0), 0)
                            ELSE 0
                        END
                    ) > 0
                    THEN
                        SUM(
                            d.renda_media
                            * COALESCE(NULLIF(d.populacao, 0), NULLIF(e.populacao, 0), 0)
                        )
                        /
                        SUM(
                            CASE
                                WHEN d.renda_media IS NOT NULL
                                THEN COALESCE(NULLIF(d.populacao, 0), NULLIF(e.populacao, 0), 0)
                                ELSE 0
                            END
                        )
                    ELSE NULL
                END AS renda_media,

                CASE
                    WHEN SUM(
                        CASE
                            WHEN d.renda_mediana IS NOT NULL
                            THEN COALESCE(NULLIF(d.populacao, 0), NULLIF(e.populacao, 0), 0)
                            ELSE 0
                        END
                    ) > 0
                    THEN
                        SUM(
                            d.renda_mediana
                            * COALESCE(NULLIF(d.populacao, 0), NULLIF(e.populacao, 0), 0)
                        )
                        /
                        SUM(
                            CASE
                                WHEN d.renda_mediana IS NOT NULL
                                THEN COALESCE(NULLIF(d.populacao, 0), NULLIF(e.populacao, 0), 0)
                                ELSE 0
                            END
                        )
                    ELSE NULL
                END AS renda_mediana,

                'IBGE SIDRA Censo 2022 tabela 10295' AS fonte_renda

            FROM app.fato_expansao_municipio e
            JOIN app.fato_demografia_renda_municipio d
              ON e.codigo_ibge::text = d.codigo_ibge
            WHERE e.uf IN ('MG','SP','RJ','ES')
            GROUP BY e.uf, e.{q(micro_col)}::text
        )
        SELECT
            {select_sql}
        FROM app.{BASE_VIEW} b
        LEFT JOIN renda r
          ON r.estado = b.estado
         AND r.microrregiao = b.microrregiao;
        """

        conn.execute(text(sql))

    print("✅ View IDC corrigida: renda média agora é ponderada pela população.")

if __name__ == "__main__":
    main()

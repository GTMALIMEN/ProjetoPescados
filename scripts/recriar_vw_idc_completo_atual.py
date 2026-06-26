from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from src.database.connection import get_engine


def q(col):
    return '"' + col.replace('"', '""') + '"'


def get_columns(conn, schema, table):
    rows = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = :schema
          AND table_name = :table
    """), {"schema": schema, "table": table}).fetchall()
    return {r[0] for r in rows}


def pick(cols, options):
    for c in options:
        if c in cols:
            return c
    return None


<<<<<<< HEAD
def col_expr(cols, col):
    if col in cols:
        return f"COALESCE(e.{q(col)}, 0)"
    return "0"


=======
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf
def main():
    engine = get_engine()

    with engine.begin() as conn:
        cols = get_columns(conn, "app", "fato_expansao_municipio")

        micro_col = pick(cols, ["microrregiao", "microregiao", "regiao_comercial"])
        pop_col = pick(cols, ["populacao", "populacao_total"])
        pib_col = pick(cols, ["pib", "pib_total", "valor_pib"])

        if not micro_col:
            raise RuntimeError("Não encontrei microrregião em app.fato_expansao_municipio.")

        if not pop_col:
            raise RuntimeError("Não encontrei população em app.fato_expansao_municipio.")

        if not pib_col:
            raise RuntimeError("Não encontrei PIB em app.fato_expansao_municipio.")

<<<<<<< HEAD
        # Importante:
        # Detecta coluna total ANTES de criar colunas novas.
        # Se total_pdv já existir, usa ela como principal.
        total_pdv_col = pick(cols, ["total_pdv", "pdv_total", "qtd_pdv", "pontos_venda"])

        supermercados_expr = col_expr(cols, "supermercados")
        restaurantes_expr = col_expr(cols, "restaurantes")
        peixarias_expr = col_expr(cols, "peixarias")
        outros_pdv_expr = col_expr(cols, "outros_pdv")

        pdv_detalhado_expr = (
            f"{supermercados_expr} + {restaurantes_expr} + "
            f"{peixarias_expr} + {outros_pdv_expr}"
        )

        if total_pdv_col:
            # Usa total_pdv quando vier preenchido.
            # Se vier vazio/zero, usa detalhamento como fallback.
            pdv_linha_expr = (
                f"CASE "
                f"WHEN COALESCE(e.{q(total_pdv_col)}, 0) > 0 "
                f"THEN COALESCE(e.{q(total_pdv_col)}, 0) "
                f"ELSE ({pdv_detalhado_expr}) "
                f"END"
            )
            fonte_pdv = f"Total PDV principal: {total_pdv_col}; fallback: soma detalhada"
        else:
            pdv_linha_expr = f"({pdv_detalhado_expr})"
            fonte_pdv = "Soma detalhada: supermercados + restaurantes + peixarias + outros_pdv"

        regiao_expr = "NULL::text"
        if "regiao_economica" in cols:
            regiao_expr = "MAX(e.regiao_economica)::text"
        elif "regiao_comercial" in cols:
            regiao_expr = "MAX(e.regiao_comercial)::text"

        idh_expr = "NULL::numeric"
        if "idh" in cols:
            idh_expr = "AVG(NULLIF(e.idh, 0))"
=======
        pdv_cols = [
            c for c in [
                "supermercados",
                "restaurantes",
                "peixarias",
                "outros_pdv",
                "pdv_total",
                "qtd_pdv",
                "pontos_venda",
                "total_pdv"
            ]
            if c in cols
        ]

        if pdv_cols:
            pdv_expr = " + ".join([f"COALESCE(e.{q(c)}, 0)" for c in pdv_cols])
        else:
            pdv_expr = "0"
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf

        conn.execute(text("""
            CREATE SCHEMA IF NOT EXISTS app;

<<<<<<< HEAD
=======
            CREATE TABLE IF NOT EXISTS app.fato_demografia_renda_municipio (
                codigo_ibge TEXT PRIMARY KEY
            );

            ALTER TABLE app.fato_demografia_renda_municipio
                ADD COLUMN IF NOT EXISTS uf TEXT,
                ADD COLUMN IF NOT EXISTS municipio TEXT,
                ADD COLUMN IF NOT EXISTS ano INTEGER DEFAULT 2022,
                ADD COLUMN IF NOT EXISTS populacao NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_masculina NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_feminina NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_0_14 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_15_29 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_30_44 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_45_59 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_60_plus NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_masculina NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_feminina NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_0_14 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_15_29 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_30_44 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_45_59 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_60_plus NUMERIC,
                ADD COLUMN IF NOT EXISTS renda_media NUMERIC,
                ADD COLUMN IF NOT EXISTS renda_mediana NUMERIC,
                ADD COLUMN IF NOT EXISTS fonte_demografia TEXT,
                ADD COLUMN IF NOT EXISTS fonte_renda TEXT,
                ADD COLUMN IF NOT EXISTS data_atualizacao TIMESTAMP DEFAULT NOW();

>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf
            ALTER TABLE app.fato_expansao_municipio
                ADD COLUMN IF NOT EXISTS renda_media NUMERIC,
                ADD COLUMN IF NOT EXISTS renda_mediana NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_masculina NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_feminina NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_0_14 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_15_29 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_30_44 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_45_59 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_60_plus NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_masculina NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_feminina NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_0_14 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_15_29 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_30_44 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_45_59 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_60_plus NUMERIC,
<<<<<<< HEAD
                ADD COLUMN IF NOT EXISTS supermercados NUMERIC,
                ADD COLUMN IF NOT EXISTS restaurantes NUMERIC,
                ADD COLUMN IF NOT EXISTS peixarias NUMERIC,
                ADD COLUMN IF NOT EXISTS outros_pdv NUMERIC,
                ADD COLUMN IF NOT EXISTS fonte_renda TEXT,
                ADD COLUMN IF NOT EXISTS fonte_demografia TEXT;

            CREATE TABLE IF NOT EXISTS app.fato_demografia_renda_municipio (
                codigo_ibge TEXT PRIMARY KEY
            );

            ALTER TABLE app.fato_demografia_renda_municipio
                ADD COLUMN IF NOT EXISTS populacao NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_masculina NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_feminina NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_0_14 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_15_29 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_30_44 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_45_59 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_60_plus NUMERIC,
                ADD COLUMN IF NOT EXISTS renda_media NUMERIC,
                ADD COLUMN IF NOT EXISTS renda_mediana NUMERIC;
=======
                ADD COLUMN IF NOT EXISTS fonte_renda TEXT,
                ADD COLUMN IF NOT EXISTS fonte_demografia TEXT;
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf
        """))

        sql = f"""
        DROP VIEW IF EXISTS app.vw_idc_completo_atual CASCADE;
        DROP VIEW IF EXISTS app.vw_idc_completo_atual_base_renda CASCADE;
        DROP VIEW IF EXISTS app.vw_idc_completo_atual_base_demografia CASCADE;

        CREATE OR REPLACE VIEW app.vw_idc_completo_atual AS
        WITH micro AS (
            SELECT
                e.uf AS estado,
                e.{q(micro_col)}::text AS microrregiao,
<<<<<<< HEAD
                {regiao_expr} AS regiao_economica,
=======
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf

                SUM(COALESCE(e.{q(pop_col)}, 0)) AS populacao,
                SUM(COALESCE(e.{q(pib_col)}, 0)) AS pib,

                CASE
                    WHEN SUM(COALESCE(e.{q(pop_col)}, 0)) > 0
                    THEN SUM(COALESCE(e.{q(pib_col)}, 0)) / SUM(COALESCE(e.{q(pop_col)}, 0))
                    ELSE NULL
                END AS pib_per_capita,

<<<<<<< HEAD
                {idh_expr} AS idh,

=======
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf
                CASE
                    WHEN SUM(
                        CASE
                            WHEN COALESCE(d.renda_media, e.renda_media) IS NOT NULL
                            THEN COALESCE(NULLIF(d.populacao, 0), NULLIF(e.{q(pop_col)}, 0), 0)
                            ELSE 0
                        END
                    ) > 0
                    THEN
                        SUM(
                            COALESCE(d.renda_media, e.renda_media)
                            * COALESCE(NULLIF(d.populacao, 0), NULLIF(e.{q(pop_col)}, 0), 0)
                        )
                        /
                        SUM(
                            CASE
                                WHEN COALESCE(d.renda_media, e.renda_media) IS NOT NULL
                                THEN COALESCE(NULLIF(d.populacao, 0), NULLIF(e.{q(pop_col)}, 0), 0)
                                ELSE 0
                            END
                        )
                    ELSE NULL
                END AS renda_media,

                CASE
                    WHEN SUM(
                        CASE
                            WHEN COALESCE(d.renda_mediana, e.renda_mediana) IS NOT NULL
                            THEN COALESCE(NULLIF(d.populacao, 0), NULLIF(e.{q(pop_col)}, 0), 0)
                            ELSE 0
                        END
                    ) > 0
                    THEN
                        SUM(
                            COALESCE(d.renda_mediana, e.renda_mediana)
                            * COALESCE(NULLIF(d.populacao, 0), NULLIF(e.{q(pop_col)}, 0), 0)
                        )
                        /
                        SUM(
                            CASE
                                WHEN COALESCE(d.renda_mediana, e.renda_mediana) IS NOT NULL
                                THEN COALESCE(NULLIF(d.populacao, 0), NULLIF(e.{q(pop_col)}, 0), 0)
                                ELSE 0
                            END
                        )
                    ELSE NULL
                END AS renda_mediana,

                SUM(COALESCE(d.pop_masculina, e.pop_masculina, 0)) AS pop_masculina,
                SUM(COALESCE(d.pop_feminina, e.pop_feminina, 0)) AS pop_feminina,
                SUM(COALESCE(d.pop_0_14, e.pop_0_14, 0)) AS pop_0_14,
                SUM(COALESCE(d.pop_15_29, e.pop_15_29, 0)) AS pop_15_29,
                SUM(COALESCE(d.pop_30_44, e.pop_30_44, 0)) AS pop_30_44,
                SUM(COALESCE(d.pop_45_59, e.pop_45_59, 0)) AS pop_45_59,
                SUM(COALESCE(d.pop_60_plus, e.pop_60_plus, 0)) AS pop_60_plus,

                CASE
                    WHEN SUM(COALESCE(d.populacao, e.{q(pop_col)}, 0)) > 0
                    THEN SUM(COALESCE(d.pop_masculina, e.pop_masculina, 0))
                         / SUM(COALESCE(d.populacao, e.{q(pop_col)}, 0)) * 100
                    ELSE NULL
                END AS pct_masculina,

                CASE
                    WHEN SUM(COALESCE(d.populacao, e.{q(pop_col)}, 0)) > 0
                    THEN SUM(COALESCE(d.pop_feminina, e.pop_feminina, 0))
                         / SUM(COALESCE(d.populacao, e.{q(pop_col)}, 0)) * 100
                    ELSE NULL
                END AS pct_feminina,

<<<<<<< HEAD
                CASE WHEN SUM(COALESCE(d.pop_0_14, e.pop_0_14, 0) + COALESCE(d.pop_15_29, e.pop_15_29, 0) + COALESCE(d.pop_30_44, e.pop_30_44, 0) + COALESCE(d.pop_45_59, e.pop_45_59, 0) + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)) > 0
                    THEN SUM(COALESCE(d.pop_0_14, e.pop_0_14, 0)) / SUM(COALESCE(d.pop_0_14, e.pop_0_14, 0) + COALESCE(d.pop_15_29, e.pop_15_29, 0) + COALESCE(d.pop_30_44, e.pop_30_44, 0) + COALESCE(d.pop_45_59, e.pop_45_59, 0) + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)) * 100
                    ELSE NULL END AS pct_0_14,

                CASE WHEN SUM(COALESCE(d.pop_0_14, e.pop_0_14, 0) + COALESCE(d.pop_15_29, e.pop_15_29, 0) + COALESCE(d.pop_30_44, e.pop_30_44, 0) + COALESCE(d.pop_45_59, e.pop_45_59, 0) + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)) > 0
                    THEN SUM(COALESCE(d.pop_15_29, e.pop_15_29, 0)) / SUM(COALESCE(d.pop_0_14, e.pop_0_14, 0) + COALESCE(d.pop_15_29, e.pop_15_29, 0) + COALESCE(d.pop_30_44, e.pop_30_44, 0) + COALESCE(d.pop_45_59, e.pop_45_59, 0) + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)) * 100
                    ELSE NULL END AS pct_15_29,

                CASE WHEN SUM(COALESCE(d.pop_0_14, e.pop_0_14, 0) + COALESCE(d.pop_15_29, e.pop_15_29, 0) + COALESCE(d.pop_30_44, e.pop_30_44, 0) + COALESCE(d.pop_45_59, e.pop_45_59, 0) + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)) > 0
                    THEN SUM(COALESCE(d.pop_30_44, e.pop_30_44, 0)) / SUM(COALESCE(d.pop_0_14, e.pop_0_14, 0) + COALESCE(d.pop_15_29, e.pop_15_29, 0) + COALESCE(d.pop_30_44, e.pop_30_44, 0) + COALESCE(d.pop_45_59, e.pop_45_59, 0) + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)) * 100
                    ELSE NULL END AS pct_30_44,

                CASE WHEN SUM(COALESCE(d.pop_0_14, e.pop_0_14, 0) + COALESCE(d.pop_15_29, e.pop_15_29, 0) + COALESCE(d.pop_30_44, e.pop_30_44, 0) + COALESCE(d.pop_45_59, e.pop_45_59, 0) + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)) > 0
                    THEN SUM(COALESCE(d.pop_45_59, e.pop_45_59, 0)) / SUM(COALESCE(d.pop_0_14, e.pop_0_14, 0) + COALESCE(d.pop_15_29, e.pop_15_29, 0) + COALESCE(d.pop_30_44, e.pop_30_44, 0) + COALESCE(d.pop_45_59, e.pop_45_59, 0) + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)) * 100
                    ELSE NULL END AS pct_45_59,

                CASE WHEN SUM(COALESCE(d.pop_0_14, e.pop_0_14, 0) + COALESCE(d.pop_15_29, e.pop_15_29, 0) + COALESCE(d.pop_30_44, e.pop_30_44, 0) + COALESCE(d.pop_45_59, e.pop_45_59, 0) + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)) > 0
                    THEN SUM(COALESCE(d.pop_60_plus, e.pop_60_plus, 0)) / SUM(COALESCE(d.pop_0_14, e.pop_0_14, 0) + COALESCE(d.pop_15_29, e.pop_15_29, 0) + COALESCE(d.pop_30_44, e.pop_30_44, 0) + COALESCE(d.pop_45_59, e.pop_45_59, 0) + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)) * 100
                    ELSE NULL END AS pct_60_plus,

                SUM({supermercados_expr}) AS supermercados,
                SUM({restaurantes_expr}) AS restaurantes,
                SUM({peixarias_expr}) AS peixarias,
                SUM({outros_pdv_expr}) AS outros_pdv,

                SUM({pdv_linha_expr}) AS total_pdv,
                SUM({pdv_linha_expr}) AS pdv_total,

                COUNT(DISTINCT e.codigo_ibge) AS qtd_municipios,

                'IBGE SIDRA Censo 2022 tabela 9514' AS fonte_demografia,
                'IBGE SIDRA Censo 2022 tabela 10295' AS fonte_renda,
                '{fonte_pdv}' AS fonte_pdv,
                NOW() AS data_atualizacao
=======
                CASE
                    WHEN SUM(
                        COALESCE(d.pop_0_14, e.pop_0_14, 0)
                      + COALESCE(d.pop_15_29, e.pop_15_29, 0)
                      + COALESCE(d.pop_30_44, e.pop_30_44, 0)
                      + COALESCE(d.pop_45_59, e.pop_45_59, 0)
                      + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)
                    ) > 0
                    THEN SUM(COALESCE(d.pop_0_14, e.pop_0_14, 0))
                         / SUM(
                            COALESCE(d.pop_0_14, e.pop_0_14, 0)
                          + COALESCE(d.pop_15_29, e.pop_15_29, 0)
                          + COALESCE(d.pop_30_44, e.pop_30_44, 0)
                          + COALESCE(d.pop_45_59, e.pop_45_59, 0)
                          + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)
                         ) * 100
                    ELSE NULL
                END AS pct_0_14,

                CASE
                    WHEN SUM(
                        COALESCE(d.pop_0_14, e.pop_0_14, 0)
                      + COALESCE(d.pop_15_29, e.pop_15_29, 0)
                      + COALESCE(d.pop_30_44, e.pop_30_44, 0)
                      + COALESCE(d.pop_45_59, e.pop_45_59, 0)
                      + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)
                    ) > 0
                    THEN SUM(COALESCE(d.pop_15_29, e.pop_15_29, 0))
                         / SUM(
                            COALESCE(d.pop_0_14, e.pop_0_14, 0)
                          + COALESCE(d.pop_15_29, e.pop_15_29, 0)
                          + COALESCE(d.pop_30_44, e.pop_30_44, 0)
                          + COALESCE(d.pop_45_59, e.pop_45_59, 0)
                          + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)
                         ) * 100
                    ELSE NULL
                END AS pct_15_29,

                CASE
                    WHEN SUM(
                        COALESCE(d.pop_0_14, e.pop_0_14, 0)
                      + COALESCE(d.pop_15_29, e.pop_15_29, 0)
                      + COALESCE(d.pop_30_44, e.pop_30_44, 0)
                      + COALESCE(d.pop_45_59, e.pop_45_59, 0)
                      + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)
                    ) > 0
                    THEN SUM(COALESCE(d.pop_30_44, e.pop_30_44, 0))
                         / SUM(
                            COALESCE(d.pop_0_14, e.pop_0_14, 0)
                          + COALESCE(d.pop_15_29, e.pop_15_29, 0)
                          + COALESCE(d.pop_30_44, e.pop_30_44, 0)
                          + COALESCE(d.pop_45_59, e.pop_45_59, 0)
                          + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)
                         ) * 100
                    ELSE NULL
                END AS pct_30_44,

                CASE
                    WHEN SUM(
                        COALESCE(d.pop_0_14, e.pop_0_14, 0)
                      + COALESCE(d.pop_15_29, e.pop_15_29, 0)
                      + COALESCE(d.pop_30_44, e.pop_30_44, 0)
                      + COALESCE(d.pop_45_59, e.pop_45_59, 0)
                      + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)
                    ) > 0
                    THEN SUM(COALESCE(d.pop_45_59, e.pop_45_59, 0))
                         / SUM(
                            COALESCE(d.pop_0_14, e.pop_0_14, 0)
                          + COALESCE(d.pop_15_29, e.pop_15_29, 0)
                          + COALESCE(d.pop_30_44, e.pop_30_44, 0)
                          + COALESCE(d.pop_45_59, e.pop_45_59, 0)
                          + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)
                         ) * 100
                    ELSE NULL
                END AS pct_45_59,

                CASE
                    WHEN SUM(
                        COALESCE(d.pop_0_14, e.pop_0_14, 0)
                      + COALESCE(d.pop_15_29, e.pop_15_29, 0)
                      + COALESCE(d.pop_30_44, e.pop_30_44, 0)
                      + COALESCE(d.pop_45_59, e.pop_45_59, 0)
                      + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)
                    ) > 0
                    THEN SUM(COALESCE(d.pop_60_plus, e.pop_60_plus, 0))
                         / SUM(
                            COALESCE(d.pop_0_14, e.pop_0_14, 0)
                          + COALESCE(d.pop_15_29, e.pop_15_29, 0)
                          + COALESCE(d.pop_30_44, e.pop_30_44, 0)
                          + COALESCE(d.pop_45_59, e.pop_45_59, 0)
                          + COALESCE(d.pop_60_plus, e.pop_60_plus, 0)
                         ) * 100
                    ELSE NULL
                END AS pct_60_plus,

                SUM({pdv_expr}) AS pdv_total,

                'IBGE SIDRA Censo 2022 tabela 9514' AS fonte_demografia,
                'IBGE SIDRA Censo 2022 tabela 10295' AS fonte_renda
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf

            FROM app.fato_expansao_municipio e
            LEFT JOIN app.fato_demografia_renda_municipio d
              ON e.codigo_ibge::text = d.codigo_ibge
            WHERE e.uf IN ('MG','SP','RJ','ES')
            GROUP BY e.uf, e.{q(micro_col)}::text
        ),
        norm AS (
            SELECT
                *,
<<<<<<< HEAD
                CASE WHEN SUM(populacao) OVER() > 0 THEN populacao / SUM(populacao) OVER() * 100 ELSE NULL END AS participacao_populacao_pct,
                CASE WHEN SUM(pib) OVER() > 0 THEN pib / SUM(pib) OVER() * 100 ELSE NULL END AS participacao_pib_pct,

=======
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf
                CASE WHEN MAX(populacao) OVER() > 0 THEN populacao / MAX(populacao) OVER() * 100 ELSE NULL END AS fator_populacao,
                CASE WHEN MAX(pib) OVER() > 0 THEN pib / MAX(pib) OVER() * 100 ELSE NULL END AS fator_pib,
                CASE WHEN MAX(renda_media) OVER() > 0 THEN renda_media / MAX(renda_media) OVER() * 100 ELSE NULL END AS fator_renda,
                CASE WHEN MAX(pib_per_capita) OVER() > 0 THEN pib_per_capita / MAX(pib_per_capita) OVER() * 100 ELSE NULL END AS fator_pib_per_capita,
<<<<<<< HEAD

                CASE WHEN MAX(pct_30_44) OVER() > 0 THEN pct_30_44 / MAX(pct_30_44) OVER() * 100 ELSE NULL END AS fator_pop_30_44,
                CASE WHEN MAX(pct_15_29) OVER() > 0 THEN pct_15_29 / MAX(pct_15_29) OVER() * 100 ELSE NULL END AS fator_pop_15_29,
                CASE WHEN MAX(pct_masculina) OVER() > 0 THEN pct_masculina / MAX(pct_masculina) OVER() * 100 ELSE NULL END AS fator_masculino,
                CASE WHEN MAX(pct_feminina) OVER() > 0 THEN pct_feminina / MAX(pct_feminina) OVER() * 100 ELSE NULL END AS fator_feminino,
                CASE WHEN MAX(restaurantes) OVER() > 0 THEN restaurantes / MAX(restaurantes) OVER() * 100 ELSE NULL END AS fator_restaurantes,
                CASE WHEN MAX(total_pdv) OVER() > 0 THEN total_pdv / MAX(total_pdv) OVER() * 100 ELSE NULL END AS fator_pdv_total,
                CASE WHEN MAX(total_pdv) OVER() > 0 THEN total_pdv / MAX(total_pdv) OVER() * 100 ELSE NULL END AS fator_pdv
=======
                CASE WHEN MAX(pct_feminina) OVER() > 0 THEN pct_feminina / MAX(pct_feminina) OVER() * 100 ELSE NULL END AS fator_feminino,
                CASE WHEN MAX(pct_masculina) OVER() > 0 THEN pct_masculina / MAX(pct_masculina) OVER() * 100 ELSE NULL END AS fator_masculino,
                CASE WHEN MAX(pdv_total) OVER() > 0 THEN pdv_total / MAX(pdv_total) OVER() * 100 ELSE NULL END AS fator_pdv
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf
            FROM micro
        ),
        idc_calc AS (
            SELECT
                *,
                (
<<<<<<< HEAD
                    COALESCE(fator_pib, 0) * 0.25
                  + COALESCE(fator_pop_30_44, 0) * 0.40
                  + COALESCE(fator_masculino, 0) * 0.10
                  + COALESCE(fator_feminino, 0) * 0.00
                  + COALESCE(fator_restaurantes, 0) * 0.10
                  + COALESCE(fator_pop_15_29, 0) * 0.10
                  + COALESCE(fator_pdv_total, 0) * 0.05
                ) AS idc_planejado,

                'IDC = PIB 25% + População 30-44 40% + Masculino 10% + Feminino 0% + Restaurantes 10% + População 15-29 10% + Total PDV 5%'::text AS formula_idc
=======
                    COALESCE(fator_populacao, 0) * 0.30
                  + COALESCE(fator_pib, 0) * 0.25
                  + COALESCE(fator_renda, 0) * 0.15
                  + COALESCE(fator_pib_per_capita, 0) * 0.15
                  + COALESCE(fator_feminino, 0) * 0.05
                  + COALESCE(fator_masculino, 0) * 0.05
                  + COALESCE(fator_pdv, 0) * 0.05
                ) AS idc_planejado
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf
            FROM norm
        )
        SELECT
            *,
            idc_planejado AS idc,
            idc_planejado AS idc_final,
<<<<<<< HEAD
            idc_planejado AS idc_base,
            idc_planejado AS idc_macro,
=======
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf
            idc_planejado AS score,
            idc_planejado AS score_idc,
            CASE
                WHEN idc_planejado >= 75 THEN 'Alta'
                WHEN idc_planejado >= 55 THEN 'Média'
                WHEN idc_planejado >= 35 THEN 'Baixa'
                ELSE 'Monitorar'
<<<<<<< HEAD
            END AS classificacao_score,
            CASE
                WHEN idc_planejado >= 75 THEN 'Alta'
                WHEN idc_planejado >= 55 THEN 'Média'
                WHEN idc_planejado >= 35 THEN 'Baixa'
                ELSE 'Monitorar'
            END AS classificacao
=======
            END AS classificacao_score
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf
        FROM idc_calc;
        """

        conn.execute(text(sql))

<<<<<<< HEAD
    print("✅ app.vw_idc_completo_atual recriada com IDC oficial novo.")
    print("✅ Regra PDV: usa total_pdv se existir/preenchido; se não, usa soma detalhada.")
    print("✅ Fórmula IDC oficial: PIB 25 + Pop 30-44 40 + Masc 10 + Fem 0 + Restaurantes 10 + Pop 15-29 10 + Total PDV 5.")
=======
    print("✅ app.vw_idc_completo_atual recriada do zero com demografia, renda e IDC planejado.")
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf


if __name__ == "__main__":
    main()

from pathlib import Path
import sys
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database.connection import get_engine


def table_exists(conn, schema, table):
    return conn.execute(
        text("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = :schema
              AND table_name = :table
        """),
        {"schema": schema, "table": table},
    ).scalar() > 0


def salvar(conn, grupo, tabela, regra, status, qtd, detalhe):
    conn.execute(
        text("""
            INSERT INTO app.validacao_dados_resultado (
                grupo_validacao,
                tabela,
                regra,
                status,
                qtd_problemas,
                detalhe
            )
            VALUES (
                :grupo,
                :tabela,
                :regra,
                :status,
                :qtd,
                :detalhe
            )
        """),
        {
            "grupo": grupo,
            "tabela": tabela,
            "regra": regra,
            "status": status,
            "qtd": int(qtd or 0),
            "detalhe": detalhe,
        },
    )


def validar(conn, grupo, tabela, regra, sql, ok_msg, erro_msg):
    try:
        qtd = conn.execute(text(sql)).scalar()
        qtd = int(qtd or 0)
        status = "OK" if qtd == 0 else "ERRO"
        detalhe = ok_msg if qtd == 0 else erro_msg
        salvar(conn, grupo, tabela, regra, status, qtd, detalhe)
        print(f"{'✅' if status == 'OK' else '❌'} {tabela} | {regra} | problemas={qtd}")
    except Exception as e:
        salvar(conn, grupo, tabela, regra, "FALHA_VALIDACAO", 1, str(e))
        print(f"⚠️ {tabela} | {regra} | falha={e}")


def main():
    engine = get_engine()

    with engine.begin() as conn:
        print("\n==============================")
        print("VALIDAÇÃO DO CATÁLOGO DE FONTES")
        print("==============================")

        validar(
            conn,
            "FONTES",
            "app.catalogo_fonte_dados",
            "Fontes oficiais sem origem/url/tabela",
            """
            SELECT COUNT(*)
            FROM app.catalogo_fonte_dados
            WHERE oficial = TRUE
              AND (
                    origem IS NULL
                    OR TRIM(origem) = ''
                  )
            """,
            "Fontes oficiais possuem origem identificada.",
            "Existe fonte oficial sem origem identificada."
        )

        print("\n==============================")
        print("VALIDAÇÃO IDC / EXPANSÃO")
        print("==============================")

        if table_exists(conn, "app", "vw_idc_completo_atual"):
            validar(
                conn,
                "IDC",
                "app.vw_idc_completo_atual",
                "Duplicidade por estado + microrregião",
                """
                SELECT COUNT(*)
                FROM (
                    SELECT estado, microrregiao, COUNT(*) qtd
                    FROM app.vw_idc_completo_atual
                    GROUP BY estado, microrregiao
                    HAVING COUNT(*) > 1
                ) x
                """,
                "Sem duplicidade por estado/microrregião.",
                "Existem microrregiões duplicadas no IDC."
            )

            validar(
                conn,
                "IDC",
                "app.vw_idc_completo_atual",
                "IDC fora da faixa 0 a 100",
                """
                SELECT COUNT(*)
                FROM app.vw_idc_completo_atual
                WHERE idc_base IS NULL
                   OR idc_base < 0
                   OR idc_base > 100
                """,
                "IDC dentro da faixa esperada.",
                "IDC nulo ou fora da faixa 0-100."
            )

            validar(
                conn,
                "IDC",
                "app.vw_idc_completo_atual",
                "Percentuais demográficos fora da faixa",
                """
                SELECT COUNT(*)
                FROM app.vw_idc_completo_atual
                WHERE pct_masculina < 0 OR pct_masculina > 100
                   OR pct_feminina < 0 OR pct_feminina > 100
                   OR pct_15_29 < 0 OR pct_15_29 > 100
                   OR pct_30_44 < 0 OR pct_30_44 > 100
                """,
                "Percentuais demográficos dentro da faixa 0-100.",
                "Existem percentuais demográficos fora da faixa 0-100."
            )

            validar(
                conn,
                "IDC",
                "app.vw_idc_completo_atual",
                "População, PIB ou PDV negativos",
                """
                SELECT COUNT(*)
                FROM app.vw_idc_completo_atual
                WHERE populacao < 0
                   OR pib < 0
                   OR COALESCE(total_pdv, pdv_total, 0) < 0
                """,
                "Sem valores negativos em população, PIB e PDV.",
                "Há valores negativos em população, PIB ou PDV."
            )

            validar(
                conn,
                "IDC",
                "app.vw_idc_completo_atual",
                "Fonte de renda pendente/nula",
                """
                SELECT COUNT(*)
                FROM app.vw_idc_completo_atual
                WHERE fonte_renda IS NULL
                   OR fonte_renda ILIKE '%pendente%'
                   OR renda_media IS NULL
                """,
                "Renda preenchida com fonte identificada.",
                "Há renda nula/pendente ou fonte de renda não identificada."
            )

            validar(
                conn,
                "IDC",
                "app.vw_idc_completo_atual",
                "Fonte de demografia pendente/nula",
                """
                SELECT COUNT(*)
                FROM app.vw_idc_completo_atual
                WHERE fonte_demografia IS NULL
                   OR fonte_demografia ILIKE '%pendente%'
                   OR pct_masculina IS NULL
                   OR pct_feminina IS NULL
                   OR pct_15_29 IS NULL
                   OR pct_30_44 IS NULL
                """,
                "Demografia preenchida com fonte identificada.",
                "Há demografia nula/pendente ou fonte demográfica não identificada."
            )

        print("\n==============================")
        print("VALIDAÇÃO BASE MUNICIPAL")
        print("==============================")

        if table_exists(conn, "app", "fato_expansao_municipio"):
            validar(
                conn,
                "BASE_PUBLICA",
                "app.fato_expansao_municipio",
                "Duplicidade por código IBGE",
                """
                SELECT COUNT(*)
                FROM (
                    SELECT codigo_ibge, COUNT(*) qtd
                    FROM app.fato_expansao_municipio
                    GROUP BY codigo_ibge
                    HAVING COUNT(*) > 1
                ) x
                """,
                "Sem duplicidade por código IBGE.",
                "Existem códigos IBGE duplicados."
            )

            validar(
                conn,
                "BASE_PUBLICA",
                "app.fato_expansao_municipio",
                "Municípios sem UF ou microrregião",
                """
                SELECT COUNT(*)
                FROM app.fato_expansao_municipio
                WHERE uf IS NULL
                   OR TRIM(uf) = ''
                   OR microrregiao IS NULL
                   OR TRIM(microrregiao) = ''
                """,
                "UF e microrregião preenchidas.",
                "Existem municípios sem UF ou microrregião."
            )

        print("\n==============================")
        print("VALIDAÇÃO BASES MANUAIS")
        print("==============================")

        tabelas_manuais = [
            "fato_mercado_privado",
            "fato_curva_mercado_categoria",
            "dim_key_account_loja",
            "fato_receita_manual_expansao",
            "fato_compra_manual",
            "fato_ceagesp_pescados",
            "fato_previa_vendedores",
        ]

        for tabela in tabelas_manuais:
            if not table_exists(conn, "app", tabela):
                continue

            validar(
                conn,
                "BASES_MANUAIS",
                f"app.{tabela}",
                "Duplicidade por hash_linha",
                f"""
                SELECT COUNT(*)
                FROM (
                    SELECT hash_linha, COUNT(*) qtd
                    FROM app.{tabela}
                    WHERE hash_linha IS NOT NULL
                    GROUP BY hash_linha
                    HAVING COUNT(*) > 1
                ) x
                """,
                "Sem duplicidade por hash_linha.",
                "Existem duplicidades por hash_linha."
            )


        print("\n==============================")
        print("VALIDAÇÃO CLASSES DE RENDA A-E")
        print("==============================")

        if table_exists(conn, "app", "fato_classe_renda_oficial_regiao"):
            validar(
                conn,
                "CLASSE_RENDA",
                "app.fato_classe_renda_oficial_regiao",
                "Classes A-E nulas",
                """
                SELECT COUNT(*)
                FROM app.fato_classe_renda_oficial_regiao
                WHERE classe_a_pct IS NULL
                   OR classe_b_pct IS NULL
                   OR classe_c_pct IS NULL
                   OR classe_d_pct IS NULL
                   OR classe_e_pct IS NULL
                """,
                "Classes A-E preenchidas.",
                "Existem classes A-E nulas."
            )

            validar(
                conn,
                "CLASSE_RENDA",
                "app.fato_classe_renda_oficial_regiao",
                "Classes A-E negativas",
                """
                SELECT COUNT(*)
                FROM app.fato_classe_renda_oficial_regiao
                WHERE classe_a_pct < 0
                   OR classe_b_pct < 0
                   OR classe_c_pct < 0
                   OR classe_d_pct < 0
                   OR classe_e_pct < 0
                """,
                "Classes A-E sem valores negativos.",
                "Existem classes A-E negativas."
            )

            validar(
                conn,
                "CLASSE_RENDA",
                "app.fato_classe_renda_oficial_regiao",
                "Soma Classes A-E fora de 95 a 105",
                """
                SELECT COUNT(*)
                FROM app.fato_classe_renda_oficial_regiao
                WHERE COALESCE(classe_a_pct,0)
                    + COALESCE(classe_b_pct,0)
                    + COALESCE(classe_c_pct,0)
                    + COALESCE(classe_d_pct,0)
                    + COALESCE(classe_e_pct,0) NOT BETWEEN 95 AND 105
                """,
                "Soma das classes A-E dentro da faixa esperada.",
                "Soma das classes A-E fora da faixa esperada."
            )

            validar(
                conn,
                "CLASSE_RENDA",
                "app.fato_classe_renda_oficial_regiao",
                "Fonte ou nível da classe de renda ausente",
                """
                SELECT COUNT(*)
                FROM app.fato_classe_renda_oficial_regiao
                WHERE fonte_classe_renda IS NULL
                   OR TRIM(fonte_classe_renda) = ''
                   OR nivel_fonte_classe_renda IS NULL
                   OR TRIM(nivel_fonte_classe_renda) = ''
                """,
                "Fonte e nível das classes de renda preenchidos.",
                "Fonte ou nível da classe de renda ausente."
            )

        print("\n✅ Validação finalizada.")
        print("Consulte app.validacao_dados_resultado para o histórico completo.")


if __name__ == "__main__":
    main()

from pathlib import Path
import py_compile
import shutil

path = Path("scripts/validar_dados_completo.py")
backup = path.with_suffix(".py.bak_series_dinamicas")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

# ============================================================
# 1) Adiciona funções auxiliares se ainda não existirem
# ============================================================

if "def get_columns(conn, schema, table):" not in txt:
    anchor = "def cols_exist(conn, schema, table, cols):\n    return all(col_exists(conn, schema, table, c) for c in cols)\n"
    helper = r'''
def get_columns(conn, schema, table):
    rows = conn.execute(
        text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
        """),
        {"schema": schema, "table": table},
    ).fetchall()

    return {r[0] for r in rows}


def pick_col(cols, options):
    for c in options:
        if c in cols:
            return c
    return None


def q(col):
    return '"' + str(col).replace('"', '""') + '"'
'''
    if anchor not in txt:
        raise RuntimeError("Não encontrei ponto para inserir helpers.")
    txt = txt.replace(anchor, anchor + "\n" + helper + "\n", 1)

# ============================================================
# 2) Troca a validação de séries econômicas por versão dinâmica
# ============================================================

start_marker = '        print("\\n==============================")\n        print("VALIDAÇÃO SÉRIES ECONÔMICAS")\n        print("==============================")'
end_marker = '        print("\\n==============================")\n        print("RESULTADO FINAL")\n        print("==============================")'

start = txt.find(start_marker)
end = txt.find(end_marker, start)

if start == -1 or end == -1:
    raise RuntimeError("Não encontrei bloco de validação de séries econômicas para substituir.")

novo_bloco = r'''        print("\n==============================")
        print("VALIDAÇÃO SÉRIES ECONÔMICAS")
        print("==============================")

        if table_exists(conn, "dw", "fato_serie_historica"):
            cols_series = get_columns(conn, "dw", "fato_serie_historica")

            indicador_col = pick_col(cols_series, [
                "indicador",
                "nome_indicador",
                "codigo_indicador",
                "serie",
                "codigo_serie",
                "fonte",
                "nome_serie",
            ])

            data_col = pick_col(cols_series, [
                "data_referencia",
                "dt_referencia",
                "data",
                "data_ref",
                "periodo",
                "ano_mes",
                "mes",
                "data_competencia",
                "dt_competencia",
            ])

            valor_col = pick_col(cols_series, [
                "valor",
                "vlr",
                "valor_serie",
                "valor_observado",
                "valor_indicador",
            ])

            geo_col = pick_col(cols_series, [
                "codigo_geografia",
                "codigo_ibge",
                "uf",
                "estado",
                "regiao",
                "geografia",
            ])

            if not indicador_col or not data_col or not valor_col:
                salvar_resultado(
                    conn,
                    "dw.fato_serie_historica",
                    "Estrutura mínima para validação de séries",
                    "ALERTA",
                    1,
                    "Não foi possível validar duplicidade/valor porque faltam colunas esperadas. "
                    f"Colunas encontradas: {sorted(cols_series)}"
                )
                print("⚠️ dw.fato_serie_historica | Estrutura mínima para validação de séries | ALERTA | problemas=1")
                print("   Colunas encontradas:", sorted(cols_series))
            else:
                if geo_col:
                    group_expr = f"{q(indicador_col)}, {q(data_col)}, COALESCE({q(geo_col)}::text, '')"
                else:
                    group_expr = f"{q(indicador_col)}, {q(data_col)}"

                validar(
                    conn,
                    "dw.fato_serie_historica",
                    "Duplicidade por indicador + data + geografia disponível",
                    f"""
                    SELECT COUNT(*)
                    FROM (
                        SELECT {group_expr}, COUNT(*) qtd
                        FROM dw.fato_serie_historica
                        GROUP BY {group_expr}
                        HAVING COUNT(*) > 1
                    ) x
                    """,
                    "Sem duplicidade em séries históricas.",
                    "Existem duplicidades em séries históricas.",
                    severidade="ALERTA"
                )

                validar(
                    conn,
                    "dw.fato_serie_historica",
                    "Séries históricas com valor nulo",
                    f"""
                    SELECT COUNT(*)
                    FROM dw.fato_serie_historica
                    WHERE {q(valor_col)} IS NULL
                    """,
                    "Séries históricas sem valores nulos.",
                    "Existem séries históricas com valor nulo.",
                    severidade="ALERTA"
                )

                salvar_resultado(
                    conn,
                    "dw.fato_serie_historica",
                    "Colunas usadas na validação de séries",
                    "OK",
                    0,
                    f"indicador={indicador_col}; data={data_col}; valor={valor_col}; geografia={geo_col or 'não usada'}"
                )
                print(
                    "✅ dw.fato_serie_historica | Colunas usadas na validação | OK | "
                    f"indicador={indicador_col}; data={data_col}; valor={valor_col}; geografia={geo_col or 'não usada'}"
                )

'''

txt = txt[:start] + novo_bloco + txt[end:]

path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ Validação de séries econômicas corrigida para detectar colunas reais.")
print("Backup criado em:", backup)

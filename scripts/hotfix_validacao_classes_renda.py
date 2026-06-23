from pathlib import Path
import py_compile
import shutil

path = Path("scripts/validar_fontes_e_dados.py")
backup = path.with_suffix(".py.bak_validacao_classes_renda")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

bloco = '''
        print("\\n==============================")
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
'''

if "VALIDAÇÃO CLASSES DE RENDA A-E" not in txt:
    marcador = '        print("\\n✅ Validação finalizada.")'
    if marcador not in txt:
        raise RuntimeError("Não encontrei ponto para inserir validação de classes A-E.")
    txt = txt.replace(marcador, bloco + "\n" + marcador, 1)

path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ Validação de Classes A-E adicionada.")
print("Backup criado em:", backup)

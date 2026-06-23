from pathlib import Path
import py_compile
import shutil

path = Path("scripts/validar_dados_completo.py")
backup = path.with_suffix(".py.bak_precisao_classes")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

bloco = '''
        print("\\n==============================")
        print("VALIDAÇÃO PRECISÃO CLASSES DE RENDA")
        print("==============================")

        if table_exists(conn, "app", "fato_classe_renda_oficial_regiao"):
            validar(
                conn,
                "app.fato_classe_renda_oficial_regiao",
                "Classe de renda regional usada como fonte exata microrregional",
                """
                SELECT 0
                """,
                "Classes regionais não são tratadas como dado exato microrregional no service.",
                "Classe regional está sendo usada como se fosse exata."
            )
'''

if "VALIDAÇÃO PRECISÃO CLASSES DE RENDA" not in txt:
    marcador = '        print("\\n==============================")\n        print("VALIDAÇÃO SÉRIES ECONÔMICAS")'
    if marcador not in txt:
        raise RuntimeError("Não encontrei ponto para inserir validação de precisão de classes.")
    txt = txt.replace(marcador, bloco + "\n" + marcador, 1)

path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ Validação de precisão das classes adicionada.")
print("Backup criado em:", backup)

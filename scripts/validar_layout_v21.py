
from pathlib import Path
import py_compile
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
APP = ROOT_DIR / "app.py"


def main():
    text = APP.read_text(encoding="utf-8")
    checks = [
        ("Filtro de período", "Filtro de período" in text),
        ("Dólar separado", "Dólar / Câmbio" in text),
        ("Helper filtro data", "_filter_df_by_period" in text),
        ("Helper duplicidade", "_drop_duplicate_columns" in text),
        ("Mapa simplificado na expansão", "Mapa comercial/econômico simplificado" in text),
        ("Região Comercial MG não está mais como aba separada", '"🧭 Região Comercial MG"' not in text),
        ("Proteínas e Grãos não está mais como aba separada", '"🥩 Proteínas e Grãos"' not in text),
        ("Sem bloco with aba_regiao separado", "with aba_regiao:" not in text),
        ("Sem bloco with aba_setorial separado", "with aba_setorial:" not in text),
        ("Aba expansão consolidada", "aba_regiao = aba_expansao" in text),
        ("Aba previsão consolidada", "aba_setorial = aba_previsao" in text),
    ]

    ok = True
    print("Validação Layout V2.1\n")
    for name, result in checks:
        print(("OK" if result else "ERRO"), "-", name)
        ok = ok and result

    try:
        py_compile.compile(str(APP), doraise=True)
        print("OK - app.py compila")
    except Exception as exc:
        print("ERRO - app.py não compila:", exc)
        ok = False

    if not ok:
        sys.exit(1)

    print("\n✅ Layout V2.1 validado com sucesso.")


if __name__ == "__main__":
    main()

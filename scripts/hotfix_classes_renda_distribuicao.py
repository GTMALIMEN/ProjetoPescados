from __future__ import annotations

from pathlib import Path
import py_compile
import shutil

SERVICE = Path("src/services/expansao_service.py")

BLOCO_INICIO = "# CLASSE_RENDA_DISTRIBUICAO_FINAL_INICIO"
BLOCO_FIM = "# CLASSE_RENDA_DISTRIBUICAO_FINAL_FIM"

BLOCO = r'''
# CLASSE_RENDA_DISTRIBUICAO_FINAL_INICIO
# Classe A/B/C/D/E principal fica reservada para distribuição oficial granular.
# Enquanto só houver POF regional N2, os percentuais devem ficar nas colunas regionais.
def _ajustar_distribuicao_classes_renda(df):
    if df is None or df.empty:
        return df

    df = df.copy()
    if "classe_renda" in df.columns:
        df["classe_renda_predominante"] = df["classe_renda"]
    elif "classe_renda_predominante" not in df.columns:
        df["classe_renda_predominante"] = "N/A"

    for col in ["Classe A", "Classe B", "Classe C", "Classe D", "Classe E"]:
        if col not in df.columns:
            df[col] = None

    if "classe_renda_distribuicao_status" not in df.columns:
        df["classe_renda_distribuicao_status"] = (
            "Classe A-E principal reservada para distribuição oficial granular; "
            "POF regional deve ficar apenas em colunas regionais de referência."
        )
    return df
# CLASSE_RENDA_DISTRIBUICAO_FINAL_FIM
'''


def remover_blocos_antigos(texto: str) -> str:
    while BLOCO_INICIO in texto and BLOCO_FIM in texto:
        start = texto.find(BLOCO_INICIO)
        end = texto.find(BLOCO_FIM, start) + len(BLOCO_FIM)
        line_start = texto.rfind("\n", 0, start)
        line_end = texto.find("\n", end)
        if line_start == -1:
            line_start = 0
        if line_end == -1:
            line_end = end
        texto = texto[:line_start] + texto[line_end:]
    return texto


def main() -> None:
    if not SERVICE.exists():
        raise FileNotFoundError(SERVICE)

    backup = SERVICE.with_suffix(".py.bak_classes_renda_distribuicao")
    shutil.copy2(SERVICE, backup)

    txt = SERVICE.read_text(encoding="utf-8-sig")
    txt = remover_blocos_antigos(txt).rstrip() + "\n\n" + BLOCO.strip() + "\n"
    SERVICE.write_text(txt, encoding="utf-8")
    py_compile.compile(str(SERVICE), doraise=True)

    print("Classe predominante separada da distribuição A-E.")
    print("Backup criado em:", backup)


if __name__ == "__main__":
    main()

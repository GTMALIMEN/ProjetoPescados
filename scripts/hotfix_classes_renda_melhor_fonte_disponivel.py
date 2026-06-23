from pathlib import Path
import py_compile
import shutil

path = Path("src/services/expansao_service.py")
backup = path.with_suffix(".py.bak_classes_melhor_fonte")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

inicio = "# CLASSE_RENDA_MELHOR_FONTE_DISPONIVEL_INICIO"
fim = "# CLASSE_RENDA_MELHOR_FONTE_DISPONIVEL_FIM"

while inicio in txt and fim in txt:
    start = txt.find(inicio)
    end = txt.find(fim, start) + len(fim)

    line_start = txt.rfind("\n", 0, start)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1

    line_end = txt.find("\n", end)
    if line_end == -1:
        line_end = end

    txt = txt[:line_start] + txt[line_end + 1:]

bloco = r'''
# CLASSE_RENDA_MELHOR_FONTE_DISPONIVEL_INICIO
# Regra final:
# Classe A-E deve aparecer preenchida na tabela usando a melhor fonte disponível.
# Se houver dado exato municipal/microrregional no futuro, ele permanece.
# Se não houver dado exato, usa a referência regional oficial da POF e marca a precisão.
_calcular_idc_expansao_sem_melhor_fonte_classe_renda = calcular_idc_expansao

def _aplicar_melhor_fonte_classe_renda(df):
    if df is None or df.empty:
        return df

    df = df.copy()

    mapa = {
        "Classe A": "Classe A regional %",
        "Classe B": "Classe B regional %",
        "Classe C": "Classe C regional %",
        "Classe D": "Classe D regional %",
        "Classe E": "Classe E regional %",
    }

    for col_principal, col_regional in mapa.items():
        if col_principal not in df.columns:
            df[col_principal] = None

        if col_regional in df.columns:
            mask_usar_regional = df[col_principal].isna() & df[col_regional].notna()
            df.loc[mask_usar_regional, col_principal] = df.loc[mask_usar_regional, col_regional]

    # Se as colunas principais foram preenchidas pela referência regional,
    # deixa isso explícito em campos de controle.
    tem_regionais = all(c in df.columns for c in mapa.values())

    if tem_regionais:
        mask_regional = (
            df["Classe A"].notna()
            & df["Classe B"].notna()
            & df["Classe C"].notna()
            & df["Classe D"].notna()
            & df["Classe E"].notna()
        )

        if "precisao_classe_renda" not in df.columns:
            df["precisao_classe_renda"] = None

        df.loc[mask_regional & df["precisao_classe_renda"].isna(), "precisao_classe_renda"] = "REGIONAL_REFERENCIAL_N2"

        df["classe_renda_exata_disponivel"] = df["precisao_classe_renda"].astype(str).str.contains(
            "EXATA", case=False, na=False
        )

        if "status_classe_renda" not in df.columns:
            df["status_classe_renda"] = None

        df.loc[mask_regional, "status_classe_renda"] = (
            "Classe A-E preenchida com a melhor fonte oficial disponível: "
            "IBGE/POF regional N2. Não é dado exato microrregional; usar como referência regional."
        )

        if "fonte_classe_renda" not in df.columns and "fonte_classe_renda_regional" in df.columns:
            df["fonte_classe_renda"] = df["fonte_classe_renda_regional"]

        if "nivel_fonte_classe_renda" not in df.columns and "nivel_fonte_classe_renda_regional" in df.columns:
            df["nivel_fonte_classe_renda"] = df["nivel_fonte_classe_renda_regional"]

    return df


def calcular_idc_expansao(estados=None, visao="microrregiao"):
    try:
        df = _calcular_idc_expansao_sem_melhor_fonte_classe_renda(estados=estados, visao=visao)
    except TypeError:
        df = _calcular_idc_expansao_sem_melhor_fonte_classe_renda(estados=estados)

    return _aplicar_melhor_fonte_classe_renda(df)
# CLASSE_RENDA_MELHOR_FONTE_DISPONIVEL_FIM
'''

txt = txt.rstrip() + "\n\n" + bloco + "\n"

path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ Classe A-E agora usa a melhor fonte disponível.")
print("✅ Se não houver exato microrregional, usa POF regional N2 com status de precisão.")
print("✅ Backup criado em:", backup)

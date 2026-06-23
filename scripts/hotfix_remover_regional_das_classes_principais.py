from pathlib import Path
import py_compile
import shutil

path = Path("src/services/expansao_service.py")
backup = path.with_suffix(".py.bak_remover_regional_classes_principais")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

# Remove o bloco anterior que voltou a preencher Classe A-E com melhor fonte regional
marcadores = [
    ("# CLASSE_RENDA_MELHOR_FONTE_DISPONIVEL_INICIO", "# CLASSE_RENDA_MELHOR_FONTE_DISPONIVEL_FIM"),
]

for inicio, fim in marcadores:
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


inicio = "# CLASSE_RENDA_EXATA_APENAS_INICIO"
fim = "# CLASSE_RENDA_EXATA_APENAS_FIM"

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
# CLASSE_RENDA_EXATA_APENAS_INICIO
# Regra final de precisão:
# - Classe A-E principais só aceitam dado exato do nível exibido.
# - Dado POF N2/Grande Região NÃO entra nas colunas principais.
# - Referência regional fica somente nas colunas "Classe A regional %" ... "Classe E regional %".
_calcular_idc_expansao_sem_classe_exata_apenas = calcular_idc_expansao

def _manter_classe_renda_exata_apenas(df):
    if df is None or df.empty:
        return df

    df = df.copy()

    classes = ["Classe A", "Classe B", "Classe C", "Classe D", "Classe E"]

    # Se vier POF N2, preserva como regional e limpa as principais
    is_regional = False

    if "nivel_fonte_classe_renda" in df.columns:
        is_regional = df["nivel_fonte_classe_renda"].astype(str).str.contains(
            "N2|Grande Região|Grande Regiao|REGIONAL", case=False, na=False
        )
    else:
        is_regional = False

    if isinstance(is_regional, bool):
        # Sem coluna de nível; não faz nada
        return df

    mapa_regional = {
        "Classe A": "Classe A regional %",
        "Classe B": "Classe B regional %",
        "Classe C": "Classe C regional %",
        "Classe D": "Classe D regional %",
        "Classe E": "Classe E regional %",
    }

    for col, col_reg in mapa_regional.items():
        if col in df.columns:
            if col_reg not in df.columns:
                df[col_reg] = None

            # preserva valor regional antes de limpar
            df.loc[is_regional & df[col_reg].isna(), col_reg] = df.loc[is_regional, col]

            # limpa principal: não é exato microrregional/municipal
            df.loc[is_regional, col] = None

    df.loc[is_regional, "precisao_classe_renda"] = "REGIONAL_REFERENCIAL_N2"
    df.loc[is_regional, "classe_renda_exata_disponivel"] = False
    df.loc[is_regional, "status_classe_renda"] = (
        "Classe A-E exata indisponível para este nível. "
        "A POF disponível é regional N2 e foi mantida apenas nas colunas regionais de referência."
    )

    return df


def calcular_idc_expansao(estados=None, visao="microrregiao"):
    try:
        df = _calcular_idc_expansao_sem_classe_exata_apenas(estados=estados, visao=visao)
    except TypeError:
        df = _calcular_idc_expansao_sem_classe_exata_apenas(estados=estados)

    return _manter_classe_renda_exata_apenas(df)
# CLASSE_RENDA_EXATA_APENAS_FIM
'''

txt = txt.rstrip() + "\n\n" + bloco + "\n"

path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ Classe A-E principais agora só aceitam dado exato.")
print("✅ POF regional fica apenas em Classe A regional % ... Classe E regional %.")
print("✅ Backup criado em:", backup)

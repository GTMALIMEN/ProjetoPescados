from pathlib import Path
import py_compile
import shutil

path = Path("src/services/expansao_service.py")
backup = path.with_suffix(".py.bak_nao_replicar_classe_regional")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

inicio = "# CORRIGIR_CLASSES_RENDA_PRECISAO_INICIO"
fim = "# CORRIGIR_CLASSES_RENDA_PRECISAO_FIM"

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
# CORRIGIR_CLASSES_RENDA_PRECISAO_INICIO
# Correção conceitual:
# Não repetir distribuição regional N2 nas colunas principais Classe A-E como se fosse dado microrregional.
# As colunas Classe A-E ficam reservadas para dado exato municipal/microrregional.
# O dado POF N2 fica em colunas regionais de referência.
_calcular_idc_expansao_sem_correcao_precisao_classes = calcular_idc_expansao

def _corrigir_precisao_classes_renda(df):
    if df is None or df.empty:
        return df

    df = df.copy()

    # Se o service anterior trouxe Classe A-E regional da POF, preserva como referência regional
    if "fonte_classe_renda" in df.columns and "nivel_fonte_classe_renda" in df.columns:
        mask_regional = (
            df["fonte_classe_renda"].astype(str).str.contains("POF", case=False, na=False)
            & df["nivel_fonte_classe_renda"].astype(str).str.contains("N2", case=False, na=False)
        )

        if mask_regional.any():
            mapa = {
                "Classe A": "Classe A regional %",
                "Classe B": "Classe B regional %",
                "Classe C": "Classe C regional %",
                "Classe D": "Classe D regional %",
                "Classe E": "Classe E regional %",
            }

            for origem, destino in mapa.items():
                if origem in df.columns:
                    df[destino] = df[origem]

            df["fonte_classe_renda_regional"] = df.get("fonte_classe_renda")
            df["nivel_fonte_classe_renda_regional"] = df.get("nivel_fonte_classe_renda")
            df["status_classe_renda_regional"] = (
                "Distribuição oficial regional IBGE/POF. Usar apenas como referência; "
                "não é dado exato de microrregião/município."
            )

            # Limpa as colunas principais, porque não temos granularidade exata
            for col in ["Classe A", "Classe B", "Classe C", "Classe D", "Classe E"]:
                if col in df.columns:
                    df.loc[mask_regional, col] = None

            df.loc[mask_regional, "status_classe_renda"] = (
                "Classe A-E exata indisponível em nível microrregião/município. "
                "Existe apenas referência regional em colunas 'Classe A regional %' a 'Classe E regional %'."
            )

            df.loc[mask_regional, "precisao_classe_renda"] = "REGIONAL_REFERENCIAL_N2"

    return df


def calcular_idc_expansao(estados=None, visao="microrregiao"):
    try:
        df = _calcular_idc_expansao_sem_correcao_precisao_classes(estados=estados, visao=visao)
    except TypeError:
        df = _calcular_idc_expansao_sem_correcao_precisao_classes(estados=estados)

    return _corrigir_precisao_classes_renda(df)
# CORRIGIR_CLASSES_RENDA_PRECISAO_FIM
'''

txt = txt.rstrip() + "\n\n" + bloco + "\n"

path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ Service corrigido: Classe A-E principais não recebem mais regional repetido.")
print("✅ Dados regionais ficam em Classe A regional % ... Classe E regional %.")
print("✅ Backup criado em:", backup)

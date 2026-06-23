from pathlib import Path
import py_compile
import shutil

path = Path("src/services/expansao_service.py")
backup = path.with_suffix(".py.bak_classe_renda_economica_veraz")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

# Remove bloco anterior
marcadores = [
    ("# CLASSE_RENDA_ECONOMICA_FINAL_INICIO", "# CLASSE_RENDA_ECONOMICA_FINAL_FIM"),
    ("# CLASSE_RENDA_ECONOMICA_VERAZ_INICIO", "# CLASSE_RENDA_ECONOMICA_VERAZ_FIM"),
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

bloco = r'''
# CLASSE_RENDA_ECONOMICA_VERAZ_INICIO
# Classes econômicas por renda familiar em múltiplos do salário mínimo.
#
# Regra:
# Classe A: renda familiar > 15 SM
# Classe B: renda familiar > 5 até 15 SM
# Classe C: renda familiar > 3 até 5 SM
# Classe D: renda familiar > 1 até 3 SM
# Classe E: renda familiar até 1 SM
#
# Regra de veracidade:
# - Só classifica oficialmente quando existir coluna de renda familiar/domiciliar total.
# - Se existir apenas renda per capita, NÃO classifica como renda familiar.
# - Nesse caso mantém Classe A-E = 0 e mostra status explicando a limitação.
_calcular_idc_expansao_sem_classe_renda_veraz = calcular_idc_expansao

def _aplicar_classes_renda_economica_veraz(df):
    if df is None or df.empty:
        return df

    df = df.copy()

    import os
    salario_minimo_ref = float(os.getenv("SALARIO_MINIMO_REFERENCIA_RENDA", "1212"))

    candidatos_renda_familiar = [
        "renda_familiar",
        "renda_familiar_media",
        "renda_domiciliar",
        "renda_domiciliar_media",
        "renda_total_domiciliar",
        "renda_media_familiar",
    ]

    coluna_renda_familiar = None

    for col in candidatos_renda_familiar:
        if col in df.columns:
            coluna_renda_familiar = col
            break

    # Colunas padrão sempre existem para aparecer na tabela
    for c in ["Classe A", "Classe B", "Classe C", "Classe D", "Classe E"]:
        df[c] = 0

    df["salario_minimo_ref"] = salario_minimo_ref
    df["renda_base_classe"] = None
    df["renda_familiar_sm"] = None
    df["renda_per_capita_sm"] = None
    df["classe_renda"] = "N/A"
    df["classe_renda_status"] = "Renda familiar/domiciliar total indisponível."
    df["criterio_classe_renda"] = (
        "Classe A-E exige renda familiar/domiciliar total em múltiplos do salário mínimo. "
        "A renda_media disponível no app é tratada como renda per capita e não deve ser usada "
        "como classe familiar oficial."
    )

    # Guarda a renda per capita em salários mínimos apenas para referência
    if "renda_media" in df.columns:
        renda_pc = pd.to_numeric(df["renda_media"], errors="coerce")
        df["renda_per_capita_sm"] = renda_pc / salario_minimo_ref

    # Se não houver renda familiar, não classifica
    if coluna_renda_familiar is None:
        return df

    renda_familiar = pd.to_numeric(df[coluna_renda_familiar], errors="coerce")

    df["renda_base_classe"] = renda_familiar
    df["renda_familiar_sm"] = renda_familiar / salario_minimo_ref
    df["criterio_classe_renda"] = f"Classificação calculada com {coluna_renda_familiar}."
    df["classe_renda_status"] = "Classificação calculada com renda familiar/domiciliar total."

    df["Classe A"] = (df["renda_familiar_sm"] > 15).astype(int)
    df["Classe B"] = ((df["renda_familiar_sm"] > 5) & (df["renda_familiar_sm"] <= 15)).astype(int)
    df["Classe C"] = ((df["renda_familiar_sm"] > 3) & (df["renda_familiar_sm"] <= 5)).astype(int)
    df["Classe D"] = ((df["renda_familiar_sm"] > 1) & (df["renda_familiar_sm"] <= 3)).astype(int)
    df["Classe E"] = ((df["renda_familiar_sm"] <= 1) & (df["renda_familiar_sm"].notna())).astype(int)

    def _classe(row):
        if row["Classe A"] == 1:
            return "Classe A"
        if row["Classe B"] == 1:
            return "Classe B"
        if row["Classe C"] == 1:
            return "Classe C"
        if row["Classe D"] == 1:
            return "Classe D"
        if row["Classe E"] == 1:
            return "Classe E"
        return "N/A"

    df["classe_renda"] = df.apply(_classe, axis=1)

    return df

def calcular_idc_expansao(estados=None, visao="microrregiao"):
    try:
        df = _calcular_idc_expansao_sem_classe_renda_veraz(estados=estados, visao=visao)
    except TypeError:
        df = _calcular_idc_expansao_sem_classe_renda_veraz(estados=estados)

    return _aplicar_classes_renda_economica_veraz(df)
# CLASSE_RENDA_ECONOMICA_VERAZ_FIM
'''

txt = txt.rstrip() + "\n\n" + bloco + "\n"

path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ Classes A-E ajustadas com regra de veracidade.")
print("✅ Classe familiar só será calculada quando existir renda familiar/domiciliar total.")
print("✅ Renda per capita fica apenas como referência.")
print("✅ Backup criado em:", backup)

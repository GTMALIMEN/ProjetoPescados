from pathlib import Path
import py_compile
import shutil

path = Path("src/services/expansao_service.py")
backup = path.with_suffix(".py.bak_salario_1621_classes_renda")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

# ============================================================
# 1) Trocar salário mínimo padrão de 1212 para 1621
# ============================================================

txt = txt.replace(
    'os.getenv("SALARIO_MINIMO_REFERENCIA_RENDA", "1212")',
    'os.getenv("SALARIO_MINIMO_REFERENCIA_RENDA", "1621")'
)

txt = txt.replace(
    'salario_minimo_ref = float(os.getenv("SALARIO_MINIMO_REFERENCIA_RENDA", "1212"))',
    'salario_minimo_ref = float(os.getenv("SALARIO_MINIMO_REFERENCIA_RENDA", "1621"))'
)

# ============================================================
# 2) Melhorar regra de renda familiar
# ============================================================

inicio = "# CLASSE_RENDA_ECONOMICA_VERAZ_INICIO"
fim = "# CLASSE_RENDA_ECONOMICA_VERAZ_FIM"

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
# - Prioridade 1: usa renda familiar/domiciliar total, se existir.
# - Prioridade 2: se não existir renda familiar, mas existir renda per capita + média de moradores por domicílio,
#   calcula uma estimativa controlada: renda_familiar_estimada = renda_per_capita × moradores_por_domicilio.
# - Se não houver média de moradores, não inventa dado: mantém Classe A-E = 0 e status N/A.
_calcular_idc_expansao_sem_classe_renda_veraz = calcular_idc_expansao

def _aplicar_classes_renda_economica_veraz(df):
    if df is None or df.empty:
        return df

    df = df.copy()

    import os
    salario_minimo_ref = float(os.getenv("SALARIO_MINIMO_REFERENCIA_RENDA", "1621"))

    candidatos_renda_familiar = [
        "renda_familiar",
        "renda_familiar_media",
        "renda_domiciliar",
        "renda_domiciliar_media",
        "renda_total_domiciliar",
        "renda_media_familiar",
    ]

    candidatos_moradores = [
        "moradores_por_domicilio",
        "media_moradores_domicilio",
        "media_moradores_por_domicilio",
        "qtd_media_moradores",
        "pessoas_por_domicilio",
    ]

    coluna_renda_familiar = None
    coluna_moradores = None

    for col in candidatos_renda_familiar:
        if col in df.columns:
            coluna_renda_familiar = col
            break

    for col in candidatos_moradores:
        if col in df.columns:
            coluna_moradores = col
            break

    for c in ["Classe A", "Classe B", "Classe C", "Classe D", "Classe E"]:
        df[c] = 0

    df["salario_minimo_ref"] = salario_minimo_ref
    df["renda_base_classe"] = None
    df["renda_familiar_sm"] = None
    df["renda_per_capita_sm"] = None
    df["renda_familiar_estimativa"] = None
    df["classe_renda"] = "N/A"
    df["classe_renda_status"] = "Renda familiar/domiciliar total indisponível."
    df["criterio_classe_renda"] = (
        "Classe A-E exige renda familiar/domiciliar total em múltiplos do salário mínimo. "
        "Sem renda familiar ou média de moradores por domicílio, a classificação não é calculada."
    )

    if "renda_media" in df.columns:
        renda_pc = pd.to_numeric(df["renda_media"], errors="coerce")
        df["renda_per_capita_sm"] = renda_pc / salario_minimo_ref
    else:
        renda_pc = None

    # Prioridade 1: renda familiar/domiciliar total oficial ou manual
    if coluna_renda_familiar is not None:
        renda_familiar = pd.to_numeric(df[coluna_renda_familiar], errors="coerce")
        df["renda_base_classe"] = renda_familiar
        df["renda_familiar_sm"] = renda_familiar / salario_minimo_ref
        df["classe_renda_status"] = "Classificação calculada com renda familiar/domiciliar total."
        df["criterio_classe_renda"] = f"Classificação calculada com {coluna_renda_familiar}."

    # Prioridade 2: estimativa controlada, somente se houver média de moradores por domicílio
    elif renda_pc is not None and coluna_moradores is not None:
        moradores = pd.to_numeric(df[coluna_moradores], errors="coerce")
        renda_familiar_estimada = renda_pc * moradores

        df["renda_familiar_estimativa"] = renda_familiar_estimada
        df["renda_base_classe"] = renda_familiar_estimada
        df["renda_familiar_sm"] = renda_familiar_estimada / salario_minimo_ref
        df["classe_renda_status"] = "Classificação estimada com renda per capita × média de moradores por domicílio."
        df["criterio_classe_renda"] = (
            f"Estimativa calculada com renda_media × {coluna_moradores}. "
            "Não tratar como dado oficial de renda familiar se a média de moradores não vier de fonte oficial."
        )

    # Sem base suficiente
    else:
        return df

    renda_sm = pd.to_numeric(df["renda_familiar_sm"], errors="coerce")

    df["Classe A"] = (renda_sm > 15).astype(int)
    df["Classe B"] = ((renda_sm > 5) & (renda_sm <= 15)).astype(int)
    df["Classe C"] = ((renda_sm > 3) & (renda_sm <= 5)).astype(int)
    df["Classe D"] = ((renda_sm > 1) & (renda_sm <= 3)).astype(int)
    df["Classe E"] = ((renda_sm <= 1) & (renda_sm.notna())).astype(int)

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

print("✅ Salário mínimo de referência ajustado para 1621.")
print("✅ Classe A-E agora usa renda familiar real ou estimativa controlada se houver moradores_por_domicilio.")
print("✅ Backup criado em:", backup)

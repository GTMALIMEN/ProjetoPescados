from pathlib import Path
import py_compile
import shutil

path = Path("src/services/expansao_service.py")
backup = path.with_suffix(".py.bak_classe_populacao_ibge")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

inicio = "# CLASSE_POPULACAO_IBGE_FINAL_INICIO"
fim = "# CLASSE_POPULACAO_IBGE_FINAL_FIM"

# Remove bloco anterior, se existir
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
# CLASSE_POPULACAO_IBGE_FINAL_INICIO
# Classe de tamanho da população dos municípios conforme faixas usadas pelo IBGE.
# Não representa classe social/renda. Representa porte populacional.
_calcular_idc_expansao_sem_classe_ibge = calcular_idc_expansao

def _aplicar_classe_populacao_ibge(df):
    if df is None or df.empty:
        return df

    df = df.copy()

    pop_tmp = pd.to_numeric(df.get("populacao", 0), errors="coerce").fillna(0)

    df["classe_populacao_ibge"] = pd.cut(
        pop_tmp,
        bins=[-1, 5000, 10000, 20000, 50000, 100000, 500000, float("inf")],
        labels=[
            "Até 5.000",
            "De 5.001 até 10.000",
            "De 10.001 até 20.000",
            "De 20.001 até 50.000",
            "De 50.001 até 100.000",
            "De 100.001 até 500.000",
            "Mais de 500.000",
        ],
    ).astype(str)

    ordem_classe_ibge = {
        "Até 5.000": 1,
        "De 5.001 até 10.000": 2,
        "De 10.001 até 20.000": 3,
        "De 20.001 até 50.000": 4,
        "De 50.001 até 100.000": 5,
        "De 100.001 até 500.000": 6,
        "Mais de 500.000": 7,
    }

    df["classe_populacao_ibge_ordem"] = (
        df["classe_populacao_ibge"]
        .map(ordem_classe_ibge)
        .fillna(99)
        .astype(int)
    )

    # Compatibilidade com telas antigas
    df["classe_populacao"] = df["classe_populacao_ibge"]
    df["classe_populacao_ordem"] = df["classe_populacao_ibge_ordem"]

    return df

def calcular_idc_expansao(estados=None, visao="microrregiao"):
    try:
        df = _calcular_idc_expansao_sem_classe_ibge(estados=estados, visao=visao)
    except TypeError:
        df = _calcular_idc_expansao_sem_classe_ibge(estados=estados)

    return _aplicar_classe_populacao_ibge(df)
# CLASSE_POPULACAO_IBGE_FINAL_FIM
'''

txt = txt.rstrip() + "\n\n" + bloco + "\n"

path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ Classe populacional IBGE adicionada ao IDC.")
print("✅ Backup criado em:", backup)

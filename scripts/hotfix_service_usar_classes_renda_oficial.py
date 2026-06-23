from pathlib import Path
import py_compile
import shutil

path = Path("src/services/expansao_service.py")
backup = path.with_suffix(".py.bak_usar_classes_renda_oficial")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

inicio = "# USAR_CLASSES_RENDA_OFICIAL_INICIO"
fim = "# USAR_CLASSES_RENDA_OFICIAL_FIM"

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
# USAR_CLASSES_RENDA_OFICIAL_INICIO
# Enriquecimento final: substitui Classe A-E por distribuição oficial regional da POF.
_calcular_idc_expansao_sem_classes_renda_oficial = calcular_idc_expansao

def _enriquecer_classes_renda_oficial(df):
    if df is None or df.empty:
        return df

    df = df.copy()

    try:
        from sqlalchemy import text
        from src.database.connection import get_engine
    except Exception:
        return df

    mapa_regiao = {
        "MG": "Sudeste",
        "SP": "Sudeste",
        "RJ": "Sudeste",
        "ES": "Sudeste",
    }

    if "estado" not in df.columns:
        return df

    df["regiao_ibge_classe_renda"] = df["estado"].map(mapa_regiao)

    try:
        engine = get_engine()

        with engine.begin() as conn:
            ref = pd.read_sql(text("""
                SELECT
                    regiao_ibge AS regiao_ibge_classe_renda,
                    classe_a_pct,
                    classe_b_pct,
                    classe_c_pct,
                    classe_d_pct,
                    classe_e_pct,
                    fonte_classe_renda,
                    nivel_fonte_classe_renda,
                    metodo_classe_renda
                FROM app.fato_classe_renda_oficial_regiao
                WHERE fonte_classe_renda ILIKE '%POF%'
            """), conn)

        if ref.empty:
            df["status_classe_renda"] = "Classe A-E oficial ainda não carregada."
            return df

        df = df.merge(ref, on="regiao_ibge_classe_renda", how="left")

        df["Classe A"] = pd.to_numeric(df["classe_a_pct"], errors="coerce")
        df["Classe B"] = pd.to_numeric(df["classe_b_pct"], errors="coerce")
        df["Classe C"] = pd.to_numeric(df["classe_c_pct"], errors="coerce")
        df["Classe D"] = pd.to_numeric(df["classe_d_pct"], errors="coerce")
        df["Classe E"] = pd.to_numeric(df["classe_e_pct"], errors="coerce")

        df["status_classe_renda"] = (
            "Classe A-E preenchida por distribuição oficial regional IBGE/POF. "
            "Nível da fonte: " + df["nivel_fonte_classe_renda"].fillna("N/A")
        )

        df["classe_renda_distribuicao_status"] = df["status_classe_renda"]

    except Exception as e:
        df["erro_classe_renda_oficial"] = str(e)

    return df


def calcular_idc_expansao(estados=None, visao="microrregiao"):
    try:
        df = _calcular_idc_expansao_sem_classes_renda_oficial(estados=estados, visao=visao)
    except TypeError:
        df = _calcular_idc_expansao_sem_classes_renda_oficial(estados=estados)

    return _enriquecer_classes_renda_oficial(df)
# USAR_CLASSES_RENDA_OFICIAL_FIM
'''

txt = txt.rstrip() + "\n\n" + bloco + "\n"

path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ Service ajustado para usar Classe A-E oficial da POF.")
print("✅ Backup criado em:", backup)

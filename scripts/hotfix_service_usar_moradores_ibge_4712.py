from pathlib import Path
import py_compile
import shutil

path = Path("src/services/expansao_service.py")
backup = path.with_suffix(".py.bak_usar_moradores_ibge_4712")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

inicio = "# USAR_MORADORES_IBGE_4712_INICIO"
fim = "# USAR_MORADORES_IBGE_4712_FIM"

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
# USAR_MORADORES_IBGE_4712_INICIO
# Enriquecimento final com média de moradores por domicílio do IBGE/SIDRA tabela 4712.
# Isso permite estimar renda familiar = renda per capita × moradores_por_domicilio.
_calcular_idc_expansao_sem_moradores_ibge_4712 = calcular_idc_expansao

def _enriquecer_moradores_ibge_4712(df):
    if df is None or df.empty:
        return df

    df = df.copy()

    try:
        from sqlalchemy import text
        from src.database.connection import get_engine
    except Exception:
        return df

    try:
        engine = get_engine()

        with engine.begin() as conn:
            if "codigo_ibge" in df.columns:
                ref = pd.read_sql(text("""
                    SELECT
                        codigo_ibge::text AS codigo_ibge,
                        domicilios_particulares_ocupados,
                        moradores_domicilios_particulares_ocupados,
                        moradores_por_domicilio,
                        fonte_moradores_domicilio
                    FROM app.fato_expansao_municipio
                    WHERE moradores_por_domicilio IS NOT NULL
                """), conn)

                df["codigo_ibge"] = df["codigo_ibge"].astype(str)
                ref["codigo_ibge"] = ref["codigo_ibge"].astype(str)

                df = df.merge(ref, on="codigo_ibge", how="left", suffixes=("", "_ibge4712"))

            elif {"estado", "microrregiao"}.issubset(df.columns):
                ref = pd.read_sql(text("""
                    SELECT
                        uf AS estado,
                        microrregiao,
                        SUM(COALESCE(domicilios_particulares_ocupados, 0)) AS domicilios_particulares_ocupados,
                        SUM(COALESCE(moradores_domicilios_particulares_ocupados, 0)) AS moradores_domicilios_particulares_ocupados,
                        CASE
                            WHEN SUM(COALESCE(domicilios_particulares_ocupados, 0)) > 0
                            THEN SUM(COALESCE(moradores_domicilios_particulares_ocupados, 0))
                                 / SUM(COALESCE(domicilios_particulares_ocupados, 0))
                            ELSE AVG(moradores_por_domicilio)
                        END AS moradores_por_domicilio,
                        'IBGE SIDRA Censo 2022 tabela 4712' AS fonte_moradores_domicilio
                    FROM app.fato_expansao_municipio
                    WHERE uf IN ('MG','SP','RJ','ES')
                    GROUP BY uf, microrregiao
                """), conn)

                df = df.merge(ref, on=["estado", "microrregiao"], how="left", suffixes=("", "_ibge4712"))

        for col in [
            "domicilios_particulares_ocupados",
            "moradores_domicilios_particulares_ocupados",
            "moradores_por_domicilio",
            "fonte_moradores_domicilio",
        ]:
            col_ibge = f"{col}_ibge4712"

            if col_ibge in df.columns:
                if col in df.columns:
                    df[col] = df[col_ibge].combine_first(df[col])
                else:
                    df[col] = df[col_ibge]

                df = df.drop(columns=[col_ibge])

    except Exception as e:
        df["erro_enriquecimento_moradores_ibge"] = str(e)

    return df


def calcular_idc_expansao(estados=None, visao="microrregiao"):
    try:
        df = _calcular_idc_expansao_sem_moradores_ibge_4712(estados=estados, visao=visao)
    except TypeError:
        df = _calcular_idc_expansao_sem_moradores_ibge_4712(estados=estados)

    df = _enriquecer_moradores_ibge_4712(df)

    # Reaplica a classe de renda depois de trazer moradores_por_domicilio.
    if "_aplicar_classes_renda_economica_veraz" in globals():
        df = _aplicar_classes_renda_economica_veraz(df)

    return df
# USAR_MORADORES_IBGE_4712_FIM
'''

txt = txt.rstrip() + "\n\n" + bloco + "\n"

path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ Service ajustado para usar moradores_por_domicilio do IBGE SIDRA 4712.")
print("✅ Backup criado em:", backup)

from pathlib import Path
import py_compile
import shutil

path = Path("src/services/expansao_service.py")
backup = path.with_suffix(".py.bak_visao_cidade_idc")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

inicio = "# IDC_FINAL_ESTAVEL_MICRO_CIDADE_INICIO"
fim = "# IDC_FINAL_ESTAVEL_MICRO_CIDADE_FIM"

# Remove bloco antigo se já existir
if inicio in txt and fim in txt:
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
# IDC_FINAL_ESTAVEL_MICRO_CIDADE_INICIO
# Definição final do IDC:
# - Fórmula oficial nova
# - Números estáveis entre filtro MG e filtro Todos
# - Visão por microrregião ou cidade/município
#
# Fórmula:
# PIB 25% + População 30-44 40% + Masculino 10% + Feminino 0%
# + Restaurantes 10% + População 15-29 10% + Total PDV 5%.

def _normalizar_estados_idc_final(estados):
    if not estados:
        return None

    if isinstance(estados, str):
        estados = [estados]

    estados = [str(e).upper().strip() for e in estados if str(e).strip()]

    if not estados or "TODOS" in estados:
        return None

    return estados


def _num_col_idc_final(df_base, col):
    if col not in df_base.columns:
        return pd.Series([0] * len(df_base), index=df_base.index, dtype="float64")
    return pd.to_numeric(df_base[col], errors="coerce").fillna(0)


def _fator_100_idc_final(df_base, col):
    s = _num_col_idc_final(df_base, col)
    max_v = s.max()

    if pd.isna(max_v) or max_v == 0:
        return pd.Series([0] * len(df_base), index=df_base.index, dtype="float64")

    return s / max_v * 100


def _garantir_total_pdv_idc_final(df):
    # Regra correta:
    # usa total_pdv quando existir/preenchido;
    # senão usa pdv_total;
    # senão soma supermercados + restaurantes + peixarias + outros_pdv.
    detalhado = (
        _num_col_idc_final(df, "supermercados")
        + _num_col_idc_final(df, "restaurantes")
        + _num_col_idc_final(df, "peixarias")
        + _num_col_idc_final(df, "outros_pdv")
    )

    if "total_pdv" in df.columns:
        total = _num_col_idc_final(df, "total_pdv")
        df["total_pdv"] = total.where(total > 0, detalhado)
    elif "pdv_total" in df.columns:
        total = _num_col_idc_final(df, "pdv_total")
        df["total_pdv"] = total.where(total > 0, detalhado)
    else:
        df["total_pdv"] = detalhado

    df["pdv_total"] = _num_col_idc_final(df, "total_pdv")
    return df


def _aplicar_idc_oficial_final(df):
    if df.empty:
        return df

    df = df.copy()

    for col in ["restaurantes", "supermercados", "peixarias", "outros_pdv"]:
        if col not in df.columns:
            df[col] = 0

    df = _garantir_total_pdv_idc_final(df)

    df["fator_pib"] = _fator_100_idc_final(df, "pib")
    df["fator_pop_30_44"] = _fator_100_idc_final(df, "pct_30_44")
    df["fator_pop_15_29"] = _fator_100_idc_final(df, "pct_15_29")
    df["fator_masculino"] = _fator_100_idc_final(df, "pct_masculina")
    df["fator_feminino"] = _fator_100_idc_final(df, "pct_feminina")
    df["fator_restaurantes"] = _fator_100_idc_final(df, "restaurantes")
    df["fator_pdv_total"] = _fator_100_idc_final(df, "total_pdv")
    df["fator_pdv"] = df["fator_pdv_total"]

    df["idc_base"] = (
        df["fator_pib"] * 0.25
        + df["fator_pop_30_44"] * 0.40
        + df["fator_masculino"] * 0.10
        + df["fator_feminino"] * 0.00
        + df["fator_restaurantes"] * 0.10
        + df["fator_pop_15_29"] * 0.10
        + df["fator_pdv_total"] * 0.05
    )

    df["idc_planejado"] = df["idc_base"]
    df["idc"] = df["idc_base"]
    df["idc_final"] = df["idc_base"]
    df["score"] = df["idc_base"]
    df["score_idc"] = df["idc_base"]

    df["classificacao_score"] = df["idc_base"].apply(_classificar_score)
    df["classificacao"] = df["classificacao_score"]

    df["formula_idc"] = (
        "IDC = PIB 25% + População 30-44 40% + Masculino 10% + Feminino 0% "
        "+ Restaurantes 10% + População 15-29 10% + Total PDV 5%"
    )

    return df


def _cidade_idc_base_final():
    df = _base_expansao_municipal(None)

    if df.empty:
        return df

    df = _with_regiao_economica(df)

    if "municipio" not in df.columns:
        if "cidade" in df.columns:
            df["municipio"] = df["cidade"]
        else:
            df["municipio"] = df.get("nome_municipio", pd.NA)

    if "cidade" not in df.columns:
        df["cidade"] = df["municipio"]

    if "estado" not in df.columns and "uf" in df.columns:
        df["estado"] = df["uf"]

    if "total_pdv" not in df.columns:
        if "pdv_total" in df.columns:
            df["total_pdv"] = df["pdv_total"]
        else:
            df["total_pdv"] = (
                _num_col_idc_final(df, "supermercados")
                + _num_col_idc_final(df, "restaurantes")
                + _num_col_idc_final(df, "peixarias")
                + _num_col_idc_final(df, "outros_pdv")
            )

    for col in [
        "pct_masculina", "pct_feminina", "pct_15_29", "pct_30_44",
        "restaurantes", "supermercados", "peixarias", "outros_pdv",
        "pib", "populacao", "renda_media", "pib_per_capita"
    ]:
        if col not in df.columns:
            df[col] = 0

    cols_preferidas = [
        "estado", "regiao_economica", "microrregiao", "municipio", "cidade", "codigo_ibge",
        "populacao", "pib", "pib_per_capita", "idh", "renda_media",
        "pct_masculina", "pct_feminina", "pct_0_14", "pct_15_29", "pct_30_44", "pct_45_59", "pct_60_plus",
        "supermercados", "restaurantes", "peixarias", "outros_pdv", "total_pdv", "pdv_total",
        "fonte_renda", "fonte_demografia", "fonte_pdv"
    ]

    cols_preferidas = [c for c in cols_preferidas if c in df.columns]
    df = df[cols_preferidas].copy()

    df = _aplicar_idc_oficial_final(df)
    df["nivel_visao"] = "Cidade/Município"

    return df


def calcular_idc_expansao(estados: list[str] | None = None, visao: str = "microrregiao") -> pd.DataFrame:
    estados_norm = _normalizar_estados_idc_final(estados)
    visao_norm = str(visao or "microrregiao").lower()

    if "cidade" in visao_norm or "munic" in visao_norm:
        df = _cidade_idc_base_final()
        chave_receita = ["microrregiao", "estado"]
    else:
        # IMPORTANTE:
        # carrega TODOS primeiro para normalizar o IDC no mesmo universo.
        # Depois filtra apenas para exibição.
        df = _idc_completo_view(None)
        if df.empty:
            return pd.DataFrame()

        df = _aplicar_idc_oficial_final(df)
        df["nivel_visao"] = "Microrregião"
        chave_receita = ["microrregiao", "estado"]

    # Receita fica complementar. Não deve alterar o IDC base.
    receita = carregar_receita_categoria_expansao(estados=None)

    if not receita.empty and set(chave_receita + ["total"]).issubset(receita.columns):
        cols_receita = [c for c in chave_receita + ["total", "receita_media_12m", "ultima_venda", "status_receita"] if c in receita.columns]
        df = df.merge(receita[cols_receita], on=chave_receita, how="left")
    else:
        df["total"] = 0.0
        df["receita_media_12m"] = 0.0
        df["ultima_venda"] = pd.NaT
        df["status_receita"] = "Sem receita real/manual importada"

    df["total"] = pd.to_numeric(df.get("total"), errors="coerce").fillna(0)
    receita_total = df["total"].sum(skipna=True)

    df["participacao_receita_pct"] = df["total"] / receita_total * 100 if receita_total else 0.0

    df["over_under_share_pct"] = (
        pd.to_numeric(df["participacao_receita_pct"], errors="coerce").fillna(0)
        - pd.to_numeric(df["idc_base"], errors="coerce").fillna(0)
    )

    df["receita_esperada_idc"] = (
        receita_total * (pd.to_numeric(df["idc_base"], errors="coerce").fillna(0) / 100)
        if receita_total else 0.0
    )

    df["oportunidade"] = df["receita_esperada_idc"] - df["total"]
    df["margin_pool_pct"] = df["oportunidade"] / receita_total * 100 if receita_total else 0.0
    df["observacao_idc"] = "IDC oficial calculado no universo Sudeste; filtros alteram apenas a exibição."

    # Filtro só no final para manter o mesmo IDC entre MG e Todos.
    if estados_norm:
        df = df[df["estado"].astype(str).str.upper().isin(estados_norm)].copy()

    return _round4_df(
        df.sort_values(["score", "populacao"], ascending=False, na_position="last")
    )
# IDC_FINAL_ESTAVEL_MICRO_CIDADE_FIM
'''

txt = txt.rstrip() + "\n\n" + bloco + "\n"

path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ expansao_service.py ajustado com IDC estável e visão cidade/microrregião.")
print(f"Backup criado em: {backup}")

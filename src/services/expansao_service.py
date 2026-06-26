
from __future__ import annotations

from io import BytesIO

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


ESTADOS_SUDESTE = ["MG", "SP", "RJ", "ES"]
CATEGORIAS_PESCADOS = ["Tilápia", "Salmão", "Camarão", "Piramutaba", "Polaca", "Merluza", "Panga"]


def _relation_exists(conn, relation_name: str) -> bool:
    return bool(conn.execute(text("SELECT to_regclass(:name) IS NOT NULL"), {"name": relation_name}).scalar())


def _safe_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in cols:
        if col not in df.columns:
            df[col] = pd.NA
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _sum_or_na(series: pd.Series):
    s = pd.to_numeric(series, errors="coerce").dropna()
    return s.sum() if len(s) else pd.NA


def _mean_or_na(series: pd.Series):
    s = pd.to_numeric(series, errors="coerce").dropna()
    return s.mean() if len(s) else pd.NA


def _classificar_score(score: float) -> str:
    if score is None or pd.isna(score):
        return "Sem dados"
    score = float(score or 0)
    if score >= 75:
        return "Alta prioridade"
    if score >= 55:
        return "Média prioridade"
    if score >= 35:
        return "Baixa prioridade"
    return "Monitorar"


def _base_expansao_municipal(estados: list[str] | None = None) -> pd.DataFrame:
    estados = estados or ESTADOS_SUDESTE
    engine = get_engine()

    sql_view = """
        SELECT
            codigo_ibge,
            uf AS estado,
            nome_uf,
            municipio,
            mesorregiao,
            COALESCE(microrregiao, 'Sem microrregião') AS microrregiao,
            regiao_comercial,
            populacao,
            pib,
            pib_per_capita,
            idh,
            renda_media,
            pct_masculina,
            pct_feminina,
            pct_0_14,
            pct_15_29,
            pct_30_44,
            pct_45_59,
            pct_60_plus,
            renda_classe_a,
            renda_classe_b,
            renda_classe_c,
            renda_classe_de,
            supermercados,
            restaurantes,
            peixarias,
            outros_pdv,
            fonte_populacao,
            fonte_pib,
            fonte_idh,
            fonte_renda,
            fonte_demografia,
            fonte_pdv,
            status_dados,
            observacao,
            data_atualizacao
        FROM app.vw_expansao_municipio
        WHERE uf = ANY(:estados)
    """

    sql_fallback = """
        SELECT
            g.codigo_ibge,
            g.uf AS estado,
            g.nome_uf,
            g.municipio,
            g.mesorregiao,
            COALESCE(g.microrregiao, 'Sem microrregião') AS microrregiao,
            g.regiao_comercial,
            pop.valor AS populacao,
            pib.valor AS pib,
            CASE WHEN pop.valor > 0 THEN pib.valor / pop.valor ELSE NULL END AS pib_per_capita,
            NULL::NUMERIC AS idh,
            NULL::NUMERIC AS renda_media,
            NULL::NUMERIC AS pct_masculina,
            NULL::NUMERIC AS pct_feminina,
            NULL::NUMERIC AS pct_0_14,
            NULL::NUMERIC AS pct_15_29,
            NULL::NUMERIC AS pct_30_44,
            NULL::NUMERIC AS pct_45_59,
            NULL::NUMERIC AS pct_60_plus,
            NULL::NUMERIC AS renda_classe_a,
            NULL::NUMERIC AS renda_classe_b,
            NULL::NUMERIC AS renda_classe_c,
            NULL::NUMERIC AS renda_classe_de,
            NULL::NUMERIC AS supermercados,
            NULL::NUMERIC AS restaurantes,
            NULL::NUMERIC AS peixarias,
            NULL::NUMERIC AS outros_pdv,
            CASE WHEN pop.valor IS NOT NULL THEN 'IBGE/SIDRA dw.fato_indicador_municipal' ELSE NULL END AS fonte_populacao,
            CASE WHEN pib.valor IS NOT NULL THEN 'IBGE/SIDRA dw.fato_indicador_municipal' ELSE NULL END AS fonte_pib,
            'Pendente: fonte externa/Atlas Brasil' AS fonte_idh,
            'Pendente: Censo/POF/renda' AS fonte_renda,
            'Pendente: Censo sexo/faixa etária' AS fonte_demografia,
            'Pendente: cadastro interno/API externa' AS fonte_pdv,
            'parcial' AS status_dados,
            'Fallback sem app.vw_expansao_municipio' AS observacao,
            NULL::TIMESTAMP AS data_atualizacao
        FROM dw.dim_geografia g
        LEFT JOIN LATERAL (
            SELECT valor
            FROM dw.fato_indicador_municipal im
            WHERE im.codigo_ibge = g.codigo_ibge
              AND im.indicador ILIKE '%popula%'
            ORDER BY im.data_referencia DESC, im.data_coleta DESC, im.id DESC
            LIMIT 1
        ) pop ON TRUE
        LEFT JOIN LATERAL (
            SELECT valor
            FROM dw.fato_indicador_municipal im
            WHERE im.codigo_ibge = g.codigo_ibge
              AND im.indicador ILIKE '%PIB%'
            ORDER BY im.data_referencia DESC, im.data_coleta DESC, im.id DESC
            LIMIT 1
        ) pib ON TRUE
        WHERE g.uf = ANY(:estados)
    """

    with engine.begin() as conn:
        if _relation_exists(conn, "app.vw_expansao_municipio"):
            df = pd.read_sql(text(sql_view), conn, params={"estados": estados})
        else:
            df = pd.read_sql(text(sql_fallback), conn, params={"estados": estados})

    numeric_cols = [
        "populacao", "pib", "pib_per_capita", "idh", "renda_media",
        "pct_masculina", "pct_feminina", "pct_0_14", "pct_15_29",
        "pct_30_44", "pct_45_59", "pct_60_plus",
        "renda_classe_a", "renda_classe_b", "renda_classe_c", "renda_classe_de",
        "supermercados", "restaurantes", "peixarias", "outros_pdv",
    ]
    return _safe_numeric(df, numeric_cols)


def _score_pct(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    max_v = s.max()
    if max_v <= 0:
        return pd.Series([pd.NA] * len(s), index=s.index)
    return s / max_v * 100




def _with_regiao_economica(df: pd.DataFrame) -> pd.DataFrame:
    """Cria a região econômica/comercial da Análise de Expansão.

    Regra atual, alinhada ao plano:
    - MG usa a classificação comercial já criada em Região Comercial MG.
    - SP/RJ/ES usam a mesorregião IBGE como região econômica inicial.
    - Quando faltar mesorregião, usa microrregião.
    - Quando faltar tudo, marca como "Sem região econômica".

    Isso mantém a lógica ajustável: depois a empresa pode trocar a regra
    sem alterar as fórmulas de população, PIB, IDH, IDC e score.
    """
    df = df.copy()
    estado = df.get("estado")
    regiao_comercial = df.get("regiao_comercial")
    mesorregiao = df.get("mesorregiao")
    microrregiao = df.get("microrregiao")

    if "regiao_comercial" not in df.columns:
        df["regiao_comercial"] = pd.NA
    if "mesorregiao" not in df.columns:
        df["mesorregiao"] = pd.NA
    if "microrregiao" not in df.columns:
        df["microrregiao"] = pd.NA

    df["regiao_economica"] = df["regiao_comercial"].where(
        (df["estado"] == "MG") & df["regiao_comercial"].notna() & (df["regiao_comercial"].astype(str).str.strip() != ""),
        df["mesorregiao"],
    )
    df["regiao_economica"] = df["regiao_economica"].fillna(df["microrregiao"])
    df["regiao_economica"] = df["regiao_economica"].fillna("Sem região econômica")
    df["regiao_economica"] = df["regiao_economica"].replace("", "Sem região econômica")
    return df


def carregar_regioes_economicas_expansao(estados: list[str] | None = None) -> pd.DataFrame:
    """Resumo por região econômica/comercial para o seletor da Análise de Expansão."""
    df = _with_regiao_economica(_base_expansao_municipal(estados))
    if df.empty:
        return df

    resumo = (
        df.groupby(["estado", "regiao_economica"], as_index=False)
        .agg(
            populacao=("populacao", _sum_or_na),
            pib=("pib", _sum_or_na),
            pib_per_capita=("pib_per_capita", _mean_or_na),
            idh=("idh", _mean_or_na),
            renda_media=("renda_media", _mean_or_na),
            supermercados=("supermercados", _sum_or_na),
            restaurantes=("restaurantes", _sum_or_na),
            peixarias=("peixarias", _sum_or_na),
            outros_pdv=("outros_pdv", _sum_or_na),
            qtd_municipios=("codigo_ibge", "nunique"),
            qtd_microrregioes=("microrregiao", "nunique"),
            municipios_com_populacao=("populacao", lambda x: x.notna().sum()),
            municipios_com_pib=("pib", lambda x: x.notna().sum()),
            municipios_com_idh=("idh", lambda x: x.notna().sum()),
        )
    )

    pop_total = pd.to_numeric(resumo["populacao"], errors="coerce").sum(skipna=True)
    pib_total = pd.to_numeric(resumo["pib"], errors="coerce").sum(skipna=True)

    resumo["participacao_populacao_pct"] = (
        pd.to_numeric(resumo["populacao"], errors="coerce") / pop_total * 100 if pop_total else pd.NA
    )
    resumo["participacao_pib_pct"] = (
        pd.to_numeric(resumo["pib"], errors="coerce") / pib_total * 100 if pib_total else pd.NA
    )
    resumo["idc_base_regiao"] = (
        (resumo["participacao_populacao_pct"].fillna(0) + resumo["participacao_pib_pct"].fillna(0)) / 2
        if pib_total else resumo["participacao_populacao_pct"]
    )

    score_base = resumo["idc_base_regiao"].fillna(0)
    if score_base.sum() <= 0:
        score_base = pd.to_numeric(resumo["populacao"], errors="coerce")
    resumo["score_regiao"] = _score_pct(score_base)
    resumo["classificacao_regiao"] = resumo["score_regiao"].apply(_classificar_score)

    return resumo.sort_values(["estado", "score_regiao"], ascending=[True, False], na_position="last")


def carregar_municipios_regiao_economica_expansao(
    estado: str | None = None,
    regiao_economica: str | None = None,
) -> pd.DataFrame:
    """Municípios de uma região econômica/comercial selecionada."""
    estados = [estado] if estado and estado != "Todos" else ESTADOS_SUDESTE
    df = _with_regiao_economica(_base_expansao_municipal(estados))
    if df.empty:
        return df

    if estado and estado != "Todos":
        df = df[df["estado"] == estado]

    if regiao_economica and regiao_economica != "Todas":
        df = df[df["regiao_economica"] == regiao_economica]

    cols = [
        "estado", "regiao_economica", "municipio", "codigo_ibge", "microrregiao", "mesorregiao",
        "populacao", "pib", "pib_per_capita", "idh", "renda_media",
        "supermercados", "restaurantes", "peixarias", "outros_pdv",
        "fonte_populacao", "fonte_pib", "fonte_idh", "fonte_pdv",
    ]
    for col in cols:
        if col not in df.columns:
            df[col] = pd.NA

    return df[cols].sort_values(["populacao", "pib"], ascending=False, na_position="last")


def carregar_resumo_estado_expansao(estados: list[str] | None = None) -> pd.DataFrame:
    df = _base_expansao_municipal(estados)
    if df.empty:
        return df

    resumo = (
        df.groupby(["estado", "nome_uf"], as_index=False)
        .agg(
            populacao=("populacao", _sum_or_na),
            idh=("idh", _mean_or_na),
            pib=("pib", _sum_or_na),
            pib_per_capita=("pib_per_capita", _mean_or_na),
            qtd_municipios=("codigo_ibge", "nunique"),
            municipios_com_populacao=("populacao", lambda x: x.notna().sum()),
            municipios_com_pib=("pib", lambda x: x.notna().sum()),
        )
    )

    pop_total = pd.to_numeric(resumo["populacao"], errors="coerce").sum(skipna=True)
    pib_total = pd.to_numeric(resumo["pib"], errors="coerce").sum(skipna=True)

    resumo["participacao_populacao_pct"] = pd.to_numeric(resumo["populacao"], errors="coerce") / pop_total * 100 if pop_total else pd.NA
    resumo["participacao_pib_pct"] = pd.to_numeric(resumo["pib"], errors="coerce") / pib_total * 100 if pib_total else pd.NA

    if pib_total:
        resumo["idc"] = (resumo["participacao_populacao_pct"] + resumo["participacao_pib_pct"]) / 2
    else:
        resumo["idc"] = resumo["participacao_populacao_pct"]

    resumo["score_expansao"] = _score_pct(resumo["idc"])
    resumo["classificacao"] = resumo["score_expansao"].apply(_classificar_score)
    resumo["status_dados"] = resumo.apply(
        lambda r: "IBGE população + PIB" if r["municipios_com_pib"] > 0 else (
            "IBGE população; PIB pendente" if r["municipios_com_populacao"] > 0 else "Pendente carga IBGE"
        ),
        axis=1,
    )

    return resumo.sort_values("score_expansao", ascending=False, na_position="last")


def carregar_microrregiao_expansao(estados: list[str] | None = None) -> pd.DataFrame:
    df = _base_expansao_municipal(estados)
    if df.empty:
        return df

    resumo = (
        df.groupby(["estado", "microrregiao"], as_index=False)
        .agg(
            populacao=("populacao", _sum_or_na),
            idh=("idh", _mean_or_na),
            renda_media=("renda_media", _mean_or_na),
            pib=("pib", _sum_or_na),
            pib_per_capita=("pib_per_capita", _mean_or_na),
            supermercados=("supermercados", _sum_or_na),
            restaurantes=("restaurantes", _sum_or_na),
            peixarias=("peixarias", _sum_or_na),
            outros_pdv=("outros_pdv", _sum_or_na),
            qtd_municipios=("codigo_ibge", "nunique"),
            municipios_com_populacao=("populacao", lambda x: x.notna().sum()),
            municipios_com_pib=("pib", lambda x: x.notna().sum()),
        )
    )

    score_base = pd.to_numeric(resumo["pib"], errors="coerce")
    if score_base.fillna(0).sum() <= 0:
        score_base = pd.to_numeric(resumo["populacao"], errors="coerce")
    if score_base.fillna(0).sum() <= 0:
        score_base = resumo["qtd_municipios"]

    resumo["score"] = _score_pct(score_base)
    resumo["classificacao"] = resumo["score"].apply(_classificar_score)
    resumo["status_dados"] = resumo.apply(
        lambda r: "IBGE população + PIB" if r["municipios_com_pib"] > 0 else (
            "IBGE população; PIB pendente" if r["municipios_com_populacao"] > 0 else "Pendente carga IBGE"
        ),
        axis=1,
    )

    return resumo.sort_values(["score", "populacao"], ascending=False, na_position="last")


def carregar_perfil_demografico_expansao(estados: list[str] | None = None) -> pd.DataFrame:
    df = _base_expansao_municipal(estados)
    if df.empty:
        return df

    resumo = (
        df.groupby(["microrregiao", "estado"], as_index=False)
        .agg(
            populacao_total=("populacao", _sum_or_na),
            pct_masculina=("pct_masculina", _mean_or_na),
            pct_feminina=("pct_feminina", _mean_or_na),
            pct_0_14=("pct_0_14", _mean_or_na),
            pct_15_29=("pct_15_29", _mean_or_na),
            pct_30_44=("pct_30_44", _mean_or_na),
            pct_45_59=("pct_45_59", _mean_or_na),
            pct_60_plus=("pct_60_plus", _mean_or_na),
            renda_classe_a=("renda_classe_a", _mean_or_na),
            renda_classe_b=("renda_classe_b", _mean_or_na),
            renda_classe_c=("renda_classe_c", _mean_or_na),
            renda_classe_de=("renda_classe_de", _mean_or_na),
            fonte_demografia=("fonte_demografia", "first"),
            fonte_renda=("fonte_renda", "first"),
        )
    )
    return resumo.sort_values("populacao_total", ascending=False, na_position="last")


def carregar_receita_categoria_expansao(estados: list[str] | None = None) -> pd.DataFrame:
    estados = estados or ESTADOS_SUDESTE
    engine = get_engine()

    base = carregar_microrregiao_expansao(estados=estados)
    if base.empty:
        return base
    base = base[["microrregiao", "estado"]].copy()

    with engine.begin() as conn:
        exists = _relation_exists(conn, "app.vw_vendas_analitica")
        if not exists:
            for cat in CATEGORIAS_PESCADOS:
                base[cat] = pd.NA
            base["total"] = pd.NA
            base["status_receita"] = "Sem view de vendas carregada"
            return base

        sql = """
            SELECT
                COALESCE(g.microrregiao, 'Sem microrregião') AS microrregiao,
                v.uf AS estado,
                COALESCE(NULLIF(v.proteina, ''), NULLIF(v.produto, ''), 'Outros') AS categoria_pescado,
                SUM(COALESCE(v.valor_venda, 0)) AS receita
            FROM app.vw_vendas_analitica v
            LEFT JOIN dw.dim_geografia g
                ON g.codigo_ibge = v.codigo_ibge
            WHERE v.uf = ANY(:estados)
            GROUP BY COALESCE(g.microrregiao, 'Sem microrregião'), v.uf, COALESCE(NULLIF(v.proteina, ''), NULLIF(v.produto, ''), 'Outros')
        """
        df = pd.read_sql(text(sql), conn, params={"estados": estados})

    if df.empty:
        for cat in CATEGORIAS_PESCADOS:
            base[cat] = pd.NA
        base["total"] = pd.NA
        base["status_receita"] = "Sem vendas internas para o recorte"
        return base

    pivot = df.pivot_table(
        index=["microrregiao", "estado"],
        columns="categoria_pescado",
        values="receita",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    out = base.merge(pivot, on=["microrregiao", "estado"], how="left")
    for cat in CATEGORIAS_PESCADOS:
        if cat not in out.columns:
            out[cat] = 0.0

    out[CATEGORIAS_PESCADOS] = out[CATEGORIAS_PESCADOS].fillna(0)
    out["total"] = out[CATEGORIAS_PESCADOS].sum(axis=1)
    out["status_receita"] = out["total"].apply(lambda v: "Receita real" if float(v or 0) > 0 else "Sem venda real no recorte")

    return out[["microrregiao", "estado"] + CATEGORIAS_PESCADOS + ["total", "status_receita"]]


def calcular_idc_expansao(estados: list[str] | None = None) -> pd.DataFrame:
    df_micro = carregar_microrregiao_expansao(estados=estados)
    df_receita = carregar_receita_categoria_expansao(estados=estados)
    if df_micro.empty:
        return df_micro

    df = df_micro.merge(df_receita[["microrregiao", "estado", "total"]], on=["microrregiao", "estado"], how="left")
    df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0)

    pop_total = pd.to_numeric(df["populacao"], errors="coerce").sum(skipna=True)
    pib_total = pd.to_numeric(df["pib"], errors="coerce").sum(skipna=True)
    receita_total = df["total"].sum(skipna=True)

    df["participacao_populacao_pct"] = pd.to_numeric(df["populacao"], errors="coerce") / pop_total * 100 if pop_total else pd.NA
    df["participacao_pib_pct"] = pd.to_numeric(df["pib"], errors="coerce") / pib_total * 100 if pib_total else pd.NA

    if pib_total:
        df["idc_base"] = (df["participacao_populacao_pct"] + df["participacao_pib_pct"]) / 2
    else:
        df["idc_base"] = df["participacao_populacao_pct"]

    df["participacao_receita_pct"] = df["total"] / receita_total * 100 if receita_total else 0
    df["over_under_share_pct"] = df["participacao_receita_pct"] - df["idc_base"].fillna(0)
    df["receita_esperada_idc"] = receita_total * (df["idc_base"].fillna(0) / 100) if receita_total else 0.0
    df["oportunidade"] = df["receita_esperada_idc"] - df["total"]
    df["margin_pool_pct"] = df["oportunidade"] / receita_total * 100 if receita_total else 0.0

    df["score"] = (df["idc_base"].fillna(0) - df["over_under_share_pct"]).clip(lower=0)
    df["score"] = _score_pct(df["score"])
    df["classificacao"] = df["score"].apply(_classificar_score)
    df["observacao_idc"] = df.apply(
        lambda r: "IDC com população + PIB" if pd.notna(r.get("pib")) and float(r.get("pib") or 0) > 0 else "IDC usando população; PIB pendente",
        axis=1,
    )

    # Compatibilidade classificação:
    # A view nova usa classificacao_score; telas antigas esperam classificacao.
    if "classificacao" not in df.columns:
        if "classificacao_score" in df.columns:
            df["classificacao"] = df["classificacao_score"]
        elif "score" in df.columns:
            score_tmp = pd.to_numeric(df["score"], errors="coerce").fillna(0)
            df["classificacao"] = pd.cut(
                score_tmp,
                bins=[-1, 35, 55, 75, 101],
                labels=["Monitorar", "Baixa", "Média", "Alta"]
            ).astype(str)
        else:
            df["classificacao"] = "Monitorar"

    if "classificacao_score" not in df.columns:
        df["classificacao_score"] = df["classificacao"]

    return df.sort_values("score", ascending=False, na_position="last")


def _normalizar_serie_0_100(series: pd.Series) -> pd.Series:
    """Normaliza uma série para 0-100 dentro do recorte.

    Usada no simulador para transformar renda, PDV e perfil demográfico em
    escalas comparáveis. Se todos os valores forem zero/nulos, retorna 50
    como neutro para não penalizar fonte ainda não carregada.
    """
    s = pd.to_numeric(series, errors="coerce")
    if s.notna().sum() == 0:
        return pd.Series([50.0] * len(s), index=s.index)

    s = s.fillna(s.median(skipna=True) if s.notna().sum() else 0)
    max_v = s.max(skipna=True)
    min_v = s.min(skipna=True)

    if pd.isna(max_v) or max_v <= 0:
        return pd.Series([50.0] * len(s), index=s.index)

    # Quando a variação é pequena, usa proporção simples para evitar divisão por zero.
    if max_v == min_v:
        return pd.Series([100.0 if max_v > 0 else 50.0] * len(s), index=s.index)

    return (s / max_v * 100).clip(lower=0, upper=100)


def _preparar_fatores_simulador_idc(df: pd.DataFrame, estados: list[str] | None = None) -> pd.DataFrame:
    """Adiciona todos os fatores usados no IDC simulado.

    Fatores finais em escala 0-100:
    - fator_populacao
    - fator_pib
    - fator_masculino
    - fator_feminino
    - fator_renda
    - fator_pib_per_capita
    - fator_pdv
    """
    out = df.copy()

    demo = carregar_perfil_demografico_expansao(estados=estados)
    if not demo.empty:
        cols_demo = [
            "microrregiao", "estado", "pct_masculina", "pct_feminina",
            "pct_15_29", "pct_30_44", "pct_45_59",
            "renda_classe_a", "renda_classe_b", "renda_classe_c", "renda_classe_de",
        ]
        cols_demo = [c for c in cols_demo if c in demo.columns]
        out = out.merge(demo[cols_demo], on=["microrregiao", "estado"], how="left", suffixes=("", "_demo"))

    # População e PIB já são participações relativas do recorte.
    out["fator_populacao"] = pd.to_numeric(out.get("participacao_populacao_pct"), errors="coerce").fillna(0)
    out["fator_pib"] = pd.to_numeric(out.get("participacao_pib_pct"), errors="coerce").fillna(0)

    # Gênero: usa o percentual demográfico da região e normaliza pelo maior valor do recorte.
    out["fator_masculino"] = _normalizar_serie_0_100(out.get("pct_masculina", pd.Series(index=out.index, dtype=float)))
    out["fator_feminino"] = _normalizar_serie_0_100(out.get("pct_feminina", pd.Series(index=out.index, dtype=float)))

    # Renda: prioriza regiões com maior renda média proxy/oficial.
    out["fator_renda"] = _normalizar_serie_0_100(out.get("renda_media", pd.Series(index=out.index, dtype=float)))

    # PIB per capita: mede intensidade econômica por habitante.
    # Entra no lugar da antiga faixa etária no simulador.
    out["fator_pib_per_capita"] = _normalizar_serie_0_100(out.get("pib_per_capita", pd.Series(index=out.index, dtype=float)))

    # PDV: soma supermercados, restaurantes, peixarias e outros pontos.
    pdv_total = (
        pd.to_numeric(out.get("supermercados", 0), errors="coerce").fillna(0)
        + pd.to_numeric(out.get("restaurantes", 0), errors="coerce").fillna(0)
        + pd.to_numeric(out.get("peixarias", 0), errors="coerce").fillna(0)
        + pd.to_numeric(out.get("outros_pdv", 0), errors="coerce").fillna(0)
    )
    out["pdv_total"] = pdv_total
    out["fator_pdv"] = _normalizar_serie_0_100(pdv_total)

    return out


def simular_idc_expansao(
    peso_populacao: float = 30,
    peso_pib: float = 25,
    peso_renda: float = 15,
    peso_pib_per_capita: float = 15,
    peso_masculino: float = 5,
    peso_feminino: float = 5,
    peso_pdv: float = 5,
    estados: list[str] | None = None,
) -> pd.DataFrame:
    df = calcular_idc_expansao(estados=estados)
    if df.empty:
        return df

    df = _preparar_fatores_simulador_idc(df, estados=estados)

    pesos_brutos = {
        "fator_populacao": float(peso_populacao or 0),
        "fator_pib": float(peso_pib or 0),
        "fator_renda": float(peso_renda or 0),
        "fator_pib_per_capita": float(peso_pib_per_capita or 0),
        "fator_masculino": float(peso_masculino or 0),
        "fator_feminino": float(peso_feminino or 0),
        "fator_pdv": float(peso_pdv or 0),
    }

    soma_pesos = sum(pesos_brutos.values())
    if soma_pesos <= 0:
        pesos_brutos = {
            "fator_populacao": 30.0,
            "fator_pib": 25.0,
            "fator_renda": 15.0,
            "fator_pib_per_capita": 15.0,
            "fator_masculino": 5.0,
            "fator_feminino": 5.0,
            "fator_pdv": 5.0,
        }
        soma_pesos = 100.0

    # Mesmo se a tela enviar 99/101 por arredondamento, o cálculo normaliza para 100%.
    pesos_norm = {col: peso / soma_pesos for col, peso in pesos_brutos.items()}

    df["idc_simulado"] = 0.0
    for col, peso_norm in pesos_norm.items():
        df["idc_simulado"] += pd.to_numeric(df[col], errors="coerce").fillna(0) * peso_norm

    df["score_simulado"] = _score_pct(df["idc_simulado"])
    df["nova_classificacao"] = df["score_simulado"].apply(_classificar_score)
    df["diferenca_idc"] = df["idc_simulado"] - df["idc_base"].fillna(0)

    df["peso_total_simulador"] = round(sum(pesos_brutos.values()), 6)
    df["peso_populacao_pct"] = pesos_norm["fator_populacao"] * 100
    df["peso_pib_pct"] = pesos_norm["fator_pib"] * 100
    df["peso_renda_pct"] = pesos_norm["fator_renda"] * 100
    df["peso_pib_per_capita_pct"] = pesos_norm["fator_pib_per_capita"] * 100
    df["peso_masculino_pct"] = pesos_norm["fator_masculino"] * 100
    df["peso_feminino_pct"] = pesos_norm["fator_feminino"] * 100
    df["peso_pdv_pct"] = pesos_norm["fator_pdv"] * 100

    df["status_simulador"] = (
        "IDC simulado com pesos normalizados para 100%; fatores demografia/renda/PDV usam fonte carregada ou proxy marcado no app"
    )

    cols_prioritarias = [
        "microrregiao", "estado",
        "idc_base", "idc_simulado", "diferenca_idc",
        "score", "score_simulado", "classificacao", "nova_classificacao",
        "participacao_populacao_pct", "participacao_pib_pct",
        "fator_populacao", "fator_pib", "fator_renda", "fator_pib_per_capita",
        "fator_masculino", "fator_feminino", "fator_pdv", "pdv_total",
        "peso_total_simulador",
        "peso_populacao_pct", "peso_pib_pct", "peso_renda_pct", "peso_pib_per_capita_pct",
        "peso_masculino_pct", "peso_feminino_pct", "peso_pdv_pct",
        "status_simulador",
    ]
    cols = [c for c in cols_prioritarias if c in df.columns] + [c for c in df.columns if c not in cols_prioritarias]
    return df[cols].sort_values("score_simulado", ascending=False, na_position="last")

def exportar_bases_expansao_excel(parametros: dict | None = None, estados: list[str] | None = None) -> bytes:
    parametros = parametros or {}
    sheets = {
        "Resumo_Estado": carregar_resumo_estado_expansao(estados=estados),
        "Microrregiao_Indicadores": carregar_microrregiao_expansao(estados=estados),
        "Perfil_Demografico": carregar_perfil_demografico_expansao(estados=estados),
        "Receita_Categoria": carregar_receita_categoria_expansao(estados=estados),
        "IDC_Base": calcular_idc_expansao(estados=estados),
        "IDC_Simulado": simular_idc_expansao(estados=estados, **parametros),
        "Parametros_Simulador": pd.DataFrame([parametros]),
        "Dicionario": pd.DataFrame([
            {"campo": "IDH", "descricao": "Campo preparado. Não preenchido com zero falso; depende de fonte externa confiável."},
            {"campo": "PIB", "descricao": "Carregado via IBGE/SIDRA quando disponível."},
            {"campo": "População", "descricao": "Carregada via IBGE/SIDRA quando disponível."},
            {"campo": "PDV", "descricao": "Supermercados/restaurantes/peixarias dependem de fonte externa/cadastro."},
            {"campo": "IDC Base", "descricao": "Média entre participação de população e participação de PIB; se PIB ausente, usa população."},
        ]),
    }
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, index=False, sheet_name=name[:31])
    return output.getvalue()


# ============================================================
# HOTFIX — Expansão Receita Manual + IDC Estratégico + 4 casas
# ============================================================

PESOS_IDC_ESTRATEGICO_PADRAO = {
    "fator_populacao": 30.0,
    "fator_pib": 25.0,
    "fator_renda": 15.0,
    "fator_pib_per_capita": 15.0,
    "fator_masculino": 5.0,
    "fator_feminino": 5.0,
    "fator_pdv": 5.0,
}


def _round4_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_float_dtype(out[col]) or pd.api.types.is_integer_dtype(out[col]):
            out[col] = pd.to_numeric(out[col], errors="ignore")
            try:
                out[col] = out[col].round(4)
            except Exception:
                pass
    return out


def _calcular_fatores_idc_em_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["fator_populacao"] = pd.to_numeric(out.get("participacao_populacao_pct"), errors="coerce").fillna(0)
    out["fator_pib"] = pd.to_numeric(out.get("participacao_pib_pct"), errors="coerce").fillna(0)
    out["fator_renda"] = _normalizar_serie_0_100(out.get("renda_media", pd.Series(index=out.index, dtype=float)))
    out["fator_pib_per_capita"] = _normalizar_serie_0_100(out.get("pib_per_capita", pd.Series(index=out.index, dtype=float)))
    out["fator_masculino"] = _normalizar_serie_0_100(out.get("pct_masculina", pd.Series(index=out.index, dtype=float)))
    out["fator_feminino"] = _normalizar_serie_0_100(out.get("pct_feminina", pd.Series(index=out.index, dtype=float)))

    pdv_total = (
        pd.to_numeric(out.get("supermercados", 0), errors="coerce").fillna(0)
        + pd.to_numeric(out.get("restaurantes", 0), errors="coerce").fillna(0)
        + pd.to_numeric(out.get("peixarias", 0), errors="coerce").fillna(0)
        + pd.to_numeric(out.get("outros_pdv", 0), errors="coerce").fillna(0)
    )
    out["pdv_total"] = pdv_total
    out["fator_pdv"] = _normalizar_serie_0_100(pdv_total)
    return out


def _aplicar_idc_estrategico_padrao(df: pd.DataFrame, prefixo: str = "") -> pd.DataFrame:
    out = _calcular_fatores_idc_em_df(df)
    col_idc = f"idc_base{prefixo}"
    col_macro = f"idc_macro{prefixo}"

    # Mantém a fórmula antiga como IDC macro para comparação.
    out[col_macro] = (
        (pd.to_numeric(out.get("participacao_populacao_pct"), errors="coerce").fillna(0)
         + pd.to_numeric(out.get("participacao_pib_pct"), errors="coerce").fillna(0)) / 2
    )

    out[col_idc] = 0.0
    for fator, peso in PESOS_IDC_ESTRATEGICO_PADRAO.items():
        out[col_idc] += pd.to_numeric(out.get(fator), errors="coerce").fillna(0) * (peso / 100.0)

    return out


def _categoria_pescado_sql_case(alias_col: str = "grupo_produto") -> str:
    return f"""
        CASE
            WHEN LOWER({alias_col}) LIKE '%til%pia%' OR LOWER({alias_col}) LIKE '%tilapia%' THEN 'Tilápia'
            WHEN LOWER({alias_col}) LIKE '%salm%o%' OR LOWER({alias_col}) LIKE '%salmao%' THEN 'Salmão'
            WHEN LOWER({alias_col}) LIKE '%camar%' THEN 'Camarão'
            WHEN LOWER({alias_col}) LIKE '%piramutaba%' THEN 'Piramutaba'
            WHEN LOWER({alias_col}) LIKE '%polaca%' THEN 'Polaca'
            WHEN LOWER({alias_col}) LIKE '%merluza%' THEN 'Merluza'
            WHEN LOWER({alias_col}) LIKE '%panga%' THEN 'Panga'
            ELSE 'Outros'
        END
    """


def carregar_regioes_economicas_expansao(estados: list[str] | None = None) -> pd.DataFrame:
    df = _with_regiao_economica(_base_expansao_municipal(estados))
    if df.empty:
        return df

    resumo = (
        df.groupby(["estado", "regiao_economica"], as_index=False)
        .agg(
            populacao=("populacao", _sum_or_na),
            pib=("pib", _sum_or_na),
            pib_per_capita=("pib_per_capita", _mean_or_na),
            idh=("idh", _mean_or_na),
            renda_media=("renda_media", _mean_or_na),
            pct_masculina=("pct_masculina", _mean_or_na),
            pct_feminina=("pct_feminina", _mean_or_na),
            supermercados=("supermercados", _sum_or_na),
            restaurantes=("restaurantes", _sum_or_na),
            peixarias=("peixarias", _sum_or_na),
            outros_pdv=("outros_pdv", _sum_or_na),
            qtd_municipios=("codigo_ibge", "nunique"),
            qtd_microrregioes=("microrregiao", "nunique"),
            municipios_com_populacao=("populacao", lambda x: x.notna().sum()),
            municipios_com_pib=("pib", lambda x: x.notna().sum()),
            municipios_com_idh=("idh", lambda x: x.notna().sum()),
        )
    )

    pop_total = pd.to_numeric(resumo["populacao"], errors="coerce").sum(skipna=True)
    pib_total = pd.to_numeric(resumo["pib"], errors="coerce").sum(skipna=True)

    resumo["participacao_populacao_pct"] = pd.to_numeric(resumo["populacao"], errors="coerce") / pop_total * 100 if pop_total else pd.NA
    resumo["participacao_pib_pct"] = pd.to_numeric(resumo["pib"], errors="coerce") / pib_total * 100 if pib_total else pd.NA

    resumo = _aplicar_idc_estrategico_padrao(resumo, prefixo="_regiao")
    resumo["score_regiao"] = _score_pct(resumo["idc_base_regiao"])
    resumo["classificacao_regiao"] = resumo["score_regiao"].apply(_classificar_score)

    return _round4_df(resumo.sort_values(["estado", "score_regiao"], ascending=[True, False], na_position="last"))


def carregar_microrregiao_expansao(estados: list[str] | None = None) -> pd.DataFrame:
    df = _base_expansao_municipal(estados)
    if df.empty:
        return df

    resumo = (
        df.groupby(["estado", "microrregiao"], as_index=False)
        .agg(
            populacao=("populacao", _sum_or_na),
            idh=("idh", _mean_or_na),
            renda_media=("renda_media", _mean_or_na),
            pib=("pib", _sum_or_na),
            pib_per_capita=("pib_per_capita", _mean_or_na),
            pct_masculina=("pct_masculina", _mean_or_na),
            pct_feminina=("pct_feminina", _mean_or_na),
            supermercados=("supermercados", _sum_or_na),
            restaurantes=("restaurantes", _sum_or_na),
            peixarias=("peixarias", _sum_or_na),
            outros_pdv=("outros_pdv", _sum_or_na),
            qtd_municipios=("codigo_ibge", "nunique"),
            municipios_com_populacao=("populacao", lambda x: x.notna().sum()),
            municipios_com_pib=("pib", lambda x: x.notna().sum()),
        )
    )

    pop_total = pd.to_numeric(resumo["populacao"], errors="coerce").sum(skipna=True)
    pib_total = pd.to_numeric(resumo["pib"], errors="coerce").sum(skipna=True)
    resumo["participacao_populacao_pct"] = pd.to_numeric(resumo["populacao"], errors="coerce") / pop_total * 100 if pop_total else pd.NA
    resumo["participacao_pib_pct"] = pd.to_numeric(resumo["pib"], errors="coerce") / pib_total * 100 if pib_total else pd.NA

    resumo = _aplicar_idc_estrategico_padrao(resumo)
    resumo["score"] = _score_pct(resumo["idc_base"])
    resumo["classificacao"] = resumo["score"].apply(_classificar_score)
    resumo["status_dados"] = resumo.apply(
        lambda r: "IBGE população + PIB + IDC estratégico" if r["municipios_com_pib"] > 0 else (
            "IBGE população; PIB pendente" if r["municipios_com_populacao"] > 0 else "Pendente carga IBGE"
        ),
        axis=1,
    )

    return _round4_df(resumo.sort_values(["score", "populacao"], ascending=False, na_position="last"))


def _receita_manual_12m_por_micro(estados: list[str]) -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        if not _relation_exists(conn, "app.fato_receita_manual_expansao"):
            return pd.DataFrame()

        # Usa a última venda carregada como referência para os últimos 12 meses,
        # evitando classificar base antiga como sem venda se o arquivo histórico estiver congelado.
        max_data = conn.execute(text("""
            SELECT MAX(data_competencia)
            FROM app.fato_receita_manual_expansao
            WHERE estado = ANY(:estados)
        """), {"estados": estados}).scalar()

        if not max_data:
            return pd.DataFrame()

        sql = f"""
            WITH params AS (
                SELECT CAST(:max_data AS DATE) AS data_ref,
                       CAST(:max_data AS DATE) - INTERVAL '12 months' AS data_inicio
            ),
            base AS (
                SELECT
                    COALESCE(g.microrregiao, 'Sem microrregião') AS microrregiao,
                    r.estado,
                    r.categoria_pescado,
                    r.data_competencia,
                    r.vlr_total_liquido
                FROM app.fato_receita_manual_expansao r
                LEFT JOIN dw.dim_geografia g
                    ON UPPER(TRIM(g.uf)) = UPPER(TRIM(r.estado))
                   AND UPPER(TRIM(g.municipio)) = UPPER(TRIM(r.cidade))
                WHERE r.estado = ANY(:estados)
            ),
            agg AS (
                SELECT
                    b.microrregiao,
                    b.estado,
                    b.categoria_pescado,
                    SUM(CASE WHEN b.data_competencia >= p.data_inicio THEN COALESCE(b.vlr_total_liquido, 0) ELSE 0 END) AS receita_12m,
                    SUM(COALESCE(b.vlr_total_liquido, 0)) AS receita_total_historica,
                    MAX(b.data_competencia) AS ultima_venda
                FROM base b
                CROSS JOIN params p
                GROUP BY b.microrregiao, b.estado, b.categoria_pescado
            )
            SELECT *
            FROM agg
        """
        return pd.read_sql(text(sql), conn, params={"estados": estados, "max_data": max_data})


def carregar_receita_categoria_expansao(estados: list[str] | None = None) -> pd.DataFrame:
    estados = estados or ESTADOS_SUDESTE
    engine = get_engine()

    base = carregar_microrregiao_expansao(estados=estados)
    if base.empty:
        return base
    base = base[["microrregiao", "estado", "renda_media"]].copy()

    df = _receita_manual_12m_por_micro(estados)

    # Fallback: view analítica antiga, se a base manual ainda não foi carregada.
    if df.empty:
        with engine.begin() as conn:
            exists = _relation_exists(conn, "app.vw_vendas_analitica")
            if exists:
                sql = """
                    SELECT
                        COALESCE(g.microrregiao, 'Sem microrregião') AS microrregiao,
                        v.uf AS estado,
                        COALESCE(NULLIF(v.proteina, ''), NULLIF(v.produto, ''), 'Outros') AS categoria_pescado,
                        SUM(COALESCE(v.valor_venda, 0)) AS receita_12m,
                        SUM(COALESCE(v.valor_venda, 0)) AS receita_total_historica,
                        MAX(v.data_venda) AS ultima_venda
                    FROM app.vw_vendas_analitica v
                    LEFT JOIN dw.dim_geografia g
                        ON g.codigo_ibge = v.codigo_ibge
                    WHERE v.uf = ANY(:estados)
                      AND v.data_venda >= (CURRENT_DATE - INTERVAL '12 months')
                    GROUP BY COALESCE(g.microrregiao, 'Sem microrregião'), v.uf, COALESCE(NULLIF(v.proteina, ''), NULLIF(v.produto, ''), 'Outros')
                """
                try:
                    df = pd.read_sql(text(sql), conn, params={"estados": estados})
                except Exception:
                    df = pd.DataFrame()

    if df.empty:
        for cat in CATEGORIAS_PESCADOS:
            base[cat] = 0.0
        base["total"] = 0.0
        base["receita_media_12m"] = 0.0
        base["ultima_venda"] = pd.NaT
        base["status_receita"] = "Sem venda nos últimos 12 meses"
        return _round4_df(base[["microrregiao", "estado", "renda_media"] + CATEGORIAS_PESCADOS + ["total", "receita_media_12m", "ultima_venda", "status_receita"]])

    pivot = df.pivot_table(
        index=["microrregiao", "estado"],
        columns="categoria_pescado",
        values="receita_12m",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    status = (
        df.groupby(["microrregiao", "estado"], as_index=False)
        .agg(
            total=("receita_12m", "sum"),
            ultima_venda=("ultima_venda", "max"),
        )
    )
    status["receita_media_12m"] = pd.to_numeric(status["total"], errors="coerce").fillna(0) / 12
    status["status_receita"] = status["ultima_venda"].apply(
        lambda d: "Sem venda nos últimos 12 meses" if pd.isna(d) else f"Última venda: {pd.to_datetime(d).strftime('%d/%m/%Y')}"
    )
    status.loc[pd.to_numeric(status["total"], errors="coerce").fillna(0) <= 0, "status_receita"] = "Sem venda nos últimos 12 meses"

    out = base.merge(pivot, on=["microrregiao", "estado"], how="left")
    out = out.merge(status, on=["microrregiao", "estado"], how="left")

    for cat in CATEGORIAS_PESCADOS:
        if cat not in out.columns:
            out[cat] = 0.0

    out[CATEGORIAS_PESCADOS] = out[CATEGORIAS_PESCADOS].fillna(0)
    out["total"] = pd.to_numeric(out["total"], errors="coerce").fillna(0)
    out["receita_media_12m"] = pd.to_numeric(out["receita_media_12m"], errors="coerce").fillna(0)
    out["status_receita"] = out["status_receita"].fillna("Sem venda nos últimos 12 meses")

    return _round4_df(out[["microrregiao", "estado", "renda_media"] + CATEGORIAS_PESCADOS + ["total", "receita_media_12m", "ultima_venda", "status_receita"]])


def calcular_idc_expansao(estados: list[str] | None = None) -> pd.DataFrame:
    df_micro = carregar_microrregiao_expansao(estados=estados)
    df_receita = carregar_receita_categoria_expansao(estados=estados)
    if df_micro.empty:
        return df_micro

    df = df_micro.merge(
        df_receita[["microrregiao", "estado", "total", "receita_media_12m", "ultima_venda", "status_receita"]],
        on=["microrregiao", "estado"],
        how="left"
    )
    df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0)

    # idc_macro = fórmula antiga; idc_base = IDC estratégico com todos os fatores.
    receita_total = df["total"].sum(skipna=True)
    df["participacao_receita_pct"] = df["total"] / receita_total * 100 if receita_total else 0
    df["over_under_share_pct"] = df["participacao_receita_pct"] - df["idc_base"].fillna(0)
    df["receita_esperada_idc"] = receita_total * (df["idc_base"].fillna(0) / 100) if receita_total else 0.0
    df["oportunidade"] = df["receita_esperada_idc"] - df["total"]
    df["margin_pool_pct"] = df["oportunidade"] / receita_total * 100 if receita_total else 0.0

    df["score"] = (df["idc_base"].fillna(0) - df["over_under_share_pct"]).clip(lower=0)
    df["score"] = _score_pct(df["score"])
    df["classificacao"] = df["score"].apply(_classificar_score)
    df["observacao_idc"] = "IDC estratégico: população, PIB, renda, PIB per capita, gênero e PDV"

    return _round4_df(df.sort_values("score", ascending=False, na_position="last"))


def exportar_bases_expansao_excel(parametros: dict | None = None, estados: list[str] | None = None) -> bytes:
    parametros = parametros or {}
    sheets = {
        "Resumo_Estado": carregar_resumo_estado_expansao(estados=estados),
        "Regioes_Economicas": carregar_regioes_economicas_expansao(estados=estados),
        "Municipios": carregar_municipios_regiao_economica_expansao(estado=None, regiao_economica="Todas"),
        "Microrregiao_Indicadores": carregar_microrregiao_expansao(estados=estados),
        "Perfil_Demografico": carregar_perfil_demografico_expansao(estados=estados),
        "Receita_Categoria": carregar_receita_categoria_expansao(estados=estados),
        "IDC_Estrategico": calcular_idc_expansao(estados=estados),
        "IDC_Simulado": simular_idc_expansao(estados=estados, **parametros),
        "Parametros_Simulador": pd.DataFrame([parametros]),
        "Dicionario": pd.DataFrame([
            {"campo": "IDC Macro", "descricao": "Fórmula antiga: média entre participação de população e participação de PIB."},
            {"campo": "IDC Estratégico", "descricao": "Índice principal: população, PIB, renda, PIB per capita, gênero e pontos de venda."},
            {"campo": "Receita manual", "descricao": "Base manual: parceiro, cidade, estado, data_competencia, grupo_produto e vlr_total_liquido."},
            {"campo": "Status receita", "descricao": "Mostra a última venda por região ou Sem venda nos últimos 12 meses."},
            {"campo": "PDV", "descricao": "Pode ser proxy até existir base oficial de pontos de venda."},
        ]),
    }
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            if isinstance(df, pd.DataFrame):
                df.to_excel(writer, index=False, sheet_name=name[:31])
    return output.getvalue()

# ============================================================
# ETAPA 41 — Overrides finais: IDC planejado, proxies automáticos e view central
# ============================================================

PESOS_IDC_PLANEJADO = {
    "fator_populacao": 30.0,
    "fator_pib": 25.0,
    "fator_renda": 15.0,
    "fator_pib_per_capita": 15.0,
    "fator_feminino": 5.0,
    "fator_masculino": 5.0,
    "fator_pdv": 5.0,
}


def _view_exists_safe(relation_name: str) -> bool:
    engine = get_engine()
    try:
        with engine.begin() as conn:
            return _relation_exists(conn, relation_name)
    except Exception:
        return False


def _idc_completo_view(estados: list[str] | None = None) -> pd.DataFrame:
    estados = estados or ESTADOS_SUDESTE
    engine = get_engine()
    if not _view_exists_safe("app.vw_idc_completo_atual"):
        return pd.DataFrame()
    with engine.begin() as conn:
        df = pd.read_sql(text("""
            SELECT *
            FROM app.vw_idc_completo_atual
            WHERE estado = ANY(:estados)
            ORDER BY score DESC NULLS LAST, populacao DESC NULLS LAST
        """), conn, params={"estados": estados})
    return _round4_df(df)


def carregar_microrregiao_expansao(estados: list[str] | None = None) -> pd.DataFrame:
    df_view = _idc_completo_view(estados)
    if not df_view.empty:
        cols = [
            "estado", "microrregiao", "regiao_economica", "populacao", "idh", "renda_media",
            "pib", "pib_per_capita", "pct_feminina", "pct_masculina", "supermercados",
            "restaurantes", "peixarias", "outros_pdv", "total_pdv", "qtd_municipios",
            "participacao_populacao_pct", "participacao_pib_pct", "fator_populacao", "fator_pib",
            "fator_renda", "fator_pib_per_capita", "fator_feminino", "fator_masculino",
            "fator_pdv", "idc_macro", "idc_base", "score", "classificacao", "formula_idc",
            "fonte_renda", "fonte_demografia", "fonte_pdv", "data_atualizacao"
        ]
        cols = [c for c in cols if c in df_view.columns]
        return df_view[cols]

    # fallback antigo se a Etapa 41 ainda não foi aplicada
    return _round4_df(_aplicar_idc_estrategico_padrao(_base_expansao_municipal(estados)))


def carregar_perfil_demografico_expansao(estados: list[str] | None = None) -> pd.DataFrame:
    df_view = _idc_completo_view(estados)
    if not df_view.empty:
        cols = [
            "microrregiao", "estado", "populacao", "pct_masculina", "pct_feminina",
            "renda_media", "pib_per_capita", "fonte_renda", "fonte_demografia",
            "fator_renda", "fator_feminino", "fator_masculino"
        ]
        cols = [c for c in cols if c in df_view.columns]
        return df_view[cols].rename(columns={"populacao": "populacao_total"})
    return pd.DataFrame()


def calcular_idc_expansao(estados: list[str] | None = None) -> pd.DataFrame:
    df_view = _idc_completo_view(estados)
    if df_view.empty:
        return pd.DataFrame()

    # Se houver receita real interna, calcula over/under e margin pool. Se não houver, mantém 0 e sinaliza.
    df = df_view.copy()
    receita = carregar_receita_categoria_expansao(estados=estados)
    if not receita.empty and {"microrregiao", "estado", "total"}.issubset(receita.columns):
        df = df.merge(receita[["microrregiao", "estado", "total", "receita_media_12m", "ultima_venda", "status_receita"]], on=["microrregiao", "estado"], how="left")
    else:
        df["total"] = 0.0
        df["receita_media_12m"] = 0.0
        df["ultima_venda"] = pd.NaT
        df["status_receita"] = "Sem receita real/manual importada"

    df["total"] = pd.to_numeric(df.get("total"), errors="coerce").fillna(0)
    receita_total = df["total"].sum(skipna=True)
    df["participacao_receita_pct"] = df["total"] / receita_total * 100 if receita_total else 0.0
<<<<<<< HEAD
    # IDC_OFICIAL_NOVA_FORMULA_INICIO
    # Garante que o IDC base/oficial use a mesma fórmula do simulador.
    # Fórmula:
    # PIB 25% + População 30-44 40% + Masculino 10% + Feminino 0%
    # + Restaurantes 10% + População 15-29 10% + Total PDV 5%.
    def _num_col_idc_base(df_base, col):
        if col not in df_base.columns:
            return pd.Series([0] * len(df_base), index=df_base.index, dtype="float64")
        return pd.to_numeric(df_base[col], errors="coerce").fillna(0)

    def _fator_100_idc_base(df_base, col):
        s = _num_col_idc_base(df_base, col)
        max_v = s.max()
        if pd.isna(max_v) or max_v == 0:
            return pd.Series([0] * len(df_base), index=df_base.index, dtype="float64")
        return s / max_v * 100

    # Regra correta de PDV:
    # se total_pdv existir, usa total_pdv como base principal;
    # se não existir, usa pdv_total;
    # se nenhum existir, soma as colunas detalhadas.
    if "total_pdv" not in df.columns:
        if "pdv_total" in df.columns:
            df["total_pdv"] = _num_col_idc_base(df, "pdv_total")
        else:
            df["total_pdv"] = (
                _num_col_idc_base(df, "supermercados")
                + _num_col_idc_base(df, "restaurantes")
                + _num_col_idc_base(df, "peixarias")
                + _num_col_idc_base(df, "outros_pdv")
            )

    if "pdv_total" not in df.columns:
        df["pdv_total"] = _num_col_idc_base(df, "total_pdv")

    if "restaurantes" not in df.columns:
        df["restaurantes"] = 0

    df["fator_pib"] = _fator_100_idc_base(df, "pib")
    df["fator_pop_30_44"] = _fator_100_idc_base(df, "pct_30_44")
    df["fator_pop_15_29"] = _fator_100_idc_base(df, "pct_15_29")
    df["fator_masculino"] = _fator_100_idc_base(df, "pct_masculina")
    df["fator_feminino"] = _fator_100_idc_base(df, "pct_feminina")
    df["fator_restaurantes"] = _fator_100_idc_base(df, "restaurantes")
    df["fator_pdv_total"] = _fator_100_idc_base(df, "total_pdv")
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

    if "_classificar_score" in globals():
        df["classificacao_score"] = df["idc_base"].apply(_classificar_score)
    else:
        df["classificacao_score"] = pd.cut(
            pd.to_numeric(df["idc_base"], errors="coerce").fillna(0),
            bins=[-1, 35, 55, 75, 101],
            labels=["Monitorar", "Baixa", "Média", "Alta"]
        ).astype(str)

    df["classificacao"] = df["classificacao_score"]

    df["formula_idc"] = (
        "IDC = PIB 25% + População 30-44 40% + Masculino 10% + Feminino 0% "
        "+ Restaurantes 10% + População 15-29 10% + Total PDV 5%"
    )
    # IDC_OFICIAL_NOVA_FORMULA_FIM






=======
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf
    # Compatibilidade IDC:
    # A view nova usa idc_planejado/idc/idc_final/score_idc.
    # O código antigo ainda esperava idc_base.
    if "idc_base" not in df.columns:
        for col_idc in ["idc_planejado", "idc_final", "idc", "score_idc", "score"]:
            if col_idc in df.columns:
                df["idc_base"] = pd.to_numeric(df[col_idc], errors="coerce").fillna(0)
                break
        else:
            df["idc_base"] = 0

    if "participacao_receita_pct" not in df.columns:
        df["participacao_receita_pct"] = 0

    df["over_under_share_pct"] = (
        pd.to_numeric(df["participacao_receita_pct"], errors="coerce").fillna(0)
        - pd.to_numeric(df["idc_base"], errors="coerce").fillna(0)
    )

    df["receita_esperada_idc"] = receita_total * (pd.to_numeric(df["idc_base"], errors="coerce").fillna(0) / 100) if receita_total else 0.0
    df["oportunidade"] = df["receita_esperada_idc"] - df["total"]
    df["margin_pool_pct"] = df["oportunidade"] / receita_total * 100 if receita_total else 0.0
    df["observacao_idc"] = "IDC planejado com fatores automáticos/proxy; bases manuais entram quando importadas no app"

    return _round4_df(df.sort_values("score", ascending=False, na_position="last"))


def simular_idc_expansao(
    peso_populacao: float = 30,
    peso_pib: float = 25,
    peso_renda: float = 15,
    peso_pib_per_capita: float = 15,
    peso_feminino: float = 5,
    peso_masculino: float = 5,
    peso_pdv: float = 5,
    estados: list[str] | None = None,
) -> pd.DataFrame:
    df = calcular_idc_expansao(estados=estados)
    if df.empty:
        return df

    pesos = {
        "fator_populacao": float(peso_populacao or 0),
        "fator_pib": float(peso_pib or 0),
        "fator_renda": float(peso_renda or 0),
        "fator_pib_per_capita": float(peso_pib_per_capita or 0),
        "fator_feminino": float(peso_feminino or 0),
        "fator_masculino": float(peso_masculino or 0),
        "fator_pdv": float(peso_pdv or 0),
    }
    total_pesos = sum(pesos.values())

    if round(total_pesos, 6) != 100.0:
        df["idc_simulado"] = pd.to_numeric(df["idc_base"], errors="coerce").fillna(0)
        df["score_simulado"] = pd.to_numeric(df["score"], errors="coerce").fillna(0)
        df["nova_classificacao"] = df["classificacao"]
        df["diferenca_idc"] = 0.0
        df["peso_total_simulador"] = total_pesos
        df["status_simulador"] = "bloqueado: soma dos pesos precisa fechar 100%"
        return _round4_df(df)

    df["idc_simulado"] = 0.0
    for fator, peso in pesos.items():
        df["idc_simulado"] += pd.to_numeric(df.get(fator), errors="coerce").fillna(0) * (peso / 100.0)

    df["score_simulado"] = _score_pct(df["idc_simulado"])
    df["nova_classificacao"] = df["score_simulado"].apply(_classificar_score)
    df["diferenca_idc"] = df["idc_simulado"] - pd.to_numeric(df["idc_base"], errors="coerce").fillna(0)
    df["peso_total_simulador"] = total_pesos
    df["status_simulador"] = "ok: IDC simulado com pesos fechados em 100%"

    return _round4_df(df.sort_values("score_simulado", ascending=False, na_position="last"))


def carregar_receita_categoria_expansao(estados: list[str] | None = None) -> pd.DataFrame:
    estados = estados or ESTADOS_SUDESTE
    base = carregar_microrregiao_expansao(estados=estados)
    if base.empty:
        return base
    base = base[["microrregiao", "estado", "renda_media"]].copy() if "renda_media" in base.columns else base[["microrregiao", "estado"]].copy()
    if "renda_media" not in base.columns:
        base["renda_media"] = pd.NA

    df = _receita_manual_12m_por_micro(estados)
    if df.empty:
        # Sem manual: não inventa faturamento real. Mantém zeros, mas com status claro.
        for cat in CATEGORIAS_PESCADOS:
            base[cat] = 0.0
        base["total"] = 0.0
        base["receita_media_12m"] = 0.0
        base["ultima_venda"] = pd.NaT
        base["status_receita"] = "Sem receita real/manual importada"
        base["tipo_receita"] = "pendente_manual"
        return _round4_df(base[["microrregiao", "estado", "renda_media"] + CATEGORIAS_PESCADOS + ["total", "receita_media_12m", "ultima_venda", "status_receita", "tipo_receita"]])

    pivot = df.pivot_table(index=["microrregiao", "estado"], columns="categoria_pescado", values="receita_12m", aggfunc="sum", fill_value=0).reset_index()
    status = df.groupby(["microrregiao", "estado"], as_index=False).agg(total=("receita_12m", "sum"), ultima_venda=("ultima_venda", "max"))
    status["receita_media_12m"] = pd.to_numeric(status["total"], errors="coerce").fillna(0) / 12
    status["status_receita"] = status["ultima_venda"].apply(lambda d: "Sem venda nos últimos 12 meses" if pd.isna(d) else f"Última venda: {pd.to_datetime(d).strftime('%d/%m/%Y')}")
    status.loc[pd.to_numeric(status["total"], errors="coerce").fillna(0) <= 0, "status_receita"] = "Sem venda nos últimos 12 meses"
    out = base.merge(pivot, on=["microrregiao", "estado"], how="left").merge(status, on=["microrregiao", "estado"], how="left")
    for cat in CATEGORIAS_PESCADOS:
        if cat not in out.columns:
            out[cat] = 0.0
    out[CATEGORIAS_PESCADOS] = out[CATEGORIAS_PESCADOS].fillna(0)
    out["total"] = pd.to_numeric(out["total"], errors="coerce").fillna(0)
    out["receita_media_12m"] = pd.to_numeric(out["receita_media_12m"], errors="coerce").fillna(0)
    out["status_receita"] = out["status_receita"].fillna("Sem venda nos últimos 12 meses")
    out["tipo_receita"] = "receita_real_importada"
    return _round4_df(out[["microrregiao", "estado", "renda_media"] + CATEGORIAS_PESCADOS + ["total", "receita_media_12m", "ultima_venda", "status_receita", "tipo_receita"]])


def exportar_bases_expansao_excel(parametros: dict | None = None, estados: list[str] | None = None) -> bytes:
    parametros = parametros or {}
    sheets = {
        "IDC_Completo_Atual": calcular_idc_expansao(estados=estados),
        "Resumo_Estado": carregar_resumo_estado_expansao(estados=estados),
        "Regioes_Economicas": carregar_regioes_economicas_expansao(estados=estados),
        "Microrregiao_Indicadores": carregar_microrregiao_expansao(estados=estados),
        "Perfil_Demografico": carregar_perfil_demografico_expansao(estados=estados),
        "Receita_Categoria": carregar_receita_categoria_expansao(estados=estados),
        "IDC_Simulado": simular_idc_expansao(estados=estados, **parametros),
        "Parametros_Simulador": pd.DataFrame([parametros]),
        "Dicionario": pd.DataFrame([
            {"campo": "IDC planejado", "descricao": "30% população + 25% PIB + 15% renda + 15% PIB per capita + 5% feminino + 5% masculino + 5% PDV."},
            {"campo": "Renda", "descricao": "Usa fonte oficial quando carregada. Enquanto não houver, usa proxy PIB per capita mensal × 0,38 com fonte marcada."},
            {"campo": "Gênero", "descricao": "Usa Censo quando carregado. Enquanto não houver, usa proxy automático marcado na fonte_demografia."},
            {"campo": "Receita por categoria", "descricao": "Não inventa mercado real. Fica zero/pendente até importação manual/Scanntech."},
        ]),
    }
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            if isinstance(df, pd.DataFrame):
                df.to_excel(writer, index=False, sheet_name=name[:31])
    return output.getvalue()
<<<<<<< HEAD


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


# IDC_SIMULADOR_CANONICO_FINAL_INICIO
# Definição canônica do simulador/exportação alinhada à documentação atual.
# Mantida no final do módulo para sobrescrever implementações antigas de hotfix.
def _coalesce_peso(valor, legado=None, default=0.0) -> float:
    if valor is not None:
        return float(valor or 0)
    if legado is not None:
        return float(legado or 0)
    return float(default or 0)


def _garantir_fatores_idc_simulador(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["supermercados", "restaurantes", "peixarias", "outros_pdv"]:
        if col not in out.columns:
            out[col] = 0

    out = _garantir_total_pdv_idc_final(out) if "_garantir_total_pdv_idc_final" in globals() else out
    if "total_pdv" not in out.columns:
        out["total_pdv"] = (
            pd.to_numeric(out.get("supermercados", 0), errors="coerce").fillna(0)
            + pd.to_numeric(out.get("restaurantes", 0), errors="coerce").fillna(0)
            + pd.to_numeric(out.get("peixarias", 0), errors="coerce").fillna(0)
            + pd.to_numeric(out.get("outros_pdv", 0), errors="coerce").fillna(0)
        )
    out["pdv_total"] = pd.to_numeric(out.get("total_pdv"), errors="coerce").fillna(0)

    fatores = {
        "fator_pib": "pib",
        "fator_pop_30_44": "pct_30_44",
        "fator_pop_15_29": "pct_15_29",
        "fator_masculino": "pct_masculina",
        "fator_feminino": "pct_feminina",
        "fator_restaurantes": "restaurantes",
        "fator_pdv_total": "total_pdv",
    }
    for fator, origem in fatores.items():
        if fator not in out.columns:
            out[fator] = _fator_100_idc_final(out, origem) if "_fator_100_idc_final" in globals() else _score_pct(out.get(origem, pd.Series(index=out.index)))
        out[fator] = pd.to_numeric(out[fator], errors="coerce").fillna(0)

    # Compatibilidade controlada com telas antigas.
    # População total, renda e PDV antigo não entram na fórmula oficial atual.
    if "fator_populacao" not in out.columns:
        out["fator_populacao"] = _fator_100_idc_final(out, "populacao") if "_fator_100_idc_final" in globals() else 0
    if "fator_renda" not in out.columns:
        out["fator_renda"] = _fator_100_idc_final(out, "renda_media") if "_fator_100_idc_final" in globals() else 0
    if "fator_pdv" not in out.columns:
        out["fator_pdv"] = out["fator_pdv_total"]
    return out


def simular_idc_expansao(
    peso_pib: float | None = None,
    peso_pop_30_44: float | None = None,
    peso_masculino: float | None = None,
    peso_feminino: float | None = None,
    peso_restaurantes: float | None = None,
    peso_pop_15_29: float | None = None,
    peso_pdv_total: float | None = None,
    estados: list[str] | None = None,
    visao: str = "microrregiao",
    # compatibilidade com parâmetros antigos
    peso_populacao: float | None = None,
    peso_renda: float | None = None,
    peso_pib_per_capita: float | None = None,
    peso_pdv: float | None = None,
    **kwargs,
) -> pd.DataFrame:
    df = calcular_idc_expansao(estados=estados, visao=visao)
    if df is None or df.empty:
        return pd.DataFrame() if df is None else df

    df = _garantir_fatores_idc_simulador(df)

    pesos = {
        "fator_pib": _coalesce_peso(peso_pib, default=25),
        "fator_pop_30_44": _coalesce_peso(peso_pop_30_44, peso_populacao, 40),
        "fator_masculino": _coalesce_peso(peso_masculino, default=10),
        "fator_feminino": _coalesce_peso(peso_feminino, default=0),
        "fator_restaurantes": _coalesce_peso(peso_restaurantes, default=10),
        "fator_pop_15_29": _coalesce_peso(peso_pop_15_29, default=10),
        "fator_pdv_total": _coalesce_peso(peso_pdv_total, peso_pdv, 5),
    }

    # Parâmetros antigos que não fazem parte da fórmula oficial ficam documentados como peso zero efetivo.
    df["peso_renda_ignorado_pct"] = float(peso_renda or 0)
    df["peso_pib_per_capita_ignorado_pct"] = float(peso_pib_per_capita or 0)

    total_pesos = round(sum(pesos.values()), 6)
    df["peso_total_simulador"] = total_pesos

    for fator, peso in pesos.items():
        df[f"peso_{fator.replace('fator_', '')}_pct"] = peso

    if total_pesos != 100.0:
        df["idc_simulado"] = pd.to_numeric(df.get("idc_base"), errors="coerce").fillna(0)
        df["score_simulado"] = pd.to_numeric(df.get("score", df["idc_simulado"]), errors="coerce").fillna(0)
        df["nova_classificacao"] = df.get("classificacao_score", df.get("classificacao", "Monitorar"))
        df["classificacao_simulada"] = df["nova_classificacao"]
        df["diferenca_idc"] = 0.0
        df["diferenca_base_simulado"] = 0.0
        df["status_simulador"] = "bloqueado: soma dos pesos precisa fechar exatamente 100%"
        return _round4_df(df)

    idc_simulado = pd.Series([0.0] * len(df), index=df.index, dtype="float64")
    for fator, peso in pesos.items():
        idc_simulado += pd.to_numeric(df[fator], errors="coerce").fillna(0) * (peso / 100.0)

    df["idc_simulado"] = idc_simulado.clip(lower=0, upper=100)
    df["score_simulado"] = df["idc_simulado"]
    df["nova_classificacao"] = df["score_simulado"].apply(_classificar_score)
    df["classificacao_simulada"] = df["nova_classificacao"]
    df["diferenca_idc"] = df["idc_simulado"] - pd.to_numeric(df.get("idc_base"), errors="coerce").fillna(0)
    df["diferenca_base_simulado"] = df["diferenca_idc"]
    df["status_simulador"] = "ok: IDC simulado com fórmula oficial e pesos fechados em 100%"
    df["formula_idc_simulado"] = (
        "IDC = PIB 25% + População 30-44 40% + Masculino 10% + Feminino 0% "
        "+ Restaurantes 10% + População 15-29 10% + Total PDV 5%"
    )

    return _round4_df(df.sort_values("score_simulado", ascending=False, na_position="last"))


def exportar_bases_expansao_excel(parametros: dict | None = None, estados: list[str] | None = None) -> bytes:
    parametros = parametros or {
        "peso_pib": 25,
        "peso_pop_30_44": 40,
        "peso_masculino": 10,
        "peso_feminino": 0,
        "peso_restaurantes": 10,
        "peso_pop_15_29": 10,
        "peso_pdv_total": 5,
    }
    sheets = {
        "IDC_Completo_Atual": calcular_idc_expansao(estados=estados),
        "Resumo_Estado": carregar_resumo_estado_expansao(estados=estados),
        "Regioes_Economicas": carregar_regioes_economicas_expansao(estados=estados),
        "Microrregiao_Indicadores": carregar_microrregiao_expansao(estados=estados),
        "Perfil_Demografico": carregar_perfil_demografico_expansao(estados=estados),
        "Receita_Categoria": carregar_receita_categoria_expansao(estados=estados),
        "IDC_Simulado": simular_idc_expansao(estados=estados, **parametros),
        "Parametros_Simulador": pd.DataFrame([parametros]),
        "Dicionario": pd.DataFrame([
            {"campo": "idc_base", "descricao": "IDC oficial: PIB 25%, população 30-44 40%, masculino 10%, feminino 0%, restaurantes 10%, população 15-29 10%, total PDV 5%."},
            {"campo": "idc_simulado", "descricao": "IDC recalculado com os pesos do simulador; liberado apenas quando a soma dos pesos fecha 100%."},
            {"campo": "Classe A-E", "descricao": "Reservado para distribuição oficial granular. POF regional N2 fica em colunas regionais de referência."},
            {"campo": "Receita por categoria", "descricao": "Não inventa mercado real. Zera/pendente até importação manual ou fonte comercial identificada."},
        ]),
    }
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            if isinstance(df, pd.DataFrame):
                df.to_excel(writer, index=False, sheet_name=name[:31])
    return output.getvalue()
# IDC_SIMULADOR_CANONICO_FINAL_FIM
=======
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf

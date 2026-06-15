
from __future__ import annotations

from io import BytesIO

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine
from src.services.indicadores_service import carregar_series_dw, listar_indicadores_disponiveis
from src.services.setorial_service import carregar_series_setoriais, carregar_indices_setoriais_atuais


def _relation_exists(conn, relation_name: str) -> bool:
    return bool(conn.execute(text("SELECT to_regclass(:name) IS NOT NULL"), {"name": relation_name}).scalar())


def carregar_radar_economico_ultimo_ano(indicador: str | None = None) -> pd.DataFrame:
    indicadores = listar_indicadores_disponiveis()
    if not indicadores:
        return pd.DataFrame()
    indicador = indicador or indicadores[0]
    df = carregar_series_dw(indicador=indicador)
    if df.empty:
        return df

    df = df.copy()
    df["data"] = pd.to_datetime(df["data"])
    hoje = pd.Timestamp.today().normalize()
    data_inicio = hoje - pd.DateOffset(years=1)
    return df[df["data"] >= data_inicio].sort_values("data")


def resumo_radar_economico_ultimo_ano(indicador: str | None = None) -> dict:
    df = carregar_radar_economico_ultimo_ano(indicador)
    if df.empty:
        return {"ultimo_valor": 0, "ultima_data": None, "variacao_periodo_pct": 0, "tendencia": "Sem dados"}
    df = df.sort_values("data")
    primeiro = float(df["valor"].iloc[0] or 0)
    ultimo = float(df["valor"].iloc[-1] or 0)
    variacao = ((ultimo / primeiro) - 1) * 100 if primeiro else 0
    tendencia = "Alta" if variacao > 2 else "Queda" if variacao < -2 else "Estável"
    return {
        "ultimo_valor": ultimo,
        "ultima_data": df["data"].iloc[-1].date(),
        "variacao_periodo_pct": variacao,
        "tendencia": tendencia,
    }


def carregar_proteinas_graos_unificado(uf: str = "MG", produtos: list[str] | None = None, data_inicio=None, data_fim=None) -> pd.DataFrame:
    df = carregar_series_setoriais(uf=uf, categoria=None, produtos=produtos, data_inicio=data_inicio, data_fim=data_fim)
    if df.empty:
        return df

    df = df.copy()
    df["mes"] = pd.to_datetime(df["mes"], errors="coerce")
    df["valor_medio"] = pd.to_numeric(df["valor_medio"], errors="coerce")
    df = df.dropna(subset=["mes", "valor_medio"]).sort_values(["produto", "mes"])
    if df.empty:
        return df

    df["indice_base100"] = pd.NA
    for produto, idx in df.groupby("produto").groups.items():
        serie = df.loc[idx].sort_values("mes")
        base = serie["valor_medio"].dropna()
        if base.empty or base.iloc[0] == 0:
            continue
        df.loc[serie.index, "indice_base100"] = (serie["valor_medio"] / base.iloc[0]) * 100

    df["variacao_mensal_pct"] = df.groupby("produto")["valor_medio"].pct_change() * 100

    def _acumulada(s):
        clean = pd.to_numeric(s, errors="coerce").dropna()
        if clean.empty or clean.iloc[0] == 0:
            return pd.Series([pd.NA] * len(s), index=s.index)
        return ((pd.to_numeric(s, errors="coerce") / clean.iloc[0]) - 1) * 100

    df["variacao_acumulada_pct"] = df.groupby("produto")["valor_medio"].transform(_acumulada)

    for col in ["valor_medio", "indice_base100", "variacao_mensal_pct", "variacao_acumulada_pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")

    return df


def carregar_base_ceagesp_historico() -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        if not _relation_exists(conn, "app.fato_ceagesp_pescados"):
            return pd.DataFrame(columns=[
                "data_coleta", "data_referencia", "produto", "classificacao", "unidade",
                "preco_minimo", "preco_comum", "preco_maximo", "fonte", "hash_carga"
            ])
        return pd.read_sql(text("""
            SELECT data_coleta, data_referencia, produto, classificacao, unidade,
                   preco_minimo, preco_comum, preco_maximo, fonte, url_fonte, hash_carga
            FROM app.fato_ceagesp_pescados
            ORDER BY data_referencia DESC, produto
        """), conn)


def carregar_base_compra_manual() -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        if not _relation_exists(conn, "app.fato_compra_manual"):
            return pd.DataFrame()
        return pd.read_sql(text("SELECT * FROM app.fato_compra_manual ORDER BY data DESC NULLS LAST, id DESC"), conn)


def carregar_base_previa_vendedores() -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        if _relation_exists(conn, "app.fato_previa_vendedores"):
            df_manual = pd.read_sql(text("SELECT * FROM app.fato_previa_vendedores ORDER BY data_venda DESC NULLS LAST, id DESC"), conn)
            if not df_manual.empty:
                return df_manual

        if not _relation_exists(conn, "app.vw_vendas_analitica"):
            return pd.DataFrame(columns=[
                "vendedor", "produto", "preco", "data_venda", "quantidade_vendida",
                "receita_total", "cliente", "regiao", "observacao"
            ])

        return pd.read_sql(text("""
            SELECT
                COALESCE(vendedor, 'Sem vendedor') AS vendedor,
                COALESCE(produto, 'Sem produto') AS produto,
                preco_medio_kg AS preco,
                data AS data_venda,
                quantidade AS quantidade_vendida,
                valor_venda AS receita_total,
                cliente,
                regiao_comercial AS regiao,
                'Origem: vendas internas' AS observacao
            FROM app.vw_vendas_analitica
            ORDER BY data DESC
            LIMIT 5000
        """), conn)


def carregar_diagnostico_v2_plano() -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        if not _relation_exists(conn, "app.vw_diagnostico_v2_plano"):
            return pd.DataFrame(columns=["item", "qtd_preenchida", "qtd_total", "status"])
        return pd.read_sql(text("SELECT * FROM app.vw_diagnostico_v2_plano ORDER BY item"), conn)


def exportar_bases_previsao_mercado_excel(indicador: str | None = None, produtos: list[str] | None = None) -> bytes:
    sheets = {
        "Radar_Economico_1Ano": carregar_radar_economico_ultimo_ano(indicador),
        "Proteinas_Graos": carregar_proteinas_graos_unificado(produtos=produtos),
        "Indices_Setoriais": carregar_indices_setoriais_atuais(uf="MG"),
        "CEAGESP_Historico": carregar_base_ceagesp_historico(),
        "Base_Compra": carregar_base_compra_manual(),
        "Base_Vendedores": carregar_base_previa_vendedores(),
        "Dicionario": pd.DataFrame([
            {"base": "Radar_Economico_1Ano", "descricao": "Indicadores macroeconômicos do último ano"},
            {"base": "Proteinas_Graos", "descricao": "Séries unificadas de proteínas, grãos e insumos"},
            {"base": "CEAGESP_Historico", "descricao": "Histórico CEAGESP quando carregado por script"},
            {"base": "Base_Compra", "descricao": "Base de compra manual/histórica"},
            {"base": "Base_Vendedores", "descricao": "Vendas/previsões comerciais por vendedor"},
        ]),
    }

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, index=False, sheet_name=name[:31])
    return output.getvalue()



def carregar_importacao_manual_resumo() -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        if not _relation_exists(conn, "app.vw_importacao_manual_resumo"):
            return pd.DataFrame(columns=["tipo_importacao", "status", "qtd_execucoes", "ultima_execucao", "registros_processados"])
        return pd.read_sql(text("SELECT * FROM app.vw_importacao_manual_resumo ORDER BY tipo_importacao, status"), conn)



def carregar_base_compra_resumo() -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        if not _relation_exists(conn, "app.vw_compra_manual_resumo"):
            return pd.DataFrame()
        return pd.read_sql(text("SELECT * FROM app.vw_compra_manual_resumo"), conn)


def carregar_previa_vendedores_resumo() -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        if not _relation_exists(conn, "app.vw_previa_vendedores_resumo"):
            return pd.DataFrame()
        return pd.read_sql(text("SELECT * FROM app.vw_previa_vendedores_resumo"), conn)



# ============================================================
# HOTFIX — CEPEA x CEAGESP em Análise Previsão de Mercado
# ============================================================

def carregar_cepea_series(produtos: list[str] | None = None) -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        if not _relation_exists(conn, "dw.fato_indicador_setorial"):
            return pd.DataFrame()

        sql = """
            SELECT
                data,
                fonte,
                indicador,
                categoria,
                subcategoria,
                produto,
                uf,
                valor,
                unidade,
                periodicidade
            FROM dw.fato_indicador_setorial
            WHERE fonte ILIKE '%CEPEA%'
            ORDER BY data DESC, produto
        """
        df = pd.read_sql(text(sql), conn)

    if produtos and not df.empty and "produto" in df.columns:
        df = df[df["produto"].astype(str).isin(produtos)].copy()

    return df


def carregar_comparacao_cepea_ceagesp(produtos: list[str] | None = None, fontes: list[str] | None = None) -> pd.DataFrame:
    fontes = fontes or ["CEPEA", "CEAGESP"]
    frames = []

    if "CEPEA" in fontes:
        df_cepea = carregar_cepea_series(produtos=produtos)
        if not df_cepea.empty:
            tmp = df_cepea.rename(columns={"data": "data_referencia", "valor": "preco"})
            tmp["origem"] = "CEPEA"
            tmp["preco_tipo"] = tmp.get("indicador", "CEPEA")
            frames.append(tmp[["data_referencia", "origem", "produto", "preco", "unidade", "preco_tipo"]])

    if "CEAGESP" in fontes:
        df_ceagesp = carregar_base_ceagesp_historico()
        if not df_ceagesp.empty:
            tmp = df_ceagesp.rename(columns={"preco_comum": "preco"})
            tmp["origem"] = "CEAGESP"
            tmp["preco_tipo"] = tmp.get("classificacao", "Preço comum")
            if produtos and "produto" in tmp.columns:
                tmp = tmp[tmp["produto"].astype(str).isin(produtos)].copy()
            frames.append(tmp[["data_referencia", "origem", "produto", "preco", "unidade", "preco_tipo"]])

    if not frames:
        return pd.DataFrame()

    out = pd.concat(frames, ignore_index=True)
    out["data_referencia"] = pd.to_datetime(out["data_referencia"], errors="coerce")
    out["preco"] = pd.to_numeric(out["preco"], errors="coerce")
    out = out.dropna(subset=["data_referencia", "preco"])
    return out.sort_values(["data_referencia", "origem", "produto"], ascending=[True, True, True])


def carregar_receita_manual_expansao_resumo() -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        if not _relation_exists(conn, "app.vw_receita_manual_expansao_resumo"):
            return pd.DataFrame()
        return pd.read_sql(text("SELECT * FROM app.vw_receita_manual_expansao_resumo"), conn)


def carregar_receita_manual_expansao_base() -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        if not _relation_exists(conn, "app.vw_receita_manual_expansao"):
            return pd.DataFrame()
        return pd.read_sql(text("SELECT * FROM app.vw_receita_manual_expansao"), conn)

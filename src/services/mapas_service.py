
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
from sqlalchemy import text

from src.database.connection import get_engine


UF_TO_CODIGO = {
    "RO": "11", "AC": "12", "AM": "13", "RR": "14", "PA": "15", "AP": "16", "TO": "17",
    "MA": "21", "PI": "22", "CE": "23", "RN": "24", "PB": "25", "PE": "26", "AL": "27", "SE": "28", "BA": "29",
    "MG": "31", "ES": "32", "RJ": "33", "SP": "35",
    "PR": "41", "SC": "42", "RS": "43",
    "MS": "50", "MT": "51", "GO": "52", "DF": "53",
}


# Paleta estável para compatibilidade com mapas Folium antigos e testes.
REGIAO_CORES = {
    "Central": "#1f77b4",
    "Grande BH": "#1f77b4",
    "Zona da Mata": "#ff7f0e",
    "Triângulo/Alto Paranaíba": "#2ca02c",
    "Vale do Aço/Rio Doce": "#d62728",
    "Sul de MG": "#9467bd",
    "Oeste de MG": "#8c564b",
    "Campo das Vertentes": "#e377c2",
    "Central Mineira": "#7f7f7f",
    "Noroeste de MG": "#bcbd22",
    "Norte de MG": "#17becf",
    "Jequitinhonha/Mucuri": "#aec7e8",
    "Sem região": "#d9d9d9",
}


def _linear_colormap(nome: str = "viridis", vmin: float = 0, vmax: float = 100):
    """Compatibilidade com versões antigas baseadas em Folium/branca.

    Retorna um objeto chamável. Quando branca não está instalado, retorna uma
    função simples que preserva a interface esperada pelos testes e pelo app.
    """
    try:
        from branca.colormap import linear

        nome_norm = str(nome or "viridis").lower().replace("-", "_")
        aliases = {
            "viridis": "viridis",
            "ylgnbu": "YlGnBu_09",
            "ylgnbu_09": "YlGnBu_09",
        }
        attr = aliases.get(nome_norm, nome_norm)
        cmap = getattr(linear, attr, None)
        if cmap is None:
            cmap = linear.viridis
        return cmap.scale(vmin, vmax)
    except Exception:
        def _fallback(value):
            return "#808080"

        return _fallback


def normalizar_codarea(value: Any) -> str:
    if value is None:
        return ""

    text_value = str(value).strip()
    if text_value.endswith(".0"):
        text_value = text_value[:-2]

    if text_value and not text_value.isdigit():
        digits = "".join(ch for ch in text_value if ch.isdigit())
        if digits:
            text_value = digits

    return text_value


def _relation_exists(conn, relation_name: str) -> bool:
    return bool(
        conn.execute(
            text("SELECT to_regclass(:relation_name) IS NOT NULL"),
            {"relation_name": relation_name},
        ).scalar()
    )


def _safe_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in cols:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def _safe_size_column(df: pd.DataFrame, preferred: str, fallback: str = "qtd_municipios") -> str:
    """
    Treemap precisa de coluna de tamanho positiva.
    Se a métrica selecionada estiver toda zero, usa uma coluna fallback estável.
    """
    if preferred not in df.columns:
        return fallback

    values = pd.to_numeric(df[preferred], errors="coerce").fillna(0)
    if values.sum() <= 0:
        return fallback

    return preferred


def dados_mapa_brasil_ufs() -> pd.DataFrame:
    """
    Dados resumidos por UF para visualização simples em blocos.

    Não depende de GeoJSON nem internet.
    """
    engine = get_engine()
    sql = """
        WITH geo AS (
            SELECT
                uf,
                nome_uf,
                regiao_brasil,
                COUNT(*) AS qtd_municipios
            FROM dw.dim_geografia
            WHERE uf IS NOT NULL
            GROUP BY uf, nome_uf, regiao_brasil
        ), vendas AS (
            SELECT
                uf,
                COALESCE(SUM(valor_venda), 0) AS faturamento,
                COALESCE(SUM(volume_kg), 0) AS volume_kg,
                COUNT(DISTINCT id_cliente) AS qtd_clientes
            FROM dw.fato_vendas
            WHERE uf IS NOT NULL
            GROUP BY uf
        )
        SELECT
            geo.uf,
            geo.nome_uf,
            COALESCE(geo.regiao_brasil, 'Brasil') AS regiao_brasil,
            geo.qtd_municipios,
            COALESCE(vendas.faturamento, 0) AS faturamento,
            COALESCE(vendas.volume_kg, 0) AS volume_kg,
            COALESCE(vendas.qtd_clientes, 0) AS qtd_clientes
        FROM geo
        LEFT JOIN vendas ON vendas.uf = geo.uf
        ORDER BY geo.uf
    """
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn)

    if df.empty:
        return df

    df["codigo_uf"] = df["uf"].map(UF_TO_CODIGO).fillna("")
    df = _safe_numeric(df, ["qtd_municipios", "faturamento", "volume_kg", "qtd_clientes"])
    df["faturamento_por_municipio"] = df["faturamento"] / df["qtd_municipios"].replace({0: pd.NA})
    df["faturamento_por_municipio"] = df["faturamento_por_municipio"].fillna(0)
    return df


def dados_mapa_mg_regioes() -> pd.DataFrame:
    """
    Dados por município/região comercial para visualização simples em blocos.

    Não depende de GeoJSON nem internet.
    """
    engine = get_engine()
    sql_base = """
        SELECT
            g.codigo_ibge,
            g.uf,
            g.nome_uf,
            g.municipio,
            g.mesorregiao,
            g.microrregiao,
            g.regiao_comercial
        FROM dw.dim_geografia g
        WHERE g.uf = 'MG'
        ORDER BY g.regiao_comercial, g.municipio
    """

    sql_com_potencial = """
        SELECT
            g.codigo_ibge,
            g.uf,
            g.nome_uf,
            g.municipio,
            g.mesorregiao,
            g.microrregiao,
            g.regiao_comercial,
            COALESCE(p.populacao_estimada, 0) AS populacao_regiao,
            COALESCE(p.faturamento, 0) AS faturamento_regiao,
            COALESCE(p.volume_kg, 0) AS volume_kg_regiao,
            COALESCE(p.qtd_clientes, 0) AS clientes_regiao,
            COALESCE(p.score_potencial, 0) AS score_potencial,
            COALESCE(p.cenario_1_10, 0) AS cenario_1_10,
            COALESCE(p.confianca, 0) AS confianca
        FROM dw.dim_geografia g
        LEFT JOIN app.mv_potencial_regional_atual p
            ON p.uf = g.uf
           AND p.regiao_comercial = g.regiao_comercial
        WHERE g.uf = 'MG'
        ORDER BY g.regiao_comercial, g.municipio
    """

    with engine.begin() as conn:
        if _relation_exists(conn, "app.mv_potencial_regional_atual"):
            df = pd.read_sql(text(sql_com_potencial), conn)
        else:
            df = pd.read_sql(text(sql_base), conn)

    if df.empty:
        return df

    df["codigo_ibge"] = df["codigo_ibge"].apply(normalizar_codarea)
    df["regiao_comercial"] = df["regiao_comercial"].fillna("Sem região")

    numeric_cols = [
        "populacao_regiao",
        "faturamento_regiao",
        "volume_kg_regiao",
        "clientes_regiao",
        "score_potencial",
        "cenario_1_10",
        "confianca",
    ]
    df = _safe_numeric(df, numeric_cols)

    return df


def fig_mapa_brasil_uf(df: pd.DataFrame, coluna_valor: str, titulo: str):
    """
    Mapa simples em blocos por UF.

    A área dos blocos fica sempre por quantidade de municípios para evitar erro
    quando Faturamento/Volume/Clientes ainda estão zerados.
    A métrica selecionada controla a cor.
    """
    if df.empty:
        return None

    df = df.copy()
    df = _safe_numeric(
        df,
        [
            "qtd_municipios",
            "faturamento",
            "volume_kg",
            "qtd_clientes",
            "faturamento_por_municipio",
        ],
    )

    if coluna_valor not in df.columns:
        coluna_valor = "qtd_municipios"

    size_col = "qtd_municipios"
    color_col = coluna_valor

    # Se a métrica escolhida estiver toda zerada, mantém a cor por municípios
    # e preserva a métrica zerada no hover.
    if pd.to_numeric(df[color_col], errors="coerce").fillna(0).sum() <= 0:
        color_col = "qtd_municipios"

    fig = px.treemap(
        df,
        path=["regiao_brasil", "uf"],
        values=size_col,
        color=color_col,
        hover_name="nome_uf",
        hover_data={
            "uf": True,
            "qtd_municipios": True,
            "faturamento": ":,.2f",
            "volume_kg": ":,.2f",
            "qtd_clientes": True,
            "faturamento_por_municipio": ":,.2f",
        },
        title=titulo,
        color_continuous_scale="Viridis",
    )

    fig.update_traces(
        textinfo="label+value",
        marker=dict(line=dict(width=2)),
    )
    fig.update_layout(
        height=520,
        margin=dict(t=60, l=10, r=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _resumo_mg_por_regiao(df: pd.DataFrame) -> pd.DataFrame:
    resumo = (
        df.groupby("regiao_comercial", as_index=False)
        .agg(
            qtd_municipios=("codigo_ibge", "nunique"),
            populacao_regiao=("populacao_regiao", "max"),
            faturamento_regiao=("faturamento_regiao", "max"),
            volume_kg_regiao=("volume_kg_regiao", "max"),
            clientes_regiao=("clientes_regiao", "max"),
            score_potencial=("score_potencial", "max"),
            cenario_1_10=("cenario_1_10", "max"),
            confianca=("confianca", "max"),
        )
    )

    return _safe_numeric(
        resumo,
        [
            "qtd_municipios",
            "populacao_regiao",
            "faturamento_regiao",
            "volume_kg_regiao",
            "clientes_regiao",
            "score_potencial",
            "cenario_1_10",
            "confianca",
        ],
    )


def fig_mapa_mg_regioes(df: pd.DataFrame, titulo: str = "Mapa comercial simplificado — MG"):
    """
    Mapa simples em blocos por região comercial de MG.
    """
    if df.empty:
        return None

    resumo = _resumo_mg_por_regiao(df).sort_values("qtd_municipios", ascending=False)

    fig = px.treemap(
        resumo,
        path=["regiao_comercial"],
        values="qtd_municipios",
        color="regiao_comercial",
        hover_data={
            "qtd_municipios": True,
            "populacao_regiao": ":,.0f",
            "faturamento_regiao": ":,.2f",
            "volume_kg_regiao": ":,.2f",
            "clientes_regiao": True,
            "score_potencial": ":.2f",
            "cenario_1_10": True,
            "confianca": ":.2f",
        },
        title=titulo,
    )

    fig.update_traces(
        textinfo="label+value",
        marker=dict(line=dict(width=3)),
    )
    fig.update_layout(
        height=430,
        margin=dict(t=60, l=10, r=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


def fig_mapa_mg_metrica(df: pd.DataFrame, coluna_valor: str, titulo: str):
    """
    Blocos por região comercial usando a métrica escolhida como cor.
    O tamanho permanece por quantidade de municípios para evitar erro com valores zerados.
    """
    if df.empty:
        return None

    resumo = _resumo_mg_por_regiao(df)

    if coluna_valor not in resumo.columns:
        coluna_valor = "score_potencial"

    color_col = coluna_valor
    if pd.to_numeric(resumo[color_col], errors="coerce").fillna(0).sum() <= 0:
        color_col = "qtd_municipios"

    resumo = resumo.sort_values(color_col, ascending=False)

    fig = px.treemap(
        resumo,
        path=["regiao_comercial"],
        values="qtd_municipios",
        color=color_col,
        hover_data={
            "qtd_municipios": True,
            "populacao_regiao": ":,.0f",
            "faturamento_regiao": ":,.2f",
            "volume_kg_regiao": ":,.2f",
            "clientes_regiao": True,
            "score_potencial": ":.2f",
            "cenario_1_10": True,
            "confianca": ":.2f",
        },
        title=titulo,
        color_continuous_scale="Viridis",
    )

    fig.update_traces(
        textinfo="label+value",
        marker=dict(line=dict(width=3)),
    )
    fig.update_layout(
        height=430,
        margin=dict(t=60, l=10, r=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def regiao_por_codigo_ibge(df_mapa: pd.DataFrame, codigo_ibge: str | None) -> str | None:
    if not codigo_ibge or df_mapa.empty:
        return None

    match = df_mapa[df_mapa["codigo_ibge"].astype(str).apply(normalizar_codarea) == normalizar_codarea(codigo_ibge)]
    if match.empty:
        return None

    return str(match.iloc[0]["regiao_comercial"])


# Compatibilidade com versões anteriores que chamavam mapas reais/Folium.
def carregar_geojson_brasil_ufs(force: bool = False) -> dict:
    return {}


def carregar_geojson_mg_municipios(force: bool = False) -> dict:
    return {}


def diagnostico_geojson(geojson: dict) -> dict:
    return {"qtd_features": 0, "primeiros_codigos": [], "bounds_lonlat": None}


def extrair_codarea_folium(event: Any) -> str | None:
    return None


def extrair_location_plotly_selection(event: Any) -> str | None:
    return None


def mapa_folium_brasil_uf(df: pd.DataFrame, geojson: dict, coluna_valor: str, titulo: str):
    return fig_mapa_brasil_uf(df, coluna_valor, titulo)


def mapa_folium_mg_regioes(df: pd.DataFrame, geojson: dict, titulo: str = "Mapa comercial simplificado — MG"):
    return fig_mapa_mg_regioes(df, titulo)


def mapa_folium_mg_metrica(df: pd.DataFrame, geojson: dict, coluna_valor: str, titulo: str):
    return fig_mapa_mg_metrica(df, coluna_valor, titulo)

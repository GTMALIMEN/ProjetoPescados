import pandas as pd
from sqlalchemy import text
from src.database.connection import get_engine


def carregar_indices_setoriais_atuais(uf: str = "MG") -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            data_referencia,
            uf,
            indice,
            score,
            cenario_1_10,
            confianca,
            metodo,
            data_calculo
        FROM app.mv_indice_setorial_atual
        WHERE uf = :uf
        ORDER BY indice
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"uf": uf})


def carregar_alertas_setoriais_atuais(uf: str = "MG") -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            data_referencia,
            uf,
            tipo_alerta,
            severidade,
            titulo,
            mensagem,
            score_relacionado,
            status,
            data_criacao
        FROM app.mv_alerta_setorial_atual
        WHERE uf = :uf
        ORDER BY
            CASE severidade
                WHEN 'critico' THEN 1
                WHEN 'alto' THEN 2
                WHEN 'medio' THEN 3
                ELSE 4
            END,
            data_referencia DESC
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"uf": uf})


def carregar_series_setoriais(
    uf: str = "MG",
    categoria: str | None = None,
    produtos: list[str] | None = None,
    data_inicio=None,
    data_fim=None,
) -> pd.DataFrame:
    engine = get_engine()

    filtros = ["COALESCE(NULLIF(uf, ''), 'BR') IN (:uf, 'BR')"]
    params = {"uf": uf}

    if categoria:
        filtros.append("categoria = :categoria")
        params["categoria"] = categoria

    if produtos:
        filtros.append("produto = ANY(:produtos)")
        params["produtos"] = produtos

    if data_inicio:
        filtros.append("mes >= :data_inicio")
        params["data_inicio"] = data_inicio

    if data_fim:
        filtros.append("mes <= :data_fim")
        params["data_fim"] = data_fim

    where_clause = " AND ".join(filtros)

    sql = f"""
        SELECT
            mes,
            uf,
            categoria,
            subcategoria,
            produto,
            indicador,
            unidade,
            valor_medio
        FROM app.vw_indicador_setorial_mensal
        WHERE {where_clause}
        ORDER BY mes, categoria, produto
    """

    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def listar_produtos_setoriais(uf: str = "MG", categoria: str | None = None) -> list[str]:
    engine = get_engine()

    filtros = ["COALESCE(NULLIF(uf, ''), 'BR') IN (:uf, 'BR')"]
    params = {"uf": uf}

    if categoria:
        filtros.append("categoria = :categoria")
        params["categoria"] = categoria

    where_clause = " AND ".join(filtros)

    sql = f"""
        SELECT DISTINCT produto
        FROM app.vw_indicador_setorial_mensal
        WHERE {where_clause}
          AND produto IS NOT NULL
          AND produto <> ''
        ORDER BY produto
    """

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params=params)

    return df["produto"].dropna().tolist()


def listar_categorias_setoriais(uf: str = "MG") -> list[str]:
    engine = get_engine()

    sql = """
        SELECT DISTINCT categoria
        FROM app.vw_indicador_setorial_mensal
        WHERE COALESCE(NULLIF(uf, ''), 'BR') IN (:uf, 'BR')
          AND categoria IS NOT NULL
          AND categoria <> ''
        ORDER BY categoria
    """

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"uf": uf})

    return df["categoria"].dropna().tolist()


def carregar_comparacao_proteinas(
    uf: str = "MG",
    produtos: list[str] | None = None,
    produto_base: str | None = None,
    data_inicio=None,
    data_fim=None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Retorna:
    - df_long: séries originais filtradas;
    - df_base100: séries normalizadas com base 100;
    - df_razao: razão produto/produto_base.
    """
    df = carregar_series_setoriais(
        uf=uf,
        categoria="proteina",
        produtos=produtos,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )

    if df.empty:
        return df, pd.DataFrame(), pd.DataFrame()

    df = df.copy()
    df["mes"] = pd.to_datetime(df["mes"])

    pivot = df.pivot_table(index="mes", columns="produto", values="valor_medio", aggfunc="mean").sort_index()

    # Base 100
    base100 = pivot.copy()
    for col in base100.columns:
        serie = base100[col].dropna()
        if serie.empty or serie.iloc[0] == 0:
            base100[col] = None
        else:
            base100[col] = (base100[col] / serie.iloc[0]) * 100

    df_base100 = base100.reset_index().melt(
        id_vars="mes",
        var_name="produto",
        value_name="indice_base100",
    )

    # Razão contra base
    df_razao = pd.DataFrame()
    if produto_base and produto_base in pivot.columns:
        razoes = pd.DataFrame(index=pivot.index)
        for col in pivot.columns:
            if col == produto_base:
                continue
            razoes[f"{col} / {produto_base}"] = pivot[col] / pivot[produto_base]

        if not razoes.empty:
            df_razao = razoes.reset_index().melt(
                id_vars="mes",
                var_name="comparacao",
                value_name="razao",
            )

    return df, df_base100, df_razao


def resumo_setorial(uf: str = "MG") -> dict:
    engine = get_engine()
    sql = """
        SELECT
            COUNT(*) AS qtd_registros,
            COUNT(DISTINCT indicador) AS qtd_indicadores,
            COUNT(DISTINCT produto) AS qtd_produtos,
            MIN(data) AS primeira_data,
            MAX(data) AS ultima_data
        FROM dw.fato_indicador_setorial
        WHERE COALESCE(NULLIF(uf, ''), 'BR') IN (:uf, 'BR')
    """
    with engine.begin() as conn:
        row = conn.execute(text(sql), {"uf": uf}).mappings().first()
    return dict(row or {})

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import hashlib
import re
import unicodedata
from typing import Any

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


@dataclass(frozen=True)
class ImportConfig:
    tipo: str
    label: str
    table: str
    columns: list[str]
    required: list[str]
    date_cols: list[str]
    numeric_cols: list[str]
    description: str


CONFIGS: dict[str, ImportConfig] = {
    "mercado_privado": ImportConfig(
        tipo="mercado_privado",
        label="Scanntech / Total Mercado",
        table="app.fato_mercado_privado",
        columns=[
            "data_competencia", "uf", "cidade", "microrregiao", "categoria", "produto", "marca", "ean", "canal",
            "valor_mercado", "volume_mercado", "preco_medio", "qtd_lojas", "fonte"
        ],
        required=["data_competencia", "uf", "microrregiao", "categoria", "valor_mercado"],
        date_cols=["data_competencia"],
        numeric_cols=["valor_mercado", "volume_mercado", "preco_medio", "qtd_lojas"],
        description="Mercado privado/sell-out por microrregião, categoria e produto. Alimenta curva de mercado, correlação e IDC ajustado.",
    ),
    "curva_mercado": ImportConfig(
        tipo="curva_mercado",
        label="Curva de Mercado por Produto/Categoria",
        table="app.fato_curva_mercado_categoria",
        columns=["data_competencia", "uf", "cidade", "microrregiao", "categoria", "produto", "valor", "volume", "preco_medio", "fonte"],
        required=["data_competencia", "uf", "microrregiao", "categoria", "valor"],
        date_cols=["data_competencia"],
        numeric_cols=["valor", "volume", "preco_medio"],
        description="Curva mensal de mercado quando vier em arquivo separado da base Scanntech/total mercado.",
    ),
    "key_account": ImportConfig(
        tipo="key_account",
        label="Key Account / Endereços de Lojas",
        table="app.dim_key_account_loja",
        columns=[
            "grupo_key_account", "cliente", "cnpj", "loja", "endereco", "numero", "bairro", "cidade", "uf", "cep",
            "latitude", "longitude", "canal", "status"
        ],
        required=["grupo_key_account", "loja", "cidade", "uf"],
        date_cols=[],
        numeric_cols=["latitude", "longitude"],
        description="Endereços e lojas Key Account. Alimenta cobertura comercial, mapa, densidade por população e gráfico IBGE.",
    ),
    "ceagesp_pescados": ImportConfig(
        tipo="ceagesp_pescados",
        label="CEAGESP Pescados",
        table="app.fato_ceagesp_pescados",
        columns=["data_referencia", "produto", "classificacao", "unidade", "preco_minimo", "preco_comum", "preco_maximo", "fonte"],
        required=["data_referencia", "produto", "preco_comum"],
        date_cols=["data_referencia"],
        numeric_cols=["preco_minimo", "preco_comum", "preco_maximo"],
        description="Histórico CEAGESP manual/controlado. Alimenta comparação CEPEA x CEAGESP e referência de preço.",
    ),
    "compra_manual": ImportConfig(
        tipo="compra_manual",
        label="Base de Compra Manual",
        table="app.fato_compra_manual",
        columns=["data", "fornecedor", "marca", "produto", "categoria", "preco_compra", "quantidade_comprada", "unidade", "observacao"],
        required=["data", "produto", "preco_compra"],
        date_cols=["data"],
        numeric_cols=["preco_compra", "quantidade_comprada"],
        description="Preço real de compra por produto/marca/fornecedor. Alimenta margem, comparação com CEPEA/CEAGESP e previsão futura.",
    ),
    "receita_expansao": ImportConfig(
        tipo="receita_expansao",
        label="Receita/Vendas Expansão",
        table="app.fato_receita_manual_expansao",
        columns=["parceiro", "cidade", "estado", "data_competencia", "grupo_produto", "vlr_total_liquido"],
        required=["cidade", "estado", "data_competencia", "grupo_produto", "vlr_total_liquido"],
        date_cols=["data_competencia"],
        numeric_cols=["vlr_total_liquido"],
        description="Venda interna/receita por cidade e grupo de produto. Alimenta receita real por categoria, over/under share e margin pool.",
    ),
    "previa_vendedores": ImportConfig(
        tipo="previa_vendedores",
        label="Prévia Vendedores",
        table="app.fato_previa_vendedores",
        columns=["vendedor", "produto", "preco", "data_venda", "quantidade_vendida", "receita_total", "cliente", "regiao", "observacao"],
        required=["vendedor", "produto", "data_venda", "quantidade_vendida"],
        date_cols=["data_venda"],
        numeric_cols=["preco", "quantidade_vendida", "receita_total"],
        description="Prévia comercial dos vendedores. Alimenta pipeline de venda e projeções futuras.",
    ),
}

ALIASES = {
    "data": "data",
    "data venda": "data_venda",
    "data_venda": "data_venda",
    "data competencia": "data_competencia",
    "data_competencia": "data_competencia",
    "data cotacao": "data_referencia",
    "data_cotacao": "data_referencia",
    "estado": "estado",
    "uf": "uf",
    "vlr total liquido": "vlr_total_liquido",
    "valor total liquido": "vlr_total_liquido",
    "vlr_total_liquido": "vlr_total_liquido",
    "valor mercado": "valor_mercado",
    "valor_mercado": "valor_mercado",
    "volume mercado": "volume_mercado",
    "volume_mercado": "volume_mercado",
    "preco medio": "preco_medio",
    "preco_medio": "preco_medio",
    "preço médio": "preco_medio",
    "qtd lojas": "qtd_lojas",
    "qtd_lojas": "qtd_lojas",
    "grupo produto": "grupo_produto",
    "grupo_produto": "grupo_produto",
    "preco compra": "preco_compra",
    "preco_compra": "preco_compra",
    "preço compra": "preco_compra",
    "quantidade comprada": "quantidade_comprada",
    "quantidade_comprada": "quantidade_comprada",
    "quantidade vendida": "quantidade_vendida",
    "quantidade_vendida": "quantidade_vendida",
    "receita total": "receita_total",
    "receita_total": "receita_total",
    "key account": "grupo_key_account",
    "grupo key account": "grupo_key_account",
    "grupo_key_account": "grupo_key_account",
}


def _slug(texto: str) -> str:
    texto = str(texto or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-z0-9]+", " ", texto).strip()
    texto = re.sub(r"\s+", "_", texto)
    return texto


def _canonical_col(col: str) -> str:
    raw = str(col or "").strip()
    key_space = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii").lower()
    key_space = re.sub(r"[^a-z0-9]+", " ", key_space).strip()
    if key_space in ALIASES:
        return ALIASES[key_space]
    slug = _slug(raw)
    return ALIASES.get(slug, slug)


def configs_importacao() -> pd.DataFrame:
    return pd.DataFrame([
        {"tipo": c.tipo, "base": c.label, "tabela_destino": c.table, "colunas_obrigatorias": ", ".join(c.required), "descricao": c.description}
        for c in CONFIGS.values()
    ])


def gerar_template_excel(tipo: str) -> bytes:
    cfg = CONFIGS[tipo]
    exemplo = {col: None for col in cfg.columns}
    # exemplos mínimos para facilitar o usuário
    if tipo in {"mercado_privado", "curva_mercado"}:
        exemplo.update({"data_competencia": "2026-01-01", "uf": "MG", "microrregiao": "Belo Horizonte", "categoria": "Tilápia", "produto": "Tilápia", "valor_mercado": 100000, "volume_mercado": 5000, "preco_medio": 20, "fonte": "Scanntech"})
    elif tipo == "key_account":
        exemplo.update({"grupo_key_account": "Grupo Exemplo", "cliente": "Cliente Exemplo", "loja": "Loja 01", "cidade": "Belo Horizonte", "uf": "MG"})
    elif tipo == "receita_expansao":
        exemplo.update({"parceiro": "Cliente Exemplo", "cidade": "Belo Horizonte", "estado": "MG", "data_competencia": "2026-01-01", "grupo_produto": "Tilápia", "vlr_total_liquido": 10000})
    elif tipo == "ceagesp_pescados":
        exemplo.update({"data_referencia": "2026-01-01", "produto": "Tilápia", "classificacao": "Comum", "unidade": "kg", "preco_comum": 20, "fonte": "CEAGESP"})
    elif tipo == "compra_manual":
        exemplo.update({"data": "2026-01-01", "fornecedor": "Fornecedor", "marca": "Marca", "produto": "Tilápia", "categoria": "Pescados", "preco_compra": 18, "quantidade_comprada": 100})
    elif tipo == "previa_vendedores":
        exemplo.update({"vendedor": "Vendedor", "produto": "Tilápia", "data_venda": "2026-01-01", "quantidade_vendida": 100, "preco": 22, "receita_total": 2200})

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([exemplo]).to_excel(writer, index=False, sheet_name="Modelo")
        pd.DataFrame([
            {"coluna": col, "obrigatoria": "SIM" if col in cfg.required else "NÃO"}
            for col in cfg.columns
        ]).to_excel(writer, index=False, sheet_name="Dicionario")
    return output.getvalue()


def _ler_arquivo(uploaded_file: Any) -> pd.DataFrame:
    name = getattr(uploaded_file, "name", "arquivo")
    if name.lower().endswith(".csv"):
        try:
            return pd.read_csv(uploaded_file, sep=None, engine="python", encoding="utf-8-sig")
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, sep=None, engine="python", encoding="latin1")
    return pd.read_excel(uploaded_file)


def validar_base(tipo: str, df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    cfg = CONFIGS[tipo]
    erros: list[str] = []
    if df is None or df.empty:
        return pd.DataFrame(), ["Arquivo vazio."]

    out = df.copy()
    out.columns = [_canonical_col(c) for c in out.columns]
    out = out.loc[:, ~out.columns.duplicated()]

    faltantes = [c for c in cfg.required if c not in out.columns]
    if faltantes:
        erros.append("Colunas obrigatórias ausentes: " + ", ".join(faltantes))

    for col in cfg.columns:
        if col not in out.columns:
            out[col] = None

    out = out[cfg.columns].copy()

    # Datas
    for col in cfg.date_cols:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce").dt.date
            if col in cfg.required and out[col].isna().all():
                erros.append(f"Coluna de data inválida ou vazia: {col}")

    # Números
    for col in cfg.numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    # UF/cidade/microrregião
    for col in ["uf", "estado"]:
        if col in out.columns:
            out[col] = out[col].astype(str).str.strip().str.upper().replace({"NAN": None, "NONE": None, "": None})

    for col in ["cidade", "microrregiao", "categoria", "produto", "marca", "canal", "fonte", "grupo_produto"]:
        if col in out.columns:
            out[col] = out[col].where(out[col].isna(), out[col].astype(str).str.strip())

    # Receita expansão usa estado, não uf.
    if tipo == "receita_expansao" and "estado" in out.columns:
        out["estado"] = out["estado"].astype(str).str.strip().str.upper()

    # Remove linhas 100% vazias.
    out = out.dropna(how="all")

    # Validação de obrigatórios linha a linha.
    for col in cfg.required:
        if col in out.columns and out[col].isna().any():
            qtd = int(out[col].isna().sum())
            if qtd > 0:
                erros.append(f"{qtd} linha(s) com obrigatório vazio: {col}")

    return out, erros


def _hash_row(tipo: str, row: dict, arquivo: str) -> str:
    parts = [tipo, arquivo]
    for key in sorted(row.keys()):
        val = row.get(key)
        parts.append(f"{key}={'' if pd.isna(val) else val}")
    return hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).hexdigest()


def _records_clean(df: pd.DataFrame) -> list[dict]:
    records = []
    for row in df.astype(object).to_dict(orient="records"):
        clean = {}
        for k, v in row.items():
            clean[k] = None if pd.isna(v) else v
        records.append(clean)
    return records


def _delete_period_if_replace(conn, cfg: ImportConfig, df: pd.DataFrame):
    if df.empty:
        return
    col_data = cfg.date_cols[0] if cfg.date_cols else None
    if not col_data or col_data not in df.columns:
        return
    inicio = df[col_data].min()
    fim = df[col_data].max()
    if pd.isna(inicio) or pd.isna(fim):
        return
    conn.execute(text(f"DELETE FROM {cfg.table} WHERE {col_data} BETWEEN :inicio AND :fim"), {"inicio": inicio, "fim": fim})


def importar_base_manual(tipo: str, uploaded_file: Any, usuario: str = "usuario", modo: str = "adicionar") -> dict:
    if tipo not in CONFIGS:
        raise ValueError(f"Tipo de importação inválido: {tipo}")

    cfg = CONFIGS[tipo]
    arquivo = getattr(uploaded_file, "name", "arquivo")
    df_raw = _ler_arquivo(uploaded_file)
    df, erros = validar_base(tipo, df_raw)

    if erros:
        _registrar_log(tipo, arquivo, usuario, modo, "ERRO_VALIDACAO", len(df_raw), 0, len(df_raw), "; ".join(erros), df)
        return {"status": "ERRO_VALIDACAO", "erros": erros, "registros_lidos": len(df_raw), "registros_processados": 0}

    df = df.copy()
    df["fonte_arquivo"] = arquivo
    if "fonte" in cfg.columns and "fonte" in df.columns:
        df["fonte"] = df["fonte"].fillna("manual_upload")

    # Hash único por linha.
    df["hash_linha"] = [_hash_row(tipo, r, arquivo) for r in _records_clean(df[cfg.columns])]

    # Campos especiais para tabelas existentes.
    if tipo == "ceagesp_pescados":
        if "data_referencia" in df.columns:
            df["chave_registro"] = df.apply(lambda r: _hash_row("ceagesp_chave", {"data": r.get("data_referencia"), "produto": r.get("produto"), "classificacao": r.get("classificacao"), "unidade": r.get("unidade")}, ""), axis=1)
    if tipo == "compra_manual" and "data" in df.columns:
        df["mes"] = pd.to_datetime(df["data"], errors="coerce").dt.to_period("M").dt.to_timestamp().dt.date
    if tipo == "receita_expansao":
        if "grupo_produto" in df.columns and "categoria_pescado" not in df.columns:
            df["categoria_pescado"] = df["grupo_produto"].fillna("Outros")

    records = _records_clean(df)
    if not records:
        return {"status": "VAZIO", "registros_lidos": len(df_raw), "registros_processados": 0}

    cols = list(records[0].keys())
    placeholders = ", ".join([f":{c}" for c in cols])
    cols_sql = ", ".join(cols)
    sql = text(f"""
        INSERT INTO {cfg.table} ({cols_sql})
        VALUES ({placeholders})
        ON CONFLICT (hash_linha) DO NOTHING
    """)

    engine = get_engine()
    with engine.begin() as conn:
        if modo == "substituir_periodo":
            _delete_period_if_replace(conn, cfg, df)
        conn.execute(sql, records)

    _registrar_log(tipo, arquivo, usuario, modo, "SUCESSO", len(df_raw), len(records), 0, "Importação concluída", df)
    return {"status": "SUCESSO", "registros_lidos": len(df_raw), "registros_processados": len(records), "erros": []}


def _registrar_log(tipo, arquivo, usuario, modo, status, lidos, processados, rejeitados, detalhe, df=None):
    periodo_inicio = None
    periodo_fim = None
    if isinstance(df, pd.DataFrame) and not df.empty:
        date_cols = CONFIGS[tipo].date_cols if tipo in CONFIGS else []
        for col in date_cols:
            if col in df.columns:
                periodo_inicio = df[col].min()
                periodo_fim = df[col].max()
                break
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.importacao_manual_log (
                tipo_importacao, arquivo, usuario, modo_importacao, status,
                registros_lidos, registros_processados, registros_rejeitados,
                periodo_inicio, periodo_fim, detalhe
            ) VALUES (
                :tipo, :arquivo, :usuario, :modo, :status,
                :lidos, :processados, :rejeitados,
                :periodo_inicio, :periodo_fim, :detalhe
            )
        """), {
            "tipo": tipo, "arquivo": arquivo, "usuario": usuario, "modo": modo, "status": status,
            "lidos": int(lidos or 0), "processados": int(processados or 0), "rejeitados": int(rejeitados or 0),
            "periodo_inicio": periodo_inicio, "periodo_fim": periodo_fim, "detalhe": detalhe,
        })


def carregar_historico_importacoes(limit: int = 100) -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        return pd.read_sql(text("""
            SELECT tipo_importacao, arquivo, usuario, modo_importacao, status,
                   registros_lidos, registros_processados, registros_rejeitados,
                   periodo_inicio, periodo_fim, detalhe, executado_em
            FROM app.importacao_manual_log
            ORDER BY executado_em DESC
            LIMIT :limit
        """), conn, params={"limit": limit})


def carregar_resumo_mercado_privado() -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        return pd.read_sql(text("""
            SELECT estado, microrregiao, categoria, produto, primeira_data, ultima_data,
                   valor_mercado, volume_mercado, preco_medio, qtd_lojas
            FROM app.vw_mercado_privado_resumo
            ORDER BY valor_mercado DESC NULLS LAST
            LIMIT 500
        """), conn)


def carregar_curva_mercado_privado(estado: str | None = None, categoria: str | None = None, produto: str | None = None) -> pd.DataFrame:
    where = []
    params = {}
    if estado and estado != "Todos":
        where.append("estado = :estado")
        params["estado"] = estado
    if categoria and categoria != "Todos":
        where.append("categoria = :categoria")
        params["categoria"] = categoria
    if produto and produto != "Todos":
        where.append("produto = :produto")
        params["produto"] = produto
    where_sql = "WHERE " + " AND ".join(where) if where else ""
    engine = get_engine()
    with engine.begin() as conn:
        return pd.read_sql(text(f"""
            SELECT data_competencia, estado, microrregiao, categoria, produto,
                   SUM(valor_mercado) AS valor_mercado,
                   SUM(volume_mercado) AS volume_mercado,
                   AVG(preco_medio) AS preco_medio
            FROM app.vw_curva_mercado_categoria
            {where_sql}
            GROUP BY data_competencia, estado, microrregiao, categoria, produto
            ORDER BY data_competencia, estado, microrregiao, categoria, produto
        """), conn, params=params)


def carregar_correlacao_mercado_idc(alvo: str = "valor_mercado", estado: str | None = None) -> pd.DataFrame:
    alvo = alvo if alvo in {"valor_mercado", "volume_mercado", "preco_medio"} else "valor_mercado"
    params = {}
    filtro = ""
    if estado and estado != "Todos":
        filtro = "WHERE m.estado = :estado"
        params["estado"] = estado

    engine = get_engine()
    with engine.begin() as conn:
        df = pd.read_sql(text(f"""
            WITH mercado AS (
                SELECT estado, microrregiao,
                       SUM(valor_mercado) AS valor_mercado,
                       SUM(volume_mercado) AS volume_mercado,
                       CASE WHEN SUM(volume_mercado) > 0 THEN SUM(valor_mercado)/SUM(volume_mercado) ELSE AVG(preco_medio) END AS preco_medio
                FROM app.vw_curva_mercado_categoria
                GROUP BY estado, microrregiao
            )
            SELECT
                i.estado, i.microrregiao,
                m.valor_mercado, m.volume_mercado, m.preco_medio,
                i.populacao, i.pib, i.renda_media, i.pib_per_capita,
                i.pct_feminina, i.pct_masculina, i.total_pdv, i.idh,
                i.fator_populacao, i.fator_pib, i.fator_renda, i.fator_pib_per_capita,
                i.fator_feminino, i.fator_masculino, i.fator_pdv,
                i.idc_base, i.score
            FROM mercado m
            JOIN app.vw_idc_completo_atual i
              ON i.estado = m.estado AND i.microrregiao = m.microrregiao
            {filtro}
        """), conn, params=params)

    if df.empty:
        return pd.DataFrame()

    variaveis = [
        "populacao", "pib", "renda_media", "pib_per_capita", "pct_feminina", "pct_masculina",
        "total_pdv", "idh", "fator_populacao", "fator_pib", "fator_renda", "fator_pib_per_capita",
        "fator_feminino", "fator_masculino", "fator_pdv", "idc_base", "score"
    ]
    rows = []
    y = pd.to_numeric(df[alvo], errors="coerce")
    for var in variaveis:
        if var not in df.columns:
            continue
        x = pd.to_numeric(df[var], errors="coerce")
        valid = pd.DataFrame({"x": x, "y": y}).dropna()
        if len(valid) < 3:
            continue
        pearson = valid["x"].corr(valid["y"], method="pearson")
        spearman = valid["x"].corr(valid["y"], method="spearman")
        rows.append({
            "variavel": var,
            "alvo": alvo,
            "pearson": pearson,
            "spearman": spearman,
            "forca": _classificar_correlacao(pearson),
            "direcao": "positiva" if pearson >= 0 else "negativa",
            "observacoes": len(valid),
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["abs_pearson"] = out["pearson"].abs()
    return out.sort_values("abs_pearson", ascending=False).drop(columns=["abs_pearson"])


def _classificar_correlacao(v) -> str:
    if pd.isna(v):
        return "Sem dados"
    a = abs(float(v))
    if a >= 0.75:
        return "Forte"
    if a >= 0.50:
        return "Média"
    if a >= 0.25:
        return "Fraca"
    return "Muito fraca"


def sugerir_pesos_idc_por_correlacao(alvo: str = "valor_mercado", estado: str | None = None) -> pd.DataFrame:
    corr = carregar_correlacao_mercado_idc(alvo=alvo, estado=estado)
    if corr.empty:
        return pd.DataFrame()

    mapa = {
        "populacao": "População",
        "pib": "PIB",
        "renda_media": "Renda",
        "pib_per_capita": "PIB per capita",
        "pct_feminina": "Feminino",
        "pct_masculina": "Masculino",
        "total_pdv": "Ponto de venda",
    }
    base = corr[corr["variavel"].isin(mapa.keys())].copy()
    if base.empty:
        return pd.DataFrame()
    base["peso_bruto"] = base["pearson"].abs().fillna(0)
    soma = base["peso_bruto"].sum()
    if soma <= 0:
        return pd.DataFrame()
    base["peso_sugerido_pct"] = base["peso_bruto"] / soma * 100
    base["criterio_idc"] = base["variavel"].map(mapa)
    return base[["criterio_idc", "variavel", "peso_sugerido_pct", "pearson", "spearman", "forca", "direcao"]].sort_values("peso_sugerido_pct", ascending=False)

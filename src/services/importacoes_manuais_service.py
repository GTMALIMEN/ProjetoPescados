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




def _deduplicar_hash_linha(conn, table_name: str) -> None:
    """Remove duplicidades técnicas por hash_linha antes de criar índice único.

    Mantém uma linha por hash. Isso protege bancos criados por versões antigas
    que permitiam duplicidade e evita erro no ON CONFLICT.
    """
    conn.execute(text(f"""
        DELETE FROM {table_name} a
        USING {table_name} b
        WHERE a.ctid < b.ctid
          AND a.hash_linha IS NOT NULL
          AND a.hash_linha = b.hash_linha
    """))


def _ensure_hash_unique_index(conn, table_name: str, index_name: str) -> None:
    """Garante índice único compatível com ON CONFLICT(hash_linha).

    Versões antigas criavam índice parcial ``WHERE hash_linha IS NOT NULL``.
    Esse tipo de índice não atende ``ON CONFLICT (hash_linha) DO NOTHING``
    sem repetir o predicado. Para evitar erro, removemos o índice antigo e
    criamos um índice único simples sobre hash_linha. PostgreSQL permite
    múltiplos NULL em índice único, então isso continua seguro.
    """
    schema = table_name.split(".")[0] if "." in table_name else None
    qualified_index = f"{schema}.{index_name}" if schema else index_name
    _deduplicar_hash_linha(conn, table_name)
    conn.execute(text(f"DROP INDEX IF EXISTS {qualified_index}"))
    conn.execute(text(f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {table_name}(hash_linha)"))


def _relation_exists(conn, relation_name: str) -> bool:
    """Retorna True se a tabela/view existe no banco.

    Usado nas importações para limpar/publicar tabelas auxiliares sem quebrar
    quando o ambiente ainda não tem DW completo criado.
    """
    return bool(conn.execute(text("SELECT to_regclass(:name) IS NOT NULL"), {"name": relation_name}).scalar())


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
    "cepea_manual": ImportConfig(
        tipo="cepea_manual",
        label="CEPEA Manual Oficial",
        table="app.fato_cepea_tilapia_manual",
        columns=[
            "data_inicio_periodo", "data_fim_periodo", "periodo_original", "produto",
            "regiao_cepea", "uf", "preco_ajustado", "preco_rs_kg", "variacao_semana_pct",
            "unidade", "url_fonte", "observacao"
        ],
        required=["data_fim_periodo", "preco_ajustado"],
        date_cols=["data_inicio_periodo", "data_fim_periodo"],
        numeric_cols=["preco_ajustado", "preco_rs_kg", "variacao_semana_pct"],
        description="CEPEA manual/controlado preenchido a partir das bases novas. O gráfico usa sempre PREÇO AJUSTADO e ignora tabelas antigas/proxy.",
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
        columns=["parceiro", "cidade", "estado", "data_competencia", "grupo_produto", "vlr_total_liquido", "volume", "produto", "top"],
        required=["cidade", "estado", "data_competencia", "grupo_produto", "vlr_total_liquido", "top"],
        date_cols=["data_competencia"],
        numeric_cols=["vlr_total_liquido", "volume"],
        description="Venda interna/receita por cidade e grupo de produto. TOP é obrigatório e deve ser 1100 - VENDA DE MERCADORIA para garantir venda faturada, não pedido.",
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
    "data inicio periodo": "data_inicio_periodo",
    "data inicial": "data_inicio_periodo",
    "data inicio": "data_inicio_periodo",
    "data_inicio_periodo": "data_inicio_periodo",
    "data fim periodo": "data_fim_periodo",
    "data final": "data_fim_periodo",
    "data fim": "data_fim_periodo",
    "data_fim_periodo": "data_fim_periodo",
    "periodo": "periodo_original",
    "periodo original": "periodo_original",
    "periodo_original": "periodo_original",
    "regiao cepea": "regiao_cepea",
    "regiao_cepea": "regiao_cepea",
    "praça": "regiao_cepea",
    "praca": "regiao_cepea",
    "preco rs kg": "preco_rs_kg",
    "preco r kg": "preco_rs_kg",
    "preco r$/kg": "preco_rs_kg",
    "preco_rs_kg": "preco_rs_kg",
    "r$/kg": "preco_rs_kg",
    "variacao semana pct": "variacao_semana_pct",
    "variacao_semana_pct": "variacao_semana_pct",
    "var pct": "variacao_semana_pct",
    "url fonte": "url_fonte",
    "url_fonte": "url_fonte",
}

TIPO_ALIASES = {
    "cepea_manual": {
        # Modelo CEPEA ajustado enviado pelo usuário.
        # IMPORTANTE: PREÇO AJUSTADO é o valor principal do gráfico/DW.
        # À vista R$ é preço bruto de referência e NÃO pode virar data.
        # Mês/Ano normalmente vem como data/serial do Excel e vira data_fim_periodo.
        "categoria": "produto",
        "produto": "produto",
        "a vista r": "preco_rs_kg",
        "a vista rs": "preco_rs_kg",
        "avista r": "preco_rs_kg",
        "à vista r$": "preco_rs_kg",
        "a vista us": "preco_usd_kg_aux",
        "a vista uss": "preco_usd_kg_aux",
        "à vista us$": "preco_usd_kg_aux",
        "ano": "ano_aux",
        "mes": "mes_aux",
        "mês": "mes_aux",
        "mes ano": "data_fim_periodo",
        "mês ano": "data_fim_periodo",
        "mes/ano": "data_fim_periodo",
        "mês/ano": "data_fim_periodo",
        "preco ajustado": "preco_ajustado",
        "preço ajustado": "preco_ajustado",
        "preco_ajustado": "preco_ajustado",
        "regiao": "regiao_cepea",
        "região": "regiao_cepea",
        "regiao cepea": "regiao_cepea",
        "região cepea": "regiao_cepea",
        "praca": "regiao_cepea",
        "praça": "regiao_cepea",
        "uf": "uf",
    },
    "ceagesp_pescados": {
        "data": "data_referencia",
        "produto": "produto",
        "classificacao": "classificacao",
        "classificação": "classificacao",
        "uni peso": "unidade",
        "uni/peso": "unidade",
        "menor": "preco_minimo",
        "comum": "preco_comum",
        "maior": "preco_maximo",
        "quilo": "quilo_aux",
    },
    "receita_expansao": {
        "volume": "volume",
        "produto": "produto",
        "top": "top",
        "tipo operacao": "top",
        "tipo de operacao": "top",
        "tipo operação": "top",
        "tipo de operação": "top",
    },
    "compra_manual": {
        "data": "data",
        "data competencia": "data",
        "data_competencia": "data",
        "data compra": "data",
        "data_compra": "data",
        "quantidade": "quantidade_comprada",
        "qtd": "quantidade_comprada",
        "quantidade comprada": "quantidade_comprada",
        "quantidade_comprada": "quantidade_comprada",
        "preco compra": "preco_compra",
        "preço compra": "preco_compra",
        "preco_compra": "preco_compra",
    },
    "previa_vendedores": {
        "quantidade": "quantidade_vendida",
        "qtd": "quantidade_vendida",
        "quantidade vendida": "quantidade_vendida",
        "quantidade_vendida": "quantidade_vendida",
        "receita": "receita_total",
        "receita total": "receita_total",
        "receita_total": "receita_total",
        "valor": "receita_total",
        "valor total": "receita_total",
        "cidade": "regiao",
        "regiao": "regiao",
        "região": "regiao",
        "observacao": "observacao",
        "observação": "observacao",
    },
}

TOP_RECEITA_EXPANSAO_OBRIGATORIO = "1100 - VENDA DE MERCADORIA"


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


def _canonical_col_tipo(tipo: str, col: str) -> str:
    raw = str(col or "").strip()
    key_space = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii").lower()
    key_space = re.sub(r"[^a-z0-9]+", " ", key_space).strip()
    tipo_aliases = TIPO_ALIASES.get(tipo, {})
    if key_space in tipo_aliases:
        return tipo_aliases[key_space]
    slug = _slug(raw)
    if slug in tipo_aliases:
        return tipo_aliases[slug]
    return _canonical_col(col)


def _normalizar_top_receita(valor: Any) -> str | None:
    txt = str(valor or "").strip()
    if not txt or txt.lower() in {"nan", "none"}:
        return None
    txt_norm = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii").upper()
    txt_norm = re.sub(r"\s+", " ", txt_norm).strip()
    if txt_norm == "1100" or txt_norm.startswith("1100") or txt_norm == "VENDA DE MERCADORIA":
        return TOP_RECEITA_EXPANSAO_OBRIGATORIO
    return txt


def _normalizar_produto_cepea(valor: Any) -> str:
    txt = str(valor or "").strip()
    if not txt or txt.lower() in {"nan", "none", "nat"}:
        return "Tilápia"
    norm = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii").upper().strip()
    norm = re.sub(r"\s+", " ", norm)
    mapa = {
        "BOI": "Bovino",
        "BOVINO": "Bovino",
        "BOI GORDO": "Bovino",
        "TILAPIA": "Tilápia",
        "TILÁPIA": "Tilápia",
        "CAMARAO": "Camarão",
        "CAMARÃO": "Camarão",
        "SALMAO": "Salmão",
        "SALMÃO": "Salmão",
    }
    return mapa.get(norm, txt)





def _to_numeric_br_series(series: pd.Series) -> pd.Series:
    """Converte número BR/Excel sem destruir decimais que já vieram como float.

    Exemplos corretos:
    - 3.345 (float do Excel) -> 3.345
    - "3,345" -> 3.345
    - "1.234,56" -> 1234.56
    - "R$ 10,22" -> 10.22
    """
    def conv(v):
        if pd.isna(v):
            return None
        if isinstance(v, (int, float)):
            return float(v)
        txt = str(v).strip()
        if not txt or txt.lower() in {"nan", "none", "nat"}:
            return None
        txt = txt.replace("R$", "").replace("%", "").strip()
        txt = re.sub(r"[^0-9,.-]", "", txt)
        if not txt:
            return None
        # Quando existem ponto e vírgula, assume padrão BR: 1.234,56
        if "," in txt and "." in txt:
            txt = txt.replace(".", "").replace(",", ".")
        elif "," in txt:
            txt = txt.replace(",", ".")
        # Quando só existe ponto, mantém como decimal. Não remover ponto.
        try:
            return float(txt)
        except Exception:
            return None
    return series.map(conv)


def _to_date_safe_series(series: pd.Series) -> pd.Series:
    """Converte datas normais e serial Excel sem gerar datas 1970 ou ano gigante."""
    def conv(v):
        if pd.isna(v):
            return None
        if hasattr(v, "date") and not isinstance(v, (int, float, str)):
            try:
                d = v.date()
                return d if 1900 <= d.year <= 9999 else None
            except Exception:
                return None
        if isinstance(v, (int, float)):
            # Serial Excel típico: 40000-60000. Também aceita datas históricas acima de 20000.
            if 20000 <= float(v) <= 60000:
                d = (pd.Timestamp("1899-12-30") + pd.to_timedelta(float(v), unit="D")).date()
                return d if 1900 <= d.year <= 9999 else None
            return None
        txt = str(v).strip()
        if not txt or txt.lower() in {"nan", "none", "nat"}:
            return None
        # Serial Excel vindo como texto.
        txt_num = txt.replace(",", ".")
        try:
            num = float(txt_num)
            if 20000 <= num <= 60000:
                d = (pd.Timestamp("1899-12-30") + pd.to_timedelta(num, unit="D")).date()
                return d if 1900 <= d.year <= 9999 else None
        except Exception:
            pass
        # ISO explícito deve ser interpretado como ano-mês-dia.
        # Sem essa regra, 2026-06-01 pode virar 2026-01-06 quando dayfirst=True.
        if re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:\s.*)?$", txt):
            d = pd.to_datetime(txt, errors="coerce", yearfirst=True)
        else:
            d = pd.to_datetime(txt, errors="coerce", dayfirst=True)
            if pd.isna(d):
                d = pd.to_datetime(txt, errors="coerce")
        if pd.isna(d):
            return None
        d = d.date()
        return d if 1900 <= d.year <= 9999 else None
    return series.map(conv)


def _safe_db_date(value):
    """Garante que logs não gravem datas fora da faixa aceita pelo Python/psycopg."""
    if value is None or pd.isna(value):
        return None
    d = _to_date_safe_series(pd.Series([value])).iloc[0]
    if d is None:
        return None
    return d if 1900 <= d.year <= 9999 else None


def configs_importacao() -> pd.DataFrame:
    return pd.DataFrame([
        {"tipo": c.tipo, "base": c.label, "tabela_destino": c.table, "colunas_obrigatorias": ", ".join(c.required), "descricao": c.description}
        for c in CONFIGS.values()
    ])


def gerar_template_excel(tipo: str) -> bytes:
    """Gera modelo Excel em branco, sem linhas de exemplo.

    Os modelos não devem vir preenchidos, porque uma linha de exemplo pode ser
    importada por engano e contaminar a base manual. O usuário baixa o arquivo,
    preenche apenas os dados reais e importa.
    """
    cfg = CONFIGS[tipo]
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(columns=cfg.columns).to_excel(writer, index=False, sheet_name="Modelo")
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
    out.columns = [_canonical_col_tipo(tipo, c) for c in out.columns]
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
            out[col] = _to_date_safe_series(out[col])
            if col in cfg.required and out[col].isna().all():
                erros.append(f"Coluna de data inválida ou vazia: {col}")

    # Números
    for col in cfg.numeric_cols:
        if col in out.columns:
            if tipo == "cepea_manual":
                out[col] = _to_numeric_br_series(out[col])
            else:
                out[col] = pd.to_numeric(out[col], errors="coerce")

    if tipo == "cepea_manual":
        if "preco_ajustado" in out.columns and "preco_rs_kg" in out.columns:
            out["preco_rs_kg"] = out["preco_rs_kg"].fillna(out["preco_ajustado"])
        if "produto" in out.columns:
            out["produto"] = out["produto"].map(_normalizar_produto_cepea)
        if "regiao_cepea" in out.columns:
            out["regiao_cepea"] = (
                out["regiao_cepea"]
                .where(out["regiao_cepea"].notna(), "CEPEA - série manual")
                .astype(str).str.strip()
                .replace({"": "CEPEA - série manual", "nan": "CEPEA - série manual", "None": "CEPEA - série manual"})
            )
        if "uf" in out.columns:
            out["uf"] = out["uf"].where(out["uf"].notna(), None)
        if "unidade" in out.columns:
            out["unidade"] = out["unidade"].fillna("R$/kg")
        if "url_fonte" in out.columns:
            out["url_fonte"] = out["url_fonte"].fillna("https://www.cepea.org.br/br/indicador/tilapia.aspx")

    if tipo == "cepea_manual":
        if "preco_ajustado" in out.columns:
            invalidos_preco = out["preco_ajustado"].isna() | (out["preco_ajustado"] <= 0) | (out["preco_ajustado"] > 500)
            if invalidos_preco.any():
                exemplos = ", ".join(out.loc[invalidos_preco, "preco_ajustado"].astype(str).drop_duplicates().head(5).tolist())
                erros.append(
                    "PREÇO AJUSTADO inválido ou fora da faixa segura (0 a 500 R$/kg). "
                    f"Valores encontrados: {exemplos}. Confira se a coluna foi lida corretamente."
                )

    if tipo == "ceagesp_pescados":
        if "fonte" in out.columns:
            out["fonte"] = "CEAGESP Manual"
        if "classificacao" in out.columns:
            out["classificacao"] = out["classificacao"].where(out["classificacao"].notna(), "-")
            out["classificacao"] = out["classificacao"].astype(str).str.strip().replace({"": "-", "nan": "-", "None": "-"})
        if "unidade" in out.columns:
            out["unidade"] = out["unidade"].where(out["unidade"].notna(), "KG")
            out["unidade"] = out["unidade"].astype(str).str.strip().replace({"": "KG", "nan": "KG", "None": "KG"}).str.upper()
        if "produto" in out.columns:
            out["produto"] = out["produto"].astype(str).str.strip().str.upper()
        if "preco_comum" in out.columns:
            invalidos_comum = out["preco_comum"].isna() | (out["preco_comum"] <= 0)
            if invalidos_comum.any():
                erros.append(f"{int(invalidos_comum.sum())} linha(s) com preço comum CEAGESP inválido.")
        if {"preco_minimo", "preco_comum"}.issubset(out.columns):
            mask = out["preco_minimo"].notna() & out["preco_comum"].notna() & (out["preco_minimo"] > out["preco_comum"])
            if mask.any():
                erros.append(f"{int(mask.sum())} linha(s) CEAGESP com preço mínimo maior que preço comum.")
        if {"preco_maximo", "preco_comum"}.issubset(out.columns):
            mask = out["preco_maximo"].notna() & out["preco_comum"].notna() & (out["preco_maximo"] < out["preco_comum"])
            if mask.any():
                erros.append(f"{int(mask.sum())} linha(s) CEAGESP com preço máximo menor que preço comum.")

    if tipo == "receita_expansao" and "top" in out.columns:
        out["top"] = out["top"].map(_normalizar_top_receita)
        invalidos = out["top"].notna() & (out["top"] != TOP_RECEITA_EXPANSAO_OBRIGATORIO)
        if invalidos.any():
            exemplos = ", ".join(out.loc[invalidos, "top"].astype(str).drop_duplicates().head(5).tolist())
            erros.append(
                "TOP inválido na Receita Expansão. Use somente "
                f"'{TOP_RECEITA_EXPANSAO_OBRIGATORIO}'. Valores encontrados: {exemplos}"
            )

    # UF/cidade/microrregião
    for col in ["uf", "estado"]:
        if col in out.columns:
            out[col] = out[col].astype(str).str.strip().str.upper().replace({"NAN": None, "NONE": None, "": None})

    for col in ["cidade", "microrregiao", "categoria", "produto", "marca", "canal", "fonte", "grupo_produto", "top"]:
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



def preparar_previa_publicacao(tipo: str, df_validado: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Monta prévias iguais às bases atuais que serão alimentadas.

    A leitura bruta do Excel pode ter nomes como ``Categoria``, ``Mês/Ano`` e
    ``PREÇO AJUSTADO``. Depois de ``validar_base`` o DataFrame já está
    normalizado. Esta função mostra no app a visão final que será gravada/usada
    pelos gráficos, evitando confusão com modelos antigos ou colunas auxiliares.
    """
    if df_validado is None or df_validado.empty:
        return {"Base normalizada": pd.DataFrame()}

    df = df_validado.copy()
    previews: dict[str, pd.DataFrame] = {}
    previews["Base normalizada que será gravada"] = df.copy()

    if tipo == "cepea_manual":
        grafico = pd.DataFrame({
            "data_referencia": df.get("data_fim_periodo"),
            "origem": "CEPEA Manual",
            "fonte": "CEPEA",
            "subcategoria": "oficial_arquivo_manual",
            "produto": df.get("produto"),
            "regiao": df.get("regiao_cepea"),
            "uf": df.get("uf"),
            "preco_grafico": df.get("preco_ajustado"),
            "preco_bruto_referencia": df.get("preco_rs_kg"),
            "unidade": df.get("unidade"),
        })
        previews["Prévia do gráfico/DW — usa PREÇO AJUSTADO"] = grafico
    elif tipo == "ceagesp_pescados":
        grafico = pd.DataFrame({
            "data_referencia": df.get("data_referencia"),
            "origem": "CEAGESP Manual",
            "produto": df.get("produto"),
            "classificacao": df.get("classificacao"),
            "preco_grafico": df.get("preco_comum"),
            "preco_minimo": df.get("preco_minimo"),
            "preco_maximo": df.get("preco_maximo"),
            "unidade": df.get("unidade"),
        })
        previews["Prévia do gráfico — usa PREÇO COMUM"] = grafico
    elif tipo == "receita_expansao":
        base = df.copy()
        base["regra_top"] = TOP_RECEITA_EXPANSAO_OBRIGATORIO
        previews["Prévia Receita Expansão — somente TOP 1100"] = base
    return previews


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




def _uf_cepea_por_regiao(regiao: str) -> str:
    r = str(regiao or "").strip().lower()
    if "morada nova" in r or "triâng" in r or "triang" in r or "alto parana" in r:
        return "MG"
    if "paraná" in r or "parana" in r:
        return "PR"
    if "grandes lagos" in r:
        return "SP/MS"
    return "BR"


def _cepea_chave_registro(row: dict) -> str:
    parts = [
        "CEPEA",
        str(row.get("data_fim_periodo") or ""),
        str(row.get("produto") or "Tilápia").strip().upper(),
        str(row.get("regiao_cepea") or "").strip().upper(),
        str(row.get("unidade") or "R$/kg").strip().upper(),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _ensure_cepea_manual_structure(conn) -> None:
    sql_path = __import__("pathlib").Path(__file__).resolve().parents[2] / "src" / "database" / "cepea_manual.sql"
    conn.execute(text(sql_path.read_text(encoding="utf-8")))


def _importar_cepea_manual_oficial(cfg: ImportConfig, df: pd.DataFrame, arquivo: str, usuario: str, modo: str) -> int:
    df = df.copy()
    df["preco_ajustado"] = pd.to_numeric(df["preco_ajustado"], errors="coerce")
    df["preco_rs_kg"] = pd.to_numeric(df.get("preco_rs_kg"), errors="coerce") if "preco_rs_kg" in df.columns else None
    df["preco_rs_kg"] = df["preco_rs_kg"].fillna(df["preco_ajustado"])
    df["produto"] = df["produto"].fillna("Tilápia").astype(str).str.strip().replace({"": "Tilápia"})
    df["regiao_cepea"] = df["regiao_cepea"].astype(str).str.strip()
    df["uf"] = df.apply(lambda r: str(r.get("uf") or "").strip().upper() or _uf_cepea_por_regiao(r.get("regiao_cepea")), axis=1)
    df["unidade"] = df["unidade"].fillna("R$/kg").astype(str).str.strip().replace({"": "R$/kg"})
    df["url_fonte"] = df["url_fonte"].fillna("https://www.cepea.org.br/br/indicador/tilapia.aspx")
    df["fonte"] = "CEPEA"
    df["tipo_fonte"] = "oficial_arquivo_manual"
    df["arquivo_origem"] = arquivo
    df["usuario_carga"] = usuario
    df["chave_registro"] = [_cepea_chave_registro(r) for r in _records_clean(df)]
    df["hash_linha"] = [_hash_row("cepea_manual", r, arquivo) for r in _records_clean(df[cfg.columns])]

    records = _records_clean(df[[
        "chave_registro", "hash_linha", "data_inicio_periodo", "data_fim_periodo",
        "periodo_original", "produto", "regiao_cepea", "uf", "preco_ajustado", "preco_rs_kg",
        "variacao_semana_pct", "unidade", "fonte", "tipo_fonte", "url_fonte",
        "arquivo_origem", "usuario_carga", "observacao"
    ]])

    indicador = "preco_tilapia_cepea_produtor_independente"

    def natural_key(data, produto, uf, regiao, unidade):
        key = "|".join([str(data or ""), "CEPEA", indicador, "proteina", "oficial_arquivo_manual", str(produto or ""), str(uf or ""), str(regiao or ""), "semanal"])
        return hashlib.md5(key.encode("utf-8")).hexdigest()

    dw_records = []
    for r in records:
        dw_records.append({
            "data": r.get("data_fim_periodo"),
            "fonte": "CEPEA",
            "indicador": indicador,
            "categoria": "proteina",
            "subcategoria": "oficial_arquivo_manual",
            "produto": r.get("produto"),
            "uf": r.get("uf"),
            "regiao": r.get("regiao_cepea"),
            "valor": r.get("preco_ajustado"),
            "unidade": r.get("unidade"),
            "periodicidade": "semanal",
            "natural_key_hash": natural_key(r.get("data_fim_periodo"), r.get("produto"), r.get("uf"), r.get("regiao_cepea"), r.get("unidade")),
        })

    engine = get_engine()
    with engine.begin() as conn:
        _ensure_cepea_manual_structure(conn)
        if modo == "substituir_tudo":
            conn.execute(text("DELETE FROM app.fato_cepea_tilapia_manual"))
            # Limpa qualquer resíduo CEPEA antigo/proxy/automático no DW.
            # A base manual nova será publicada novamente abaixo.
            if _relation_exists(conn, "dw.fato_indicador_setorial"):
                conn.execute(text("""
                    DELETE FROM dw.fato_indicador_setorial
                    WHERE fonte ILIKE '%CEPEA%'
                       OR COALESCE(subcategoria, '') ILIKE '%cepea%'
                       OR COALESCE(indicador, '') ILIKE '%cepea%'
                """))
        elif modo == "substituir_periodo":
            inicio = df["data_fim_periodo"].min()
            fim = df["data_fim_periodo"].max()
            conn.execute(text("DELETE FROM app.fato_cepea_tilapia_manual WHERE data_fim_periodo BETWEEN :inicio AND :fim"), {"inicio": inicio, "fim": fim})
            if _relation_exists(conn, "dw.fato_indicador_setorial"):
                conn.execute(text("""
                    DELETE FROM dw.fato_indicador_setorial
                    WHERE (fonte ILIKE '%CEPEA%'
                        OR COALESCE(subcategoria, '') ILIKE '%cepea%'
                        OR COALESCE(indicador, '') ILIKE '%cepea%')
                      AND data BETWEEN :inicio AND :fim
                """), {"inicio": inicio, "fim": fim})

        conn.execute(text("""
            INSERT INTO app.fato_cepea_tilapia_manual (
                chave_registro, hash_linha, data_inicio_periodo, data_fim_periodo,
                periodo_original, produto, regiao_cepea, uf, preco_ajustado, preco_rs_kg,
                variacao_semana_pct, unidade, fonte, tipo_fonte, url_fonte,
                arquivo_origem, usuario_carga, observacao
            )
            VALUES (
                :chave_registro, :hash_linha, :data_inicio_periodo, :data_fim_periodo,
                :periodo_original, :produto, :regiao_cepea, :uf, :preco_ajustado, :preco_rs_kg,
                :variacao_semana_pct, :unidade, :fonte, :tipo_fonte, :url_fonte,
                :arquivo_origem, :usuario_carga, :observacao
            )
            ON CONFLICT (chave_registro)
            DO UPDATE SET
                hash_linha = EXCLUDED.hash_linha,
                data_inicio_periodo = EXCLUDED.data_inicio_periodo,
                periodo_original = EXCLUDED.periodo_original,
                uf = EXCLUDED.uf,
                preco_ajustado = EXCLUDED.preco_ajustado,
                preco_rs_kg = EXCLUDED.preco_rs_kg,
                variacao_semana_pct = EXCLUDED.variacao_semana_pct,
                unidade = EXCLUDED.unidade,
                url_fonte = EXCLUDED.url_fonte,
                arquivo_origem = EXCLUDED.arquivo_origem,
                usuario_carga = EXCLUDED.usuario_carga,
                observacao = EXCLUDED.observacao,
                data_coleta = NOW();
        """), records)

        # Publicação opcional no DW para compatibilidade.
        # A tela principal de preços lê a tabela manual auditável; se o DW ainda
        # não existir, a importação não deve falhar por causa dele.
        if _relation_exists(conn, "dw.fato_indicador_setorial"):
            conn.execute(text("""
                INSERT INTO dw.fato_indicador_setorial (
                    data, fonte, indicador, categoria, subcategoria, produto, uf, regiao,
                    valor, unidade, periodicidade, natural_key_hash
                )
                VALUES (
                    :data, :fonte, :indicador, :categoria, :subcategoria, :produto, :uf, :regiao,
                    :valor, :unidade, :periodicidade, :natural_key_hash
                )
                ON CONFLICT (natural_key_hash)
                DO UPDATE SET
                    valor = EXCLUDED.valor,
                    unidade = EXCLUDED.unidade,
                    data_coleta = NOW();
            """), dw_records)

    return len(records)


def _ensure_receita_expansao_structure(conn) -> None:
    conn.execute(text("""
        ALTER TABLE app.fato_receita_manual_expansao
            ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
            ADD COLUMN IF NOT EXISTS hash_linha TEXT,
            ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS volume NUMERIC,
            ADD COLUMN IF NOT EXISTS produto TEXT,
            ADD COLUMN IF NOT EXISTS top TEXT,
            ADD COLUMN IF NOT EXISTS categoria_pescado TEXT;
    """))
    _ensure_hash_unique_index(conn, "app.fato_receita_manual_expansao", "uq_receita_manual_exp_hash")


def _ensure_import_table_structure(conn, tipo: str) -> None:
    """Garante colunas técnicas mínimas antes do INSERT das bases manuais.

    Isso evita erro quando o banco foi criado por script antigo e o app já está
    usando o modelo novo. Não altera dados existentes.
    """
    if tipo == "ceagesp_pescados":
        conn.execute(text("""
            ALTER TABLE app.fato_ceagesp_pescados
                ADD COLUMN IF NOT EXISTS chave_registro TEXT,
                ADD COLUMN IF NOT EXISTS data_referencia DATE,
                ADD COLUMN IF NOT EXISTS produto TEXT,
                ADD COLUMN IF NOT EXISTS classificacao TEXT,
                ADD COLUMN IF NOT EXISTS unidade TEXT,
                ADD COLUMN IF NOT EXISTS preco_minimo NUMERIC,
                ADD COLUMN IF NOT EXISTS preco_comum NUMERIC,
                ADD COLUMN IF NOT EXISTS preco_maximo NUMERIC,
                ADD COLUMN IF NOT EXISTS fonte TEXT DEFAULT 'CEAGESP Manual',
                ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
                ADD COLUMN IF NOT EXISTS hash_linha TEXT,
                ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();
        """))
        _ensure_hash_unique_index(conn, "app.fato_ceagesp_pescados", "uq_ceagesp_hash")
    elif tipo == "compra_manual":
        conn.execute(text("""
            ALTER TABLE app.fato_compra_manual
                ADD COLUMN IF NOT EXISTS data DATE,
                ADD COLUMN IF NOT EXISTS mes DATE,
                ADD COLUMN IF NOT EXISTS fornecedor TEXT,
                ADD COLUMN IF NOT EXISTS marca TEXT,
                ADD COLUMN IF NOT EXISTS produto TEXT,
                ADD COLUMN IF NOT EXISTS categoria TEXT,
                ADD COLUMN IF NOT EXISTS preco_compra NUMERIC,
                ADD COLUMN IF NOT EXISTS quantidade_comprada NUMERIC,
                ADD COLUMN IF NOT EXISTS unidade TEXT,
                ADD COLUMN IF NOT EXISTS observacao TEXT,
                ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
                ADD COLUMN IF NOT EXISTS hash_linha TEXT,
                ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();
        """))
        _ensure_hash_unique_index(conn, "app.fato_compra_manual", "uq_compra_manual_hash")
    elif tipo == "previa_vendedores":
        conn.execute(text("""
            ALTER TABLE app.fato_previa_vendedores
                ADD COLUMN IF NOT EXISTS vendedor TEXT,
                ADD COLUMN IF NOT EXISTS produto TEXT,
                ADD COLUMN IF NOT EXISTS preco NUMERIC,
                ADD COLUMN IF NOT EXISTS data_venda DATE,
                ADD COLUMN IF NOT EXISTS quantidade_vendida NUMERIC,
                ADD COLUMN IF NOT EXISTS receita_total NUMERIC,
                ADD COLUMN IF NOT EXISTS cliente TEXT,
                ADD COLUMN IF NOT EXISTS regiao TEXT,
                ADD COLUMN IF NOT EXISTS observacao TEXT,
                ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
                ADD COLUMN IF NOT EXISTS hash_linha TEXT,
                ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();
        """))
        _ensure_hash_unique_index(conn, "app.fato_previa_vendedores", "uq_previa_vendedores_hash")
    elif tipo == "mercado_privado":
        conn.execute(text("""
            ALTER TABLE app.fato_mercado_privado
                ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
                ADD COLUMN IF NOT EXISTS hash_linha TEXT,
                ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();
        """))
    elif tipo == "curva_mercado":
        conn.execute(text("""
            ALTER TABLE app.fato_curva_mercado_categoria
                ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
                ADD COLUMN IF NOT EXISTS hash_linha TEXT,
                ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();
        """))
    elif tipo == "key_account":
        conn.execute(text("""
            ALTER TABLE app.dim_key_account_loja
                ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
                ADD COLUMN IF NOT EXISTS hash_linha TEXT,
                ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();
        """))


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

    if tipo == "cepea_manual":
        processados = _importar_cepea_manual_oficial(cfg, df, arquivo, usuario, modo)
        _registrar_log(tipo, arquivo, usuario, modo, "SUCESSO", len(df_raw), processados, 0, "CEPEA manual oficial importado e publicado no DW", df)
        return {"status": "SUCESSO", "registros_lidos": len(df_raw), "registros_processados": processados, "erros": []}

    df = df.copy()
    df["fonte_arquivo"] = arquivo
    if "fonte" in cfg.columns and "fonte" in df.columns:
        df["fonte"] = df["fonte"].fillna("manual_upload")
    # Bases novas são manuais/controladas. Não deixar valor de fonte antigo
    # (CEPEA/CEAGESP automático, proxy etc.) reaparecer por ter vindo no Excel.
    if tipo == "ceagesp_pescados" and "fonte" in df.columns:
        df["fonte"] = "CEAGESP Manual"

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
        if tipo == "receita_expansao":
            _ensure_receita_expansao_structure(conn)
        else:
            _ensure_import_table_structure(conn, tipo)

        if modo == "substituir_tudo":
            conn.execute(text(f"DELETE FROM {cfg.table}"))
            if _relation_exists(conn, "dw.fato_indicador_setorial"):
                if tipo == "ceagesp_pescados":
                    conn.execute(text("""
                        DELETE FROM dw.fato_indicador_setorial
                        WHERE fonte ILIKE '%CEAGESP%'
                           OR COALESCE(subcategoria, '') ILIKE '%ceagesp%'
                           OR COALESCE(indicador, '') ILIKE '%ceagesp%'
                    """))
        elif modo == "substituir_periodo":
            _delete_period_if_replace(conn, cfg, df)

        # Toda base manual usa hash_linha para idempotência. Bancos antigos
        # podiam ter índice parcial ou não ter índice; isso é normalizado aqui.
        index_name = "uq_manual_" + re.sub(r"[^a-z0-9_]+", "_", cfg.table.replace("app.", "").replace("dw.", "")) + "_hash"
        _ensure_hash_unique_index(conn, cfg.table, index_name)
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
                periodo_inicio = _safe_db_date(df[col].min())
                periodo_fim = _safe_db_date(df[col].max())
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
        if not _relation_exists(conn, "app.importacao_manual_log"):
            return pd.DataFrame()
        # Limpa logs antigos com datas impossíveis para evitar DataError do psycopg.
        conn.execute(text("""
            UPDATE app.importacao_manual_log
            SET periodo_inicio = CASE
                    WHEN periodo_inicio IS NOT NULL
                     AND (periodo_inicio < DATE '1900-01-01' OR periodo_inicio > DATE '9999-12-31')
                    THEN NULL ELSE periodo_inicio END,
                periodo_fim = CASE
                    WHEN periodo_fim IS NOT NULL
                     AND (periodo_fim < DATE '1900-01-01' OR periodo_fim > DATE '9999-12-31')
                    THEN NULL ELSE periodo_fim END
            WHERE (periodo_inicio IS NOT NULL AND (periodo_inicio < DATE '1900-01-01' OR periodo_inicio > DATE '9999-12-31'))
               OR (periodo_fim IS NOT NULL AND (periodo_fim < DATE '1900-01-01' OR periodo_fim > DATE '9999-12-31'))
        """))
        return pd.read_sql(text("""
            SELECT tipo_importacao, arquivo, usuario, modo_importacao, status,
                   registros_lidos, registros_processados, registros_rejeitados,
                   periodo_inicio::text AS periodo_inicio,
                   periodo_fim::text AS periodo_fim,
                   detalhe, executado_em
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

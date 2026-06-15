from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
import unicodedata
import uuid
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.config.settings import settings
from src.database.connection import get_engine
from src.utils.logs import get_logger


logger = get_logger(__name__)


COLUMN_CANDIDATES = {
    "data": [
        "dt faturamento", "data faturamento", "data", "dt emissao", "dt negociacao",
        "data competencia", "previsao entrega"
    ],
    "numero_pedido": ["nro unico", "nro unico", "nro. unico", "nro único", "numero unico", "pedido"],
    "numero_documento": ["nro nota", "nro. nota", "numero nota", "nota fiscal", "nfe", "nro nfe"],
    "numero_item": ["sequencia", "seq", "item", "linha"],
    "codigo_cliente": ["cod parceiro", "cod. parceiro", "codigo parceiro", "cod cliente", "codigo cliente"],
    "cliente": ["parceiro", "cliente", "nome cliente", "razao social"],
    "cpf_cnpj": ["cpf cnpj", "cpf / cnpj", "cnpj", "cpf"],
    "perfil_cliente": ["perfil parceiro", "perfil cliente", "nomeperfil", "nome perfil"],
    "grupo_cliente": ["grupo cliente", "grupo economico", "rede", "descricao perfil pai", "perfil pai"],
    "municipio": ["nome cidade", "cidade", "municipio", "município"],
    "uf": ["uf", "estado"],
    "codigo_produto": ["cod produto", "cod. produto", "codigo produto", "cód produto", "cód. produto"],
    "produto": ["desc produto", "desc. produto", "produto", "descricao produto", "descrição produto"],
    "grupo_produto": ["desc grupo do produto", "desc. grupo do produto", "grupo produto", "grupo do produto"],
    "vendedor": ["vendedor", "nome vendedor"],
    "codigo_vendedor": ["cod vendedor", "cod. vendedor", "codigo vendedor", "cód vendedor"],
    "canal": ["canal", "tipo de negociacao", "tipo negociacao", "top", "natureza"],
    "valor_venda": [
        "vlr total liquido", "vlr. total liquido", "valor total liquido", "valor venda",
        "valor nota", "vlr total", "vlr. total", "valor"
    ],
    "volume_kg": [
        "peso liquido do produto kg", "peso líquido do produto kg",
        "peso liquido kg", "peso líquido kg", "qtd liquido nota kg",
        "qtd. liquido nota kg", "qtd líquido nota kg", "volume kg", "kg"
    ],
    "quantidade": ["quantidade", "qtd", "qtde", "qtd bruto nota kg", "qtd. bruto nota kg"],
}


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_municipio(value: object) -> str:
    return normalize_text(value)


def find_column(df: pd.DataFrame, canonical: str) -> str | None:
    normalized_cols = {normalize_text(col): col for col in df.columns}
    candidates = COLUMN_CANDIDATES.get(canonical, [])

    for candidate in candidates:
        key = normalize_text(candidate)
        if key in normalized_cols:
            return normalized_cols[key]

    # busca parcial controlada
    for candidate in candidates:
        key = normalize_text(candidate)
        for norm_col, original_col in normalized_cols.items():
            if key and key in norm_col:
                return original_col

    return None


def read_sales_file(path: Path, sheet_name: str | int | None = None) -> pd.DataFrame:
    suffix = path.suffix.lower()

    if suffix == ".csv":
        # sep=None tenta inferir ; ou ,
        return pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")

    if suffix in [".xlsx", ".xls"]:
        return pd.read_excel(path, sheet_name=sheet_name if sheet_name is not None else 0)

    if suffix == ".xlsb":
        return pd.read_excel(path, sheet_name=sheet_name if sheet_name is not None else 0, engine="pyxlsb")

    raise ValueError(f"Formato não suportado: {suffix}. Use .csv, .xlsx, .xls ou .xlsb")


def parse_decimal(value: object):
    if value is None or pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)

    text = str(value).strip()
    if text == "":
        return None

    # Formato brasileiro: 1.234,56
    text = text.replace("R$", "").replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return None


def parse_date(value: object):
    if value is None or pd.isna(value):
        return None

    # Se vier em ISO, como 2026-05-01, força yearfirst para evitar virar 2026-01-05.
    if isinstance(value, str):
        text = value.strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}", text):
            dt = pd.to_datetime(text, errors="coerce", yearfirst=True)
        else:
            dt = pd.to_datetime(text, errors="coerce", dayfirst=True)
    else:
        dt = pd.to_datetime(value, errors="coerce", dayfirst=True)

    if pd.isna(dt):
        return None

    return dt.date()


def safe_str(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if text == "":
        return None
    return text


def hash_cpf_cnpj(value: object) -> str | None:
    text = safe_str(value)
    if not text:
        return None

    digits = re.sub(r"\D", "", text)
    if not digits:
        return None

    # Hash simples para DW analítico. Em produção, usar salt/pepper em variável segura.
    return hashlib.sha256(digits.encode("utf-8")).hexdigest()


def parse_vendedor(vendedor: object, codigo_vendedor: object = None) -> tuple[str | None, str | None]:
    codigo = safe_str(codigo_vendedor)
    nome = safe_str(vendedor)

    if nome:
        match = re.match(r"^\s*(\d+)\s*[-–]\s*(.+)$", nome)
        if match:
            if not codigo:
                codigo = match.group(1).strip()
            nome = match.group(2).strip()

    return codigo, nome


def classificar_proteina(produto: object, grupo_produto: object) -> tuple[str | None, str | None, str | None]:
    texto = normalize_text(f"{produto or ''} {grupo_produto or ''}")

    if any(x in texto for x in ["salmao", "salmon"]):
        return "Salmão", "Pescado", "Importado"

    if any(x in texto for x in ["bacalhau"]):
        return "Bacalhau", "Pescado", "Importado"

    if any(x in texto for x in ["camarao"]):
        return "Camarão", "Pescado", "Importado"

    if any(x in texto for x in ["tilapia"]):
        return "Tilápia", "Pescado", "Nacional"

    if any(x in texto for x in ["merluza", "pescada", "peixe", "pescado", "file peixe", "lombo peixe"]):
        return "Pescado", "Pescado", None

    if "frango" in texto:
        return "Frango", "Proteína concorrente", "Nacional"

    if any(x in texto for x in ["suino", "porco", "pernil", "lombo suino"]):
        return "Suíno", "Proteína concorrente", "Nacional"

    if any(x in texto for x in ["boi", "bovino", "carne bovina"]):
        return "Bovino", "Proteína concorrente", "Nacional"

    if any(x in texto for x in ["ovo", "ovos"]):
        return "Ovos", "Proteína concorrente", "Nacional"

    return None, None, None


def build_geo_lookup(engine) -> dict[tuple[str, str], dict]:
    sql = """
        SELECT
            uf,
            municipio,
            codigo_ibge,
            regiao_comercial
        FROM dw.dim_geografia
    """

    with engine.begin() as conn:
        df_geo = pd.read_sql(text(sql), conn)

    lookup = {}
    for _, row in df_geo.iterrows():
        uf = safe_str(row["uf"])
        municipio = safe_str(row["municipio"])
        if not uf or not municipio:
            continue

        lookup[(uf.upper(), normalize_municipio(municipio))] = {
            "codigo_ibge": safe_str(row["codigo_ibge"]),
            "regiao_comercial": safe_str(row["regiao_comercial"]),
        }

    return lookup


def canonicalize_sales(df_raw: pd.DataFrame, arquivo_origem: str, engine) -> tuple[pd.DataFrame, dict]:
    colmap = {field: find_column(df_raw, field) for field in COLUMN_CANDIDATES.keys()}
    geo_lookup = build_geo_lookup(engine)

    linhas = []
    for idx, row in df_raw.iterrows():
        def get(field):
            col = colmap.get(field)
            if not col:
                return None
            return row.get(col)

        data = parse_date(get("data"))
        codigo_cliente = safe_str(get("codigo_cliente"))
        cliente = safe_str(get("cliente"))
        cpf_cnpj_hash = hash_cpf_cnpj(get("cpf_cnpj"))
        perfil_cliente = safe_str(get("perfil_cliente"))
        grupo_cliente = safe_str(get("grupo_cliente"))

        uf = safe_str(get("uf"))
        uf = uf.upper() if uf else None
        municipio = safe_str(get("municipio"))

        codigo_produto = safe_str(get("codigo_produto"))
        produto = safe_str(get("produto"))
        grupo_produto = safe_str(get("grupo_produto"))
        proteina, categoria, origem_produto = classificar_proteina(produto, grupo_produto)

        codigo_vendedor, vendedor = parse_vendedor(get("vendedor"), get("codigo_vendedor"))
        canal = safe_str(get("canal"))

        valor_venda = parse_decimal(get("valor_venda"))
        volume_kg = parse_decimal(get("volume_kg"))
        quantidade = parse_decimal(get("quantidade"))

        numero_documento = safe_str(get("numero_documento"))
        numero_item = safe_str(get("numero_item")) or str(idx + 1)
        numero_pedido = safe_str(get("numero_pedido"))

        codigo_ibge = None
        regiao_comercial = None

        if uf and municipio:
            geo = geo_lookup.get((uf, normalize_municipio(municipio)))
            if geo:
                codigo_ibge = geo["codigo_ibge"]
                regiao_comercial = geo["regiao_comercial"]

        hash_base = "|".join([
            arquivo_origem,
            safe_str(numero_documento) or "",
            safe_str(numero_item) or "",
            safe_str(numero_pedido) or "",
            str(data) if data else "",
            codigo_cliente or "",
            codigo_produto or "",
            f"{valor_venda:.4f}" if valor_venda is not None else "",
            f"{volume_kg:.4f}" if volume_kg is not None else "",
            f"{quantidade:.4f}" if quantidade is not None else "",
        ])
        chave_venda_hash = hashlib.md5(hash_base.encode("utf-8")).hexdigest()

        linhas.append({
            "arquivo_origem": arquivo_origem,
            "linha_origem": int(idx + 1),
            "codigo_origem": arquivo_origem,
            "numero_documento": numero_documento,
            "numero_item": numero_item,
            "numero_pedido": numero_pedido,
            "data": data,
            "codigo_cliente": codigo_cliente,
            "cliente": cliente,
            "grupo_cliente": grupo_cliente,
            "perfil_cliente": perfil_cliente,
            "cpf_cnpj_hash": cpf_cnpj_hash,
            "uf": uf,
            "municipio": municipio,
            "codigo_ibge": codigo_ibge,
            "regiao_comercial": regiao_comercial,
            "codigo_produto": codigo_produto,
            "produto": produto,
            "grupo_produto": grupo_produto,
            "proteina": proteina,
            "categoria": categoria,
            "origem_produto": origem_produto,
            "codigo_vendedor": codigo_vendedor,
            "vendedor": vendedor,
            "canal": canal,
            "valor_venda": valor_venda,
            "volume_kg": volume_kg,
            "quantidade": quantidade,
            "chave_venda_hash": chave_venda_hash,
        })

    df = pd.DataFrame(linhas)

    diagnostics = {
        "colunas_detectadas": colmap,
        "linhas_origem": len(df_raw),
        "linhas_validas_data": int(df["data"].notna().sum()) if not df.empty else 0,
        "linhas_validas_valor": int(df["valor_venda"].notna().sum()) if not df.empty else 0,
        "linhas_com_geo": int(df["codigo_ibge"].notna().sum()) if not df.empty else 0,
    }

    return df, diagnostics


def clean_records(df: pd.DataFrame) -> list[dict]:
    df_obj = df.astype(object)
    records = []
    for row in df_obj.to_dict(orient="records"):
        clean = {}
        for key, value in row.items():
            if pd.isna(value):
                clean[key] = None
            else:
                clean[key] = value
        records.append(clean)
    return records


def registrar_run(engine, run_id: str, mensagem: str):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.etl_run (
                run_id, fonte, tipo_execucao, ambiente, status, mensagem
            )
            VALUES (
                :run_id, 'VENDAS_INTERNAS', 'arquivo', :ambiente, 'INICIADO', :mensagem
            )
        """), {"run_id": run_id, "ambiente": settings.app_env, "mensagem": mensagem})


def finalizar_run(engine, run_id: str, status: str, mensagem: str):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE app.etl_run
            SET status = :status,
                mensagem = :mensagem,
                finalizado_em = NOW()
            WHERE run_id = :run_id
        """), {"run_id": run_id, "status": status, "mensagem": mensagem})


def registrar_controle(engine, run_id: str, status: str, mensagem: str, qtd_raw: int, qtd_staging: int, qtd_dw: int, qtd_rejeitados: int, tempo: float):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.etl_controle_carga (
                run_id,
                fonte,
                indicador,
                status,
                mensagem,
                qtd_registros,
                qtd_raw,
                qtd_staging,
                qtd_dw,
                qtd_rejeitados,
                tempo_execucao_segundos
            )
            VALUES (
                :run_id,
                'VENDAS_INTERNAS',
                'Arquivo de vendas',
                :status,
                :mensagem,
                :qtd_dw,
                :qtd_raw,
                :qtd_staging,
                :qtd_dw,
                :qtd_rejeitados,
                :tempo
            )
        """), {
            "run_id": run_id,
            "status": status,
            "mensagem": mensagem,
            "qtd_raw": qtd_raw,
            "qtd_staging": qtd_staging,
            "qtd_dw": qtd_dw,
            "qtd_rejeitados": qtd_rejeitados,
            "tempo": tempo,
        })


def save_staging(engine, run_id: str, df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    df = df.copy()
    df["run_id"] = run_id

    cols = [
        "run_id",
        "arquivo_origem",
        "linha_origem",
        "codigo_origem",
        "numero_documento",
        "numero_item",
        "numero_pedido",
        "data",
        "codigo_cliente",
        "cliente",
        "grupo_cliente",
        "perfil_cliente",
        "cpf_cnpj_hash",
        "uf",
        "municipio",
        "codigo_ibge",
        "regiao_comercial",
        "codigo_produto",
        "produto",
        "grupo_produto",
        "proteina",
        "categoria",
        "origem_produto",
        "codigo_vendedor",
        "vendedor",
        "canal",
        "valor_venda",
        "volume_kg",
        "quantidade",
        "chave_venda_hash",
    ]

    records = clean_records(df[cols])

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM staging.vendas_internas WHERE run_id = :run_id"), {"run_id": run_id})
        conn.execute(text("""
            INSERT INTO staging.vendas_internas (
                run_id,
                arquivo_origem,
                linha_origem,
                codigo_origem,
                numero_documento,
                numero_item,
                numero_pedido,
                data,
                codigo_cliente,
                cliente,
                grupo_cliente,
                perfil_cliente,
                cpf_cnpj_hash,
                uf,
                municipio,
                codigo_ibge,
                regiao_comercial,
                codigo_produto,
                produto,
                grupo_produto,
                proteina,
                categoria,
                origem_produto,
                codigo_vendedor,
                vendedor,
                canal,
                valor_venda,
                volume_kg,
                quantidade,
                chave_venda_hash
            )
            VALUES (
                :run_id,
                :arquivo_origem,
                :linha_origem,
                :codigo_origem,
                :numero_documento,
                :numero_item,
                :numero_pedido,
                :data,
                :codigo_cliente,
                :cliente,
                :grupo_cliente,
                :perfil_cliente,
                :cpf_cnpj_hash,
                :uf,
                :municipio,
                :codigo_ibge,
                :regiao_comercial,
                :codigo_produto,
                :produto,
                :grupo_produto,
                :proteina,
                :categoria,
                :origem_produto,
                :codigo_vendedor,
                :vendedor,
                :canal,
                :valor_venda,
                :volume_kg,
                :quantidade,
                :chave_venda_hash
            )
        """), records)

    return len(records)


def delete_existing_file_facts(engine, arquivo_origem: str) -> int:
    """Remove fatos já carregados do mesmo arquivo antes de recarregar.

    Isso evita duplicidade quando uma regra de parsing muda, por exemplo correção
    de datas ISO, ou quando o mesmo arquivo é reprocessado.
    """
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM dw.fato_vendas WHERE arquivo_origem = :arquivo_origem"),
            {"arquivo_origem": arquivo_origem},
        )
    return result.rowcount or 0


def upsert_dimensions(engine, df: pd.DataFrame):
    df = df.copy()

    clientes = df[["codigo_cliente", "cliente", "grupo_cliente", "perfil_cliente", "cpf_cnpj_hash", "uf", "municipio", "codigo_ibge"]].drop_duplicates(subset=["codigo_cliente"])
    clientes = clientes[clientes["codigo_cliente"].notna()]
    produtos = df[["codigo_produto", "produto", "grupo_produto", "proteina", "categoria", "origem_produto"]].drop_duplicates(subset=["codigo_produto"])
    produtos = produtos[produtos["codigo_produto"].notna()]
    vendedores = df[["codigo_vendedor", "vendedor"]].drop_duplicates(subset=["codigo_vendedor"])
    vendedores = vendedores[vendedores["codigo_vendedor"].notna()]
    canais = df[["canal"]].drop_duplicates()
    canais = canais[canais["canal"].notna()]

    with engine.begin() as conn:
        if not clientes.empty:
            conn.execute(text("""
                INSERT INTO dw.dim_cliente (
                    codigo_cliente, cliente, grupo_cliente, perfil_cliente, cpf_cnpj_hash, uf, municipio, codigo_ibge
                )
                VALUES (
                    :codigo_cliente, :cliente, :grupo_cliente, :perfil_cliente, :cpf_cnpj_hash, :uf, :municipio, :codigo_ibge
                )
                ON CONFLICT DO NOTHING
            """), clean_records(clientes))

        if not produtos.empty:
            prod_records = []
            for row in clean_records(produtos):
                row["origem"] = row.pop("origem_produto")
                prod_records.append(row)

            conn.execute(text("""
                INSERT INTO dw.dim_produto (
                    codigo_produto, produto, grupo_produto, proteina, categoria, origem
                )
                VALUES (
                    :codigo_produto, :produto, :grupo_produto, :proteina, :categoria, :origem
                )
                ON CONFLICT DO NOTHING
            """), prod_records)

        if not vendedores.empty:
            vend_records = []
            for row in clean_records(vendedores):
                vend_records.append({
                    "codigo_vendedor": row["codigo_vendedor"],
                    "vendedor": row["vendedor"],
                    "equipe": None,
                })

            conn.execute(text("""
                INSERT INTO dw.dim_vendedor (
                    codigo_vendedor, vendedor, equipe, ativo, data_inicio, registro_atual
                )
                VALUES (
                    :codigo_vendedor, :vendedor, :equipe, TRUE, CURRENT_DATE, TRUE
                )
                ON CONFLICT DO NOTHING
            """), vend_records)

        if not canais.empty:
            conn.execute(text("""
                INSERT INTO dw.dim_canal (canal)
                VALUES (:canal)
                ON CONFLICT DO NOTHING
            """), clean_records(canais))


def load_dimension_maps(engine):
    with engine.begin() as conn:
        clientes = pd.read_sql(text("SELECT id_cliente, codigo_cliente FROM dw.dim_cliente"), conn)
        produtos = pd.read_sql(text("SELECT id_produto, codigo_produto FROM dw.dim_produto"), conn)
        vendedores = pd.read_sql(text("SELECT id_vendedor, codigo_vendedor FROM dw.dim_vendedor WHERE registro_atual = TRUE"), conn)
        canais = pd.read_sql(text("SELECT id_canal, canal FROM dw.dim_canal"), conn)

    return {
        "clientes": dict(zip(clientes["codigo_cliente"], clientes["id_cliente"])),
        "produtos": dict(zip(produtos["codigo_produto"], produtos["id_produto"])),
        "vendedores": dict(zip(vendedores["codigo_vendedor"], vendedores["id_vendedor"])),
        "canais": dict(zip(canais["canal"], canais["id_canal"])),
    }


def upsert_fato_vendas(engine, df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    maps = load_dimension_maps(engine)

    records = []
    for _, row in df.iterrows():
        if pd.isna(row["data"]) or pd.isna(row["valor_venda"]):
            continue

        records.append({
            "arquivo_origem": row["arquivo_origem"],
            "linha_origem": int(row["linha_origem"]),
            "codigo_origem": row["codigo_origem"],
            "numero_documento": row["numero_documento"],
            "numero_item": row["numero_item"],
            "numero_pedido": row["numero_pedido"],
            "data": row["data"],
            "id_cliente": maps["clientes"].get(row["codigo_cliente"]),
            "id_produto": maps["produtos"].get(row["codigo_produto"]),
            "id_vendedor": maps["vendedores"].get(row["codigo_vendedor"]),
            "id_canal": maps["canais"].get(row["canal"]),
            "codigo_ibge": row["codigo_ibge"],
            "uf": row["uf"],
            "municipio": row["municipio"],
            "regiao_comercial": row["regiao_comercial"],
            "valor_venda": row["valor_venda"],
            "volume_kg": row["volume_kg"],
            "quantidade": row["quantidade"],
            "chave_venda_hash": row["chave_venda_hash"],
        })

    if not records:
        return 0

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO dw.fato_vendas (
                arquivo_origem,
                linha_origem,
                codigo_origem,
                numero_documento,
                numero_item,
                numero_pedido,
                data,
                id_cliente,
                id_produto,
                id_vendedor,
                id_canal,
                codigo_ibge,
                uf,
                municipio,
                regiao_comercial,
                valor_venda,
                volume_kg,
                quantidade,
                chave_venda_hash
            )
            VALUES (
                :arquivo_origem,
                :linha_origem,
                :codigo_origem,
                :numero_documento,
                :numero_item,
                :numero_pedido,
                :data,
                :id_cliente,
                :id_produto,
                :id_vendedor,
                :id_canal,
                :codigo_ibge,
                :uf,
                :municipio,
                :regiao_comercial,
                :valor_venda,
                :volume_kg,
                :quantidade,
                :chave_venda_hash
            )
            ON CONFLICT (chave_venda_hash)
            DO UPDATE SET
                valor_venda = EXCLUDED.valor_venda,
                volume_kg = EXCLUDED.volume_kg,
                quantidade = EXCLUDED.quantidade,
                id_cliente = EXCLUDED.id_cliente,
                id_produto = EXCLUDED.id_produto,
                id_vendedor = EXCLUDED.id_vendedor,
                id_canal = EXCLUDED.id_canal,
                codigo_ibge = EXCLUDED.codigo_ibge,
                uf = EXCLUDED.uf,
                municipio = EXCLUDED.municipio,
                regiao_comercial = EXCLUDED.regiao_comercial,
                data_carga = NOW();
        """), records)

    return len(records)


def refresh_materialized_views(engine):
    with engine.begin() as conn:
        conn.execute(text("REFRESH MATERIALIZED VIEW app.mv_vendas_mensal_geo"))


def carregar_vendas_arquivo(arquivo: str, sheet_name: str | int | None = None) -> None:
    engine = get_engine()
    path = Path(arquivo)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

    run_id = str(uuid.uuid4())
    inicio = time.perf_counter()
    arquivo_origem = path.name

    logger.info("Iniciando carga de vendas | arquivo=%s | run_id=%s", arquivo_origem, run_id)
    registrar_run(engine, run_id, f"Carga de vendas: {arquivo_origem}")

    try:
        df_raw = read_sales_file(path, sheet_name=sheet_name)
        df, diagnostics = canonicalize_sales(df_raw, arquivo_origem, engine)

        # Regras mínimas de validade
        df_valid = df[df["data"].notna() & df["valor_venda"].notna()].copy()
        qtd_rejeitados = len(df) - len(df_valid)

        qtd_staging = save_staging(engine, run_id, df_valid)

        # Reprocessamento idempotente por arquivo: se o mesmo arquivo for carregado de novo,
        # substituímos as linhas antigas antes de inserir as atuais.
        qtd_removidos_arquivo = delete_existing_file_facts(engine, arquivo_origem)
        if qtd_removidos_arquivo:
            logger.info("Linhas antigas removidas do mesmo arquivo | arquivo=%s | qtd=%s", arquivo_origem, qtd_removidos_arquivo)

        upsert_dimensions(engine, df_valid)
        qtd_dw = upsert_fato_vendas(engine, df_valid)
        refresh_materialized_views(engine)

        tempo = time.perf_counter() - inicio
        mensagem = f"Carga concluída. Diagnóstico: {json.dumps(diagnostics, ensure_ascii=False)}"

        registrar_controle(
            engine,
            run_id,
            "SUCESSO",
            mensagem,
            qtd_raw=len(df_raw),
            qtd_staging=qtd_staging,
            qtd_dw=qtd_dw,
            qtd_rejeitados=qtd_rejeitados,
            tempo=tempo,
        )
        finalizar_run(engine, run_id, "SUCESSO", mensagem)

        logger.info("Carga de vendas concluída | raw=%s | staging=%s | dw=%s | rejeitados=%s",
                    len(df_raw), qtd_staging, qtd_dw, qtd_rejeitados)

        print("\n✅ Carga de vendas concluída")
        print(f"Arquivo: {arquivo_origem}")
        print(f"Linhas origem: {len(df_raw)}")
        print(f"Linhas staging: {qtd_staging}")
        print(f"Linhas DW: {qtd_dw}")
        print(f"Rejeitadas: {qtd_rejeitados}")
        print("\nColunas detectadas:")
        for campo, coluna in diagnostics["colunas_detectadas"].items():
            print(f"- {campo}: {coluna}")

    except Exception as exc:
        tempo = time.perf_counter() - inicio
        logger.exception("Erro na carga de vendas")

        registrar_controle(
            engine,
            run_id,
            "ERRO_VALIDACAO",
            str(exc),
            qtd_raw=0,
            qtd_staging=0,
            qtd_dw=0,
            qtd_rejeitados=0,
            tempo=tempo,
        )
        finalizar_run(engine, run_id, "ERRO_VALIDACAO", str(exc))
        raise


def main():
    parser = argparse.ArgumentParser(description="Carregar arquivo de vendas internas")
    parser.add_argument("--arquivo", required=True, help="Caminho do arquivo .csv, .xlsx, .xls ou .xlsb")
    parser.add_argument("--sheet", required=False, help="Nome ou índice da aba para Excel")
    args = parser.parse_args()

    carregar_vendas_arquivo(args.arquivo, sheet_name=args.sheet)


if __name__ == "__main__":
    main()

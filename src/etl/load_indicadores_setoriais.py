from __future__ import annotations

import argparse
import hashlib
import math
import re
import time
import uuid
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.config.settings import settings
from src.database.connection import get_engine
from src.utils.logs import get_logger


logger = get_logger(__name__)


COLUMN_CANDIDATES = {
    "data": ["data", "mes", "mês", "periodo", "período"],
    "fonte": ["fonte", "origem"],
    "indicador": ["indicador", "serie", "série", "nome indicador"],
    "categoria": ["categoria"],
    "subcategoria": ["subcategoria", "sub categoria", "tipo"],
    "produto": ["produto", "item", "commodity"],
    "uf": ["uf", "estado"],
    "regiao": ["regiao", "região"],
    "valor": ["valor", "preco", "preço", "cotacao", "cotação"],
    "unidade": ["unidade", "medida"],
    "periodicidade": ["periodicidade", "frequencia", "frequência"],
}


def normalize_col(value: object) -> str:
    import unicodedata
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def find_column(df: pd.DataFrame, canonical: str) -> str | None:
    normalized = {normalize_col(c): c for c in df.columns}
    for cand in COLUMN_CANDIDATES.get(canonical, []):
        key = normalize_col(cand)
        if key in normalized:
            return normalized[key]
    return None


def parse_date(value: object):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, str):
        text_value = value.strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}", text_value):
            dt = pd.to_datetime(text_value, errors="coerce", yearfirst=True)
        else:
            dt = pd.to_datetime(text_value, errors="coerce", dayfirst=True)
    else:
        dt = pd.to_datetime(value, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return None
    return dt.date()


def parse_decimal(value: object):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    text_value = str(value).strip().replace("R$", "").replace("US$", "").replace(" ", "")
    if not text_value:
        return None
    if "," in text_value and "." in text_value:
        text_value = text_value.replace(".", "").replace(",", ".")
    elif "," in text_value:
        text_value = text_value.replace(",", ".")
    try:
        return float(text_value)
    except ValueError:
        return None


def safe_str(value: object, default: str = "") -> str:
    if value is None or pd.isna(value):
        return default
    out = str(value).strip()
    return out if out else default


def read_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")
    if suffix in [".xlsx", ".xls"]:
        return pd.read_excel(path)
    if suffix == ".xlsb":
        return pd.read_excel(path, engine="pyxlsb")
    raise ValueError(f"Formato não suportado: {suffix}")


def canonicalize(df_raw: pd.DataFrame, arquivo_origem: str) -> tuple[pd.DataFrame, dict]:
    colmap = {field: find_column(df_raw, field) for field in COLUMN_CANDIDATES.keys()}
    records = []

    for idx, row in df_raw.iterrows():
        def get(field):
            col = colmap.get(field)
            return row.get(col) if col else None

        data = parse_date(get("data"))
        fonte = safe_str(get("fonte"), "Arquivo")
        indicador = safe_str(get("indicador"))
        categoria = safe_str(get("categoria"), "setorial")
        subcategoria = safe_str(get("subcategoria"))
        produto = safe_str(get("produto"))
        uf = safe_str(get("uf")).upper()
        regiao = safe_str(get("regiao"))
        valor = parse_decimal(get("valor"))
        unidade = safe_str(get("unidade"))
        periodicidade = safe_str(get("periodicidade"), "mensal")

        key = "|".join([
            str(data or ""),
            fonte,
            indicador,
            categoria,
            subcategoria,
            produto,
            uf,
            regiao,
            periodicidade,
        ])
        natural_key_hash = hashlib.md5(key.encode("utf-8")).hexdigest()

        records.append({
            "arquivo_origem": arquivo_origem,
            "linha_origem": int(idx + 1),
            "data": data,
            "fonte": fonte,
            "indicador": indicador,
            "categoria": categoria,
            "subcategoria": subcategoria,
            "produto": produto,
            "uf": uf,
            "regiao": regiao,
            "valor": valor,
            "unidade": unidade,
            "periodicidade": periodicidade,
            "natural_key_hash": natural_key_hash,
        })

    df = pd.DataFrame(records)
    diagnostics = {
        "colunas_detectadas": colmap,
        "linhas_origem": len(df_raw),
        "linhas_validas": int((df["data"].notna() & df["indicador"].ne("") & df["valor"].notna()).sum()) if not df.empty else 0,
    }
    return df, diagnostics


def clean_records(df: pd.DataFrame) -> list[dict]:
    out = []
    for row in df.astype(object).to_dict(orient="records"):
        out.append({k: (None if pd.isna(v) else v) for k, v in row.items()})
    return out


def registrar_run(engine, run_id: str, mensagem: str):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.etl_run (
                run_id, fonte, tipo_execucao, ambiente, status, mensagem
            )
            VALUES (
                :run_id, 'INDICADORES_SETORIAIS', 'arquivo', :ambiente, 'INICIADO', :mensagem
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
                run_id, fonte, indicador, status, mensagem, qtd_registros,
                qtd_raw, qtd_staging, qtd_dw, qtd_rejeitados, tempo_execucao_segundos
            )
            VALUES (
                :run_id, 'INDICADORES_SETORIAIS', 'Arquivo setorial', :status, :mensagem, :qtd_dw,
                :qtd_raw, :qtd_staging, :qtd_dw, :qtd_rejeitados, :tempo
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


def salvar_staging(engine, run_id: str, df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    temp = df.copy()
    temp["run_id"] = run_id
    records = clean_records(temp)

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM staging.indicador_setorial WHERE run_id = :run_id"), {"run_id": run_id})
        conn.execute(text("""
            INSERT INTO staging.indicador_setorial (
                run_id, arquivo_origem, linha_origem, data, fonte, indicador,
                categoria, subcategoria, produto, uf, regiao, valor, unidade,
                periodicidade, natural_key_hash
            )
            VALUES (
                :run_id, :arquivo_origem, :linha_origem, :data, :fonte, :indicador,
                :categoria, :subcategoria, :produto, :uf, :regiao, :valor, :unidade,
                :periodicidade, :natural_key_hash
            )
        """), records)

    return len(records)


def upsert_dw(engine, df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    records = clean_records(df)

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO dw.fato_indicador_setorial (
                data, fonte, indicador, categoria, subcategoria, produto, uf,
                regiao, valor, unidade, periodicidade, natural_key_hash
            )
            VALUES (
                :data, :fonte, :indicador, :categoria, :subcategoria, :produto, :uf,
                :regiao, :valor, :unidade, :periodicidade, :natural_key_hash
            )
            ON CONFLICT (natural_key_hash)
            DO UPDATE SET
                valor = EXCLUDED.valor,
                unidade = EXCLUDED.unidade,
                data_coleta = NOW();
        """), records)

    return len(records)


def carregar_indicadores_setoriais_arquivo(arquivo: str) -> None:
    engine = get_engine()
    path = Path(arquivo)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

    run_id = str(uuid.uuid4())
    inicio = time.perf_counter()
    arquivo_origem = path.name

    registrar_run(engine, run_id, f"Carga indicadores setoriais: {arquivo_origem}")

    try:
        df_raw = read_file(path)
        df, diagnostics = canonicalize(df_raw, arquivo_origem)
        df_valid = df[df["data"].notna() & df["indicador"].ne("") & df["valor"].notna()].copy()
        rejeitados = len(df) - len(df_valid)

        qtd_staging = salvar_staging(engine, run_id, df_valid)
        qtd_dw = upsert_dw(engine, df_valid)

        tempo = time.perf_counter() - inicio
        mensagem = f"Carga concluída. Diagnóstico: {diagnostics}"

        registrar_controle(engine, run_id, "SUCESSO", mensagem, len(df_raw), qtd_staging, qtd_dw, rejeitados, tempo)
        finalizar_run(engine, run_id, "SUCESSO", mensagem)

        print("\n✅ Carga de indicadores setoriais concluída")
        print(f"Arquivo: {arquivo_origem}")
        print(f"Linhas origem: {len(df_raw)}")
        print(f"Linhas staging: {qtd_staging}")
        print(f"Linhas DW: {qtd_dw}")
        print(f"Rejeitadas: {rejeitados}")
        print("\nColunas detectadas:")
        for campo, coluna in diagnostics["colunas_detectadas"].items():
            print(f"- {campo}: {coluna}")

    except Exception as exc:
        tempo = time.perf_counter() - inicio
        logger.exception("Erro na carga de indicadores setoriais")
        registrar_controle(engine, run_id, "ERRO_VALIDACAO", str(exc), 0, 0, 0, 0, tempo)
        finalizar_run(engine, run_id, "ERRO_VALIDACAO", str(exc))
        raise


def main():
    parser = argparse.ArgumentParser(description="Carregar indicadores setoriais de proteínas/grãos")
    parser.add_argument("--arquivo", required=True, help="Arquivo .csv/.xlsx/.xlsb com indicadores setoriais")
    args = parser.parse_args()
    carregar_indicadores_setoriais_arquivo(args.arquivo)


if __name__ == "__main__":
    main()

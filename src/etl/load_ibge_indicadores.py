from __future__ import annotations

import json
import time
import uuid
from datetime import date

import pandas as pd
from sqlalchemy import text

from src.collectors.sidra_collector import SidraCollector
from src.config.settings import settings
from src.database.connection import get_engine
from src.utils.logs import get_logger

logger = get_logger(__name__)


def clean_records(df: pd.DataFrame) -> list[dict]:
    records = []
    for row in df.astype(object).to_dict(orient="records"):
        cleaned = {}
        for key, value in row.items():
            cleaned[key] = None if pd.isna(value) else value
        records.append(cleaned)
    return records


def periodo_to_date(periodo: str) -> date:
    text = str(periodo or "").strip()
    if text.isdigit() and len(text) == 4:
        return date(int(text), 7, 1)
    if text.isdigit() and len(text) == 6:
        return date(int(text[:4]), int(text[4:6]), 1)
    return date.today()


def registrar_run(engine, run_id: str, status: str = "INICIADO", mensagem: str | None = None):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.etl_run (
                run_id, fonte, tipo_execucao, ambiente, status, mensagem
            )
            VALUES (
                :run_id, 'IBGE/SIDRA', 'indicadores_municipais', :ambiente, :status, :mensagem
            )
        """), {
            "run_id": run_id,
            "ambiente": settings.app_env,
            "status": status,
            "mensagem": mensagem,
        })


def finalizar_run(engine, run_id: str, status: str, mensagem: str | None = None):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE app.etl_run
            SET status = :status,
                mensagem = :mensagem,
                finalizado_em = NOW()
            WHERE run_id = :run_id
        """), {"run_id": run_id, "status": status, "mensagem": mensagem})


def salvar_raw(engine, run_id: str, metadata: dict):
    payload = metadata.get("payload", [])
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO raw.api_payload (
                run_id, fonte, endpoint, parametros, payload, status_http
            )
            VALUES (
                :run_id, 'IBGE/SIDRA', :endpoint,
                CAST(:parametros AS JSONB), CAST(:payload AS JSONB), :status_http
            )
        """), {
            "run_id": run_id,
            "endpoint": metadata.get("url"),
            "parametros": json.dumps(metadata.get("params", {}), ensure_ascii=False),
            "payload": json.dumps(payload, ensure_ascii=False),
            "status_http": metadata.get("status_http"),
        })


def enriquecer_geo(engine, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    with engine.begin() as conn:
        geo = pd.read_sql(text("""
            SELECT codigo_ibge, municipio AS municipio_geo, uf AS uf_geo
            FROM dw.dim_geografia
        """), conn)

    out = df.merge(geo, on="codigo_ibge", how="left")
    out["municipio"] = out["municipio"].fillna(out["municipio_geo"])
    out["uf"] = out["uf"].fillna(out["uf_geo"])
    out = out.drop(columns=["municipio_geo", "uf_geo"])
    return out


def salvar_staging(engine, run_id: str, df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    temp = df.copy()
    temp["run_id"] = run_id
    records = clean_records(temp[[
        "run_id", "fonte", "tabela_sidra", "variavel_codigo", "variavel_nome",
        "periodo", "codigo_ibge", "municipio", "uf", "indicador", "categoria", "valor", "unidade"
    ]])

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM staging.ibge_sidra_municipal WHERE run_id = :run_id"), {"run_id": run_id})
        conn.execute(text("""
            INSERT INTO staging.ibge_sidra_municipal (
                run_id, fonte, tabela_sidra, variavel_codigo, variavel_nome,
                periodo, codigo_ibge, municipio, uf, indicador, categoria, valor, unidade
            )
            VALUES (
                :run_id, :fonte, :tabela_sidra, :variavel_codigo, :variavel_nome,
                :periodo, :codigo_ibge, :municipio, :uf, :indicador, :categoria, :valor, :unidade
            )
        """), records)

    return len(records)


def upsert_dw(engine, df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    temp = df.copy()
    temp["data_referencia"] = temp["periodo"].apply(periodo_to_date)
    records = clean_records(temp[[
        "data_referencia", "fonte", "tabela_sidra", "variavel_codigo", "variavel_nome",
        "indicador", "categoria", "uf", "codigo_ibge", "municipio", "valor", "unidade"
    ]])

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO dw.fato_indicador_municipal (
                data_referencia, fonte, tabela_sidra, variavel_codigo, variavel_nome,
                indicador, categoria, uf, codigo_ibge, municipio, valor, unidade
            )
            VALUES (
                :data_referencia, :fonte, :tabela_sidra, :variavel_codigo, :variavel_nome,
                :indicador, :categoria, :uf, :codigo_ibge, :municipio, :valor, :unidade
            )
            ON CONFLICT (
                data_referencia, fonte, tabela_sidra, variavel_codigo, indicador, codigo_ibge
            )
            DO UPDATE SET
                variavel_nome = EXCLUDED.variavel_nome,
                categoria = EXCLUDED.categoria,
                uf = EXCLUDED.uf,
                municipio = EXCLUDED.municipio,
                valor = EXCLUDED.valor,
                unidade = EXCLUDED.unidade,
                data_coleta = NOW();
        """), records)

    return len(records)


def registrar_controle(engine, run_id: str, indicador: str, status: str, mensagem: str, qtd_raw: int, qtd_staging: int, qtd_dw: int, qtd_rejeitados: int, tempo: float):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.etl_controle_carga (
                run_id, fonte, indicador, status, mensagem, qtd_registros,
                qtd_raw, qtd_staging, qtd_dw, qtd_rejeitados, tempo_execucao_segundos
            )
            VALUES (
                :run_id, 'IBGE/SIDRA', :indicador, :status, :mensagem, :qtd_dw,
                :qtd_raw, :qtd_staging, :qtd_dw, :qtd_rejeitados, :tempo
            )
        """), {
            "run_id": run_id,
            "indicador": indicador,
            "status": status,
            "mensagem": mensagem,
            "qtd_raw": qtd_raw,
            "qtd_staging": qtd_staging,
            "qtd_dw": qtd_dw,
            "qtd_rejeitados": qtd_rejeitados,
            "tempo": tempo,
        })


def carregar_populacao_estimada(periodo: str | None = None) -> None:
    engine = get_engine()
    collector = SidraCollector()
    run_id = str(uuid.uuid4())
    inicio = time.perf_counter()

    logger.info("Iniciando carga IBGE/SIDRA população estimada | run_id=%s", run_id)
    registrar_run(engine, run_id, "INICIADO", "Carga de população estimada por município")

    try:
        df, metadata = collector.coletar_populacao_estimada(periodo=periodo)
        salvar_raw(engine, run_id, metadata)
        df = enriquecer_geo(engine, df)

        qtd_raw = len(metadata.get("payload", []))
        qtd_rejeitados = max(0, len(df) - int(df["valor"].notna().sum())) if not df.empty else 0
        qtd_staging = salvar_staging(engine, run_id, df)
        qtd_dw = upsert_dw(engine, df)
        tempo = time.perf_counter() - inicio

        registrar_controle(
            engine, run_id,
            indicador="População residente estimada",
            status="SUCESSO",
            mensagem="Carga concluída",
            qtd_raw=qtd_raw,
            qtd_staging=qtd_staging,
            qtd_dw=qtd_dw,
            qtd_rejeitados=qtd_rejeitados,
            tempo=tempo,
        )
        finalizar_run(engine, run_id, "SUCESSO", "Carga concluída")
        logger.info("Carga IBGE/SIDRA concluída | staging=%s | dw=%s", qtd_staging, qtd_dw)

    except Exception as exc:
        tempo = time.perf_counter() - inicio
        logger.exception("Erro na carga IBGE/SIDRA")
        registrar_controle(
            engine, run_id,
            indicador="População residente estimada",
            status="ERRO_API",
            mensagem=str(exc),
            qtd_raw=0,
            qtd_staging=0,
            qtd_dw=0,
            qtd_rejeitados=0,
            tempo=tempo,
        )
        finalizar_run(engine, run_id, "ERRO_API", str(exc))
        raise

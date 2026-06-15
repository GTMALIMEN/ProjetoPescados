from __future__ import annotations

from datetime import datetime
import uuid
import time
import json
from sqlalchemy import text
import pandas as pd

from src.database.connection import get_engine
from src.collectors.bcb_collector import BCBCollector, BCB_SERIES
from src.config.settings import settings
from src.etl.upsert import upsert_fato_serie_historica
from src.utils.logs import get_logger
from src.utils.data_quality import (
    validar_colunas_obrigatorias,
    validar_dataframe_nao_vazio,
    validar_valor_numerico,
)


logger = get_logger(__name__)


def _data_br(data_iso: str) -> str:
    return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")


def registrar_run(engine, run_id: str, fonte: str, tipo_execucao: str, status: str, mensagem: str | None = None):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO app.etl_run (
                    run_id, fonte, tipo_execucao, ambiente, status, mensagem
                )
                VALUES (
                    :run_id, :fonte, :tipo_execucao, :ambiente, :status, :mensagem
                )
            """),
            {
                "run_id": run_id,
                "fonte": fonte,
                "tipo_execucao": tipo_execucao,
                "ambiente": settings.app_env,
                "status": status,
                "mensagem": mensagem,
            },
        )


def finalizar_run(engine, run_id: str, status: str, mensagem: str | None = None):
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE app.etl_run
                SET status = :status,
                    mensagem = :mensagem,
                    finalizado_em = NOW()
                WHERE run_id = :run_id
            """),
            {"run_id": run_id, "status": status, "mensagem": mensagem},
        )


def salvar_raw(engine, run_id: str, metadata: dict, fonte: str, data_inicio: str, data_fim: str | None):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO raw.api_payload (
                    run_id,
                    fonte,
                    endpoint,
                    parametros,
                    payload,
                    status_http,
                    data_referencia_inicio,
                    data_referencia_fim
                )
                VALUES (
                    :run_id,
                    :fonte,
                    :endpoint,
                    CAST(:parametros AS JSONB),
                    CAST(:payload AS JSONB),
                    :status_http,
                    :data_inicio,
                    :data_fim
                )
            """),
            {
                "run_id": run_id,
                "fonte": fonte,
                "endpoint": metadata.get("url"),
                "parametros": json.dumps(metadata.get("params", {}), ensure_ascii=False),
                "payload": json.dumps(metadata.get("payload", []), ensure_ascii=False),
                "status_http": metadata.get("status_http"),
                "data_inicio": data_inicio,
                "data_fim": data_fim,
            },
        )


def salvar_staging_bcb(engine, run_id: str, df: pd.DataFrame):
    if df.empty:
        return 0

    staging = df[["data", "codigo_serie", "indicador", "valor", "unidade"]].copy()
    staging["run_id"] = run_id
    registros = staging.to_dict(orient="records")

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM staging.bcb_series WHERE run_id = :run_id"), {"run_id": run_id})
        conn.execute(
            text("""
                INSERT INTO staging.bcb_series (
                    run_id, data, codigo_serie, indicador, valor, unidade
                )
                VALUES (
                    :run_id, :data, :codigo_serie, :indicador, :valor, :unidade
                )
            """),
            registros,
        )

    return len(registros)


def registrar_dq(engine, run_id: str, fonte: str, tabela: str, regra: str, status: str, qtd: int, detalhe: str):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO app.data_quality_resultado (
                    run_id, fonte, tabela, regra, status, qtd_linhas_afetadas, detalhe
                )
                VALUES (
                    :run_id, :fonte, :tabela, :regra, :status, :qtd, :detalhe
                )
            """),
            {
                "run_id": run_id,
                "fonte": fonte,
                "tabela": tabela,
                "regra": regra,
                "status": status,
                "qtd": qtd,
                "detalhe": detalhe,
            },
        )


def registrar_controle_carga(
    engine,
    run_id: str,
    serie,
    data_inicio: str,
    status: str,
    mensagem: str,
    qtd_raw: int,
    qtd_staging: int,
    qtd_dw: int,
    qtd_rejeitados: int,
    tempo_execucao: float,
):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO app.etl_controle_carga (
                    run_id,
                    fonte,
                    indicador,
                    codigo_serie,
                    data_inicio_solicitada,
                    data_inicio_disponivel,
                    data_fim_disponivel,
                    ultima_data_coletada,
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
                    'BCB',
                    :indicador,
                    :codigo_serie,
                    :data_inicio_solicitada,
                    :data_inicio_disponivel,
                    :data_fim_disponivel,
                    :ultima_data_coletada,
                    :status,
                    :mensagem,
                    :qtd_registros,
                    :qtd_raw,
                    :qtd_staging,
                    :qtd_dw,
                    :qtd_rejeitados,
                    :tempo_execucao
                )
            """),
            {
                "run_id": run_id,
                "indicador": serie.indicador,
                "codigo_serie": serie.codigo,
                "data_inicio_solicitada": data_inicio,
                "data_inicio_disponivel": None,
                "data_fim_disponivel": None,
                "ultima_data_coletada": None,
                "status": status,
                "mensagem": mensagem,
                "qtd_registros": qtd_dw,
                "qtd_raw": qtd_raw,
                "qtd_staging": qtd_staging,
                "qtd_dw": qtd_dw,
                "qtd_rejeitados": qtd_rejeitados,
                "tempo_execucao": tempo_execucao,
            },
        )


def carregar_bcb(data_inicio_iso: str | None = None) -> None:
    engine = get_engine()
    collector = BCBCollector()

    data_inicio_iso = data_inicio_iso or settings.data_inicio_padrao
    data_inicio_br = _data_br(data_inicio_iso)

    for serie in BCB_SERIES:
        run_id = str(uuid.uuid4())
        inicio = time.perf_counter()

        logger.info("Iniciando carga BCB | %s | run_id=%s", serie.indicador, run_id)
        registrar_run(engine, run_id, "BCB", "historica", "INICIADO", f"Carga {serie.indicador}")

        try:
            df, metadata = collector.coletar_serie(serie=serie, data_inicio=data_inicio_br)
            salvar_raw(engine, run_id, metadata, "BCB", data_inicio_iso, None)

            erros = []
            erros += validar_dataframe_nao_vazio(df)
            erros += validar_colunas_obrigatorias(df, ["data", "valor", "indicador", "codigo_serie"])
            erros += validar_valor_numerico(df, "valor")

            if erros:
                for erro in erros:
                    registrar_dq(engine, run_id, "BCB", "staging.bcb_series", "validacao_bcb", "ERRO", 0, erro)

                tempo = time.perf_counter() - inicio
                registrar_controle_carga(
                    engine, run_id, serie, data_inicio_iso,
                    "ERRO_VALIDACAO", "; ".join(erros),
                    qtd_raw=len(metadata.get("payload", [])),
                    qtd_staging=0,
                    qtd_dw=0,
                    qtd_rejeitados=len(metadata.get("payload", [])),
                    tempo_execucao=tempo,
                )
                finalizar_run(engine, run_id, "ERRO_VALIDACAO", "; ".join(erros))
                continue

            df["data_inicio_fonte"] = df["data"].min()
            df["data_fim_fonte"] = df["data"].max()

            qtd_staging = salvar_staging_bcb(engine, run_id, df)
            qtd_dw = upsert_fato_serie_historica(engine, df)

            registrar_dq(engine, run_id, "BCB", "dw.fato_serie_historica", "carga_bcb", "OK", qtd_dw, "Carga realizada com sucesso")

            tempo = time.perf_counter() - inicio
            registrar_controle_carga(
                engine, run_id, serie, data_inicio_iso,
                "SUCESSO", "Carga concluída",
                qtd_raw=len(metadata.get("payload", [])),
                qtd_staging=qtd_staging,
                qtd_dw=qtd_dw,
                qtd_rejeitados=0,
                tempo_execucao=tempo,
            )
            finalizar_run(engine, run_id, "SUCESSO", "Carga concluída")
            logger.info("Carga concluída | %s | registros=%s", serie.indicador, qtd_dw)

        except Exception as exc:
            tempo = time.perf_counter() - inicio
            logger.exception("Erro na carga BCB | %s", serie.indicador)

            registrar_controle_carga(
                engine, run_id, serie, data_inicio_iso,
                "ERRO_API", str(exc),
                qtd_raw=0,
                qtd_staging=0,
                qtd_dw=0,
                qtd_rejeitados=0,
                tempo_execucao=tempo,
            )
            finalizar_run(engine, run_id, "ERRO_API", str(exc))

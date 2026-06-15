from __future__ import annotations

import json
import time
import uuid
import math
from sqlalchemy import text
import pandas as pd

from src.database.connection import get_engine
from src.collectors.ibge_collector import IBGECollector
from src.config.settings import settings
from src.utils.logs import get_logger
from src.utils.data_quality import validar_dataframe_nao_vazio, validar_colunas_obrigatorias


logger = get_logger(__name__)


INT_FIELDS = {
    "id_uf",
    "id_regiao",
    "id_microrregiao",
    "id_mesorregiao",
}


def clean_value(value):
    """Converte NaN/pandas NA para None antes de enviar ao PostgreSQL."""
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, float) and math.isnan(value):
        return None

    return value


def clean_records(df: pd.DataFrame, int_fields: set[str] | None = None) -> list[dict]:
    """Converte DataFrame em lista de dicts sem NaN e com ints Python puros."""
    int_fields = int_fields or set()

    registros = []
    df_obj = df.astype(object)

    for row in df_obj.to_dict(orient="records"):
        clean = {}
        for key, value in row.items():
            value = clean_value(value)

            if key in int_fields and value is not None:
                value = int(value)

            clean[key] = value

        registros.append(clean)

    return registros


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


def salvar_raw(engine, run_id: str, metadata: dict, fonte: str):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO raw.api_payload (
                    run_id,
                    fonte,
                    endpoint,
                    parametros,
                    payload,
                    status_http
                )
                VALUES (
                    :run_id,
                    :fonte,
                    :endpoint,
                    CAST(:parametros AS JSONB),
                    CAST(:payload AS JSONB),
                    :status_http
                )
            """),
            {
                "run_id": run_id,
                "fonte": fonte,
                "endpoint": metadata.get("url"),
                "parametros": json.dumps(metadata.get("params", {}), ensure_ascii=False),
                "payload": json.dumps(metadata.get("payload", []), ensure_ascii=False),
                "status_http": metadata.get("status_http"),
            },
        )


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
    indicador: str,
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
                    'IBGE',
                    :indicador,
                    NULL,
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
                "indicador": indicador,
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


def salvar_staging_ufs(engine, run_id: str, df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    temp = df.copy()
    temp["run_id"] = run_id
    registros = clean_records(temp, int_fields=INT_FIELDS)

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM staging.ibge_ufs WHERE run_id = :run_id"), {"run_id": run_id})
        conn.execute(
            text("""
                INSERT INTO staging.ibge_ufs (
                    run_id,
                    id_uf,
                    sigla_uf,
                    nome_uf,
                    id_regiao,
                    sigla_regiao,
                    nome_regiao
                )
                VALUES (
                    :run_id,
                    :id_uf,
                    :sigla_uf,
                    :nome_uf,
                    :id_regiao,
                    :sigla_regiao,
                    :nome_regiao
                )
            """),
            registros,
        )

    return len(registros)


def salvar_staging_municipios(engine, run_id: str, df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    temp = df.copy()
    temp["run_id"] = run_id
    registros = clean_records(temp, int_fields=INT_FIELDS)

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM staging.ibge_municipios WHERE run_id = :run_id"), {"run_id": run_id})
        conn.execute(
            text("""
                INSERT INTO staging.ibge_municipios (
                    run_id,
                    codigo_ibge,
                    municipio,
                    id_microrregiao,
                    microrregiao,
                    id_mesorregiao,
                    mesorregiao,
                    id_uf,
                    sigla_uf,
                    nome_uf,
                    id_regiao,
                    sigla_regiao,
                    nome_regiao
                )
                VALUES (
                    :run_id,
                    :codigo_ibge,
                    :municipio,
                    :id_microrregiao,
                    :microrregiao,
                    :id_mesorregiao,
                    :mesorregiao,
                    :id_uf,
                    :sigla_uf,
                    :nome_uf,
                    :id_regiao,
                    :sigla_regiao,
                    :nome_regiao
                )
            """),
            registros,
        )

    return len(registros)


def upsert_dim_geografia(engine, df_municipios: pd.DataFrame) -> int:
    if df_municipios.empty:
        return 0

    registros = clean_records(df_municipios, int_fields=INT_FIELDS)

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO dw.dim_geografia (
                    codigo_ibge,
                    pais,
                    uf,
                    nome_uf,
                    municipio,
                    regiao_brasil,
                    sigla_regiao_brasil,
                    mesorregiao,
                    microrregiao,
                    fonte,
                    data_atualizacao
                )
                VALUES (
                    :codigo_ibge,
                    'Brasil',
                    :sigla_uf,
                    :nome_uf,
                    :municipio,
                    :nome_regiao,
                    :sigla_regiao,
                    :mesorregiao,
                    :microrregiao,
                    'IBGE',
                    NOW()
                )
                ON CONFLICT (codigo_ibge)
                DO UPDATE SET
                    uf = EXCLUDED.uf,
                    nome_uf = EXCLUDED.nome_uf,
                    municipio = EXCLUDED.municipio,
                    regiao_brasil = EXCLUDED.regiao_brasil,
                    sigla_regiao_brasil = EXCLUDED.sigla_regiao_brasil,
                    mesorregiao = EXCLUDED.mesorregiao,
                    microrregiao = EXCLUDED.microrregiao,
                    fonte = EXCLUDED.fonte,
                    data_atualizacao = NOW();
            """),
            registros,
        )

    return len(registros)


def carregar_ibge_localidades() -> None:
    engine = get_engine()
    collector = IBGECollector()

    run_id = str(uuid.uuid4())
    inicio = time.perf_counter()

    logger.info("Iniciando carga IBGE Localidades | run_id=%s", run_id)
    registrar_run(engine, run_id, "IBGE", "localidades", "INICIADO", "Carga UFs e Municípios")

    try:
        df_ufs, meta_ufs = collector.coletar_ufs()
        df_municipios, meta_municipios = collector.coletar_municipios()

        salvar_raw(engine, run_id, meta_ufs, "IBGE")
        salvar_raw(engine, run_id, meta_municipios, "IBGE")

        erros = []
        erros += validar_dataframe_nao_vazio(df_ufs)
        erros += validar_dataframe_nao_vazio(df_municipios)
        erros += validar_colunas_obrigatorias(df_ufs, ["id_uf", "sigla_uf", "nome_uf"])
        erros += validar_colunas_obrigatorias(df_municipios, ["codigo_ibge", "municipio", "sigla_uf", "nome_uf"])

        if erros:
            for erro in erros:
                registrar_dq(engine, run_id, "IBGE", "staging.ibge_municipios", "validacao_ibge", "ERRO", 0, erro)

            tempo = time.perf_counter() - inicio
            registrar_controle_carga(
                engine, run_id, "Localidades", "ERRO_VALIDACAO", "; ".join(erros),
                qtd_raw=len(meta_ufs.get("payload", [])) + len(meta_municipios.get("payload", [])),
                qtd_staging=0,
                qtd_dw=0,
                qtd_rejeitados=len(meta_ufs.get("payload", [])) + len(meta_municipios.get("payload", [])),
                tempo_execucao=tempo,
            )
            finalizar_run(engine, run_id, "ERRO_VALIDACAO", "; ".join(erros))
            return

        qtd_ufs = salvar_staging_ufs(engine, run_id, df_ufs)
        qtd_municipios = salvar_staging_municipios(engine, run_id, df_municipios)
        qtd_dw = upsert_dim_geografia(engine, df_municipios)

        tempo = time.perf_counter() - inicio

        registrar_dq(
            engine,
            run_id,
            "IBGE",
            "dw.dim_geografia",
            "carga_ibge_localidades",
            "OK",
            qtd_dw,
            "Carga de UFs e municípios concluída com sucesso",
        )

        registrar_controle_carga(
            engine,
            run_id,
            "Localidades",
            "SUCESSO",
            "Carga concluída",
            qtd_raw=len(meta_ufs.get("payload", [])) + len(meta_municipios.get("payload", [])),
            qtd_staging=qtd_ufs + qtd_municipios,
            qtd_dw=qtd_dw,
            qtd_rejeitados=0,
            tempo_execucao=tempo,
        )

        finalizar_run(engine, run_id, "SUCESSO", "Carga concluída")
        logger.info("Carga IBGE concluída | UFs=%s | Municípios=%s | DW=%s", qtd_ufs, qtd_municipios, qtd_dw)

    except Exception as exc:
        tempo = time.perf_counter() - inicio
        logger.exception("Erro na carga IBGE Localidades")

        registrar_controle_carga(
            engine,
            run_id,
            "Localidades",
            "ERRO_API",
            str(exc),
            qtd_raw=0,
            qtd_staging=0,
            qtd_dw=0,
            qtd_rejeitados=0,
            tempo_execucao=tempo,
        )
        finalizar_run(engine, run_id, "ERRO_API", str(exc))

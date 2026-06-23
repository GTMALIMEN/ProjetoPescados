from __future__ import annotations

from pathlib import Path
import json
import sys
import time
import uuid

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from sqlalchemy import text

from src.collectors.cepea_collector import CepeaTilapiaCollector
from src.database.connection import get_engine
from src.etl.load_fontes_reais import finalizar_run, registrar_controle, registrar_run, upsert_setorial
from src.config.settings import settings


def _clean_records(df: pd.DataFrame) -> list[dict]:
    out = []
    for row in df.astype(object).to_dict(orient="records"):
        out.append({k: (None if pd.isna(v) else v) for k, v in row.items()})
    return out


def _ensure_raw_payload_table(conn) -> None:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS raw.fonte_automatica_payload (
            id BIGSERIAL PRIMARY KEY,
            fonte TEXT NOT NULL,
            endpoint TEXT,
            status TEXT,
            detalhe TEXT,
            payload_json JSONB,
            criado_em TIMESTAMP DEFAULT NOW()
        )
    """))


def _registrar_raw(engine, meta: dict) -> None:
    with engine.begin() as conn:
        _ensure_raw_payload_table(conn)
        conn.execute(text("""
            INSERT INTO raw.fonte_automatica_payload (fonte, endpoint, status, detalhe, payload_json)
            VALUES (:fonte, :endpoint, :status, :detalhe, CAST(:payload_json AS JSONB))
        """), {
            "fonte": "CEPEA Tilápia Oficial",
            "endpoint": meta.get("url_final") or meta.get("url"),
            "status": meta.get("status"),
            "detalhe": meta.get("observacao") or meta.get("metodo") or "",
            "payload_json": json.dumps(meta, ensure_ascii=False, default=str),
        })


def _renomear_cepea_manual_antigo(engine) -> int:
    """Evita que planilhas antigas apareçam como CEPEA oficial no app.

    Antes desta correção, arquivos manuais podiam entrar com fonte='CEPEA' e
    subcategoria='fonte_real', gerando valores mensais incompatíveis com o site.
    A atualização preserva os dados, mas troca a fonte para deixar claro que são
    importações manuais/proxy.
    """
    with engine.begin() as conn:
        result = conn.execute(text("""
            UPDATE dw.fato_indicador_setorial
            SET fonte = 'CEPEA_MANUAL_IMPORTADO',
                subcategoria = CASE
                    WHEN COALESCE(subcategoria, '') = '' THEN 'manual_importado'
                    WHEN subcategoria ILIKE '%oficial%' THEN subcategoria
                    ELSE 'manual_importado'
                END,
                data_coleta = NOW()
            WHERE fonte = 'CEPEA'
              AND (
                    periodicidade ILIKE 'mensal'
                 OR subcategoria ILIKE 'fonte_real'
                 OR indicador ILIKE '%camar%'
                 OR produto ILIKE '%camar%'
              )
        """))
        return result.rowcount or 0


def _salvar_cepea_detalhe_raw(engine, df: pd.DataFrame) -> None:
    """Salva detalhes extras quando a tabela raw existir; não bloqueia a carga."""
    cols = [
        "data", "fonte", "indicador", "categoria", "subcategoria", "produto", "uf", "regiao",
        "valor", "unidade", "periodicidade", "data_inicio_periodo", "data_fim_periodo",
        "periodo_original", "variacao_semana_pct", "url_fonte", "hash_fonte",
    ]
    payload = df[cols].copy() if set(cols).issubset(df.columns) else df.copy()
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS raw.cepea_tilapia_payload (
                id BIGSERIAL PRIMARY KEY,
                data DATE,
                fonte TEXT,
                indicador TEXT,
                categoria TEXT,
                subcategoria TEXT,
                produto TEXT,
                uf TEXT,
                regiao TEXT,
                valor NUMERIC,
                unidade TEXT,
                periodicidade TEXT,
                data_inicio_periodo DATE,
                data_fim_periodo DATE,
                periodo_original TEXT,
                variacao_semana_pct NUMERIC,
                url_fonte TEXT,
                hash_fonte TEXT UNIQUE,
                coletado_em TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            INSERT INTO raw.cepea_tilapia_payload (
                data, fonte, indicador, categoria, subcategoria, produto, uf, regiao,
                valor, unidade, periodicidade, data_inicio_periodo, data_fim_periodo,
                periodo_original, variacao_semana_pct, url_fonte, hash_fonte
            )
            VALUES (
                :data, :fonte, :indicador, :categoria, :subcategoria, :produto, :uf, :regiao,
                :valor, :unidade, :periodicidade, :data_inicio_periodo, :data_fim_periodo,
                :periodo_original, :variacao_semana_pct, :url_fonte, :hash_fonte
            )
            ON CONFLICT (hash_fonte)
            DO UPDATE SET
                valor = EXCLUDED.valor,
                variacao_semana_pct = EXCLUDED.variacao_semana_pct,
                coletado_em = NOW()
        """), _clean_records(payload))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Carregar CEPEA oficial de tilápia direto do site")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--limite-linhas", type=int, default=0, help="0 = sem limite")
    parser.add_argument(
        "--renomear-manual-antigo",
        action="store_true",
        help="Renomeia registros antigos CEPEA mensais/manuais para CEPEA_MANUAL_IMPORTADO.",
    )
    args = parser.parse_args()

    engine = get_engine()
    run_id = str(uuid.uuid4())
    inicio = time.perf_counter()
    fonte = "CEPEA"

    registrar_run(engine, run_id, fonte, "Carga oficial CEPEA Tilápia direto do site")

    try:
        if args.renomear_manual_antigo:
            qtd_renomeados = _renomear_cepea_manual_antigo(engine)
        else:
            qtd_renomeados = 0

        collector = CepeaTilapiaCollector(timeout=args.timeout)
        df, meta = collector.coletar(limite_linhas=args.limite_linhas or None)
        meta["registros_cepea_manual_antigo_renomeados"] = qtd_renomeados
        _registrar_raw(engine, meta)

        if df.empty:
            tempo = time.perf_counter() - inicio
            mensagem = f"CEPEA oficial sem dados compatíveis | status={meta.get('status')}"
            registrar_controle(engine, run_id, fonte, "SEM_DADOS", mensagem, 0, 0, tempo)
            finalizar_run(engine, run_id, "SEM_DADOS", mensagem)
            print("⚠️ Nenhum dado CEPEA oficial capturado.")
            print("Status:", meta.get("status"))
            print("Detalhe:", meta.get("erro") or meta.get("observacao"))
            return

        _salvar_cepea_detalhe_raw(engine, df)

        df_dw = df[[
            "data", "fonte", "indicador", "categoria", "subcategoria", "produto",
            "uf", "regiao", "valor", "unidade", "periodicidade",
        ]].copy()
        qtd_dw = upsert_setorial(engine, df_dw)

        tempo = time.perf_counter() - inicio
        mensagem = (
            f"CEPEA oficial Tilápia concluído | raw={len(df)} | dw={qtd_dw} | "
            f"manual_antigo_renomeado={qtd_renomeados}"
        )
        registrar_controle(engine, run_id, fonte, "SUCESSO", mensagem, len(df), qtd_dw, tempo)
        finalizar_run(engine, run_id, "SUCESSO", mensagem)

        print(f"✅ {mensagem}")
        print("Fonte:", meta.get("url_final") or meta.get("url"))
        print("Regiões:", ", ".join(meta.get("regioes", [])))

    except Exception as exc:
        tempo = time.perf_counter() - inicio
        mensagem = str(exc)
        registrar_controle(engine, run_id, fonte, "ERRO_API", mensagem, 0, 0, tempo)
        finalizar_run(engine, run_id, "ERRO_API", mensagem)
        raise


if __name__ == "__main__":
    main()

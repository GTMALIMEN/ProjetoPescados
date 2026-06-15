
from __future__ import annotations

import json
import unicodedata
import re

import pandas as pd
from sqlalchemy import text

from src.collectors.atlas_brasil_collector import AtlasBrasilCollector
from src.database.connection import get_engine
from src.utils.logs import get_logger

logger = get_logger(__name__)


def _norm(value: str) -> str:
    value = "" if value is None or pd.isna(value) else str(value)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-zA-Z0-9]+", " ", value).strip().lower()
    return value


def carregar_idh_automatico(extra_urls: list[str] | None = None) -> dict:
    collector = AtlasBrasilCollector()
    result = collector.collect(extra_urls=extra_urls)
    metadata = result.metadata

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO raw.fonte_automatica_payload (fonte, endpoint, status, detalhe, payload_json)
            VALUES (:fonte, :endpoint, :status, :detalhe, CAST(:payload_json AS JSONB))
        """), {
            "fonte": "Atlas Brasil / IDHM",
            "endpoint": metadata.get("url_usada") or metadata.get("dataset_page") or metadata.get("undp_url"),
            "status": metadata.get("status"),
            "detalhe": metadata.get("observacao") or metadata.get("metodo") or "",
            "payload_json": json.dumps(metadata, ensure_ascii=False, default=str),
        })

    if result.df.empty:
        logger.warning("IDHM automático não carregou dados: %s", metadata)
        return {"status": "FALHA", "qtd": 0, "metadata": metadata}

    df = result.df.copy()
    df["codigo_ibge"] = df.get("codigo_ibge", pd.Series([pd.NA] * len(df))).astype("string")
    df["codigo_ibge"] = df["codigo_ibge"].str.extract(r"(\d{6,7})")[0]
    df["uf"] = df.get("uf", pd.Series([pd.NA] * len(df))).astype("string").str.upper().str.extract(r"([A-Z]{2})")[0]
    df["municipio"] = df.get("municipio", pd.Series([pd.NA] * len(df))).astype("string")

    with engine.begin() as conn:
        geo = pd.read_sql(text("""
            SELECT codigo_ibge, uf AS uf_geo, municipio AS municipio_geo
            FROM dw.dim_geografia
        """), conn)

    geo["municipio_norm"] = geo["municipio_geo"].map(_norm)
    geo["uf_norm"] = geo["uf_geo"].astype(str).str.upper()

    # First: code join
    by_code = df[df["codigo_ibge"].notna()].merge(geo, on="codigo_ibge", how="left")
    no_code = df[df["codigo_ibge"].isna()].copy()

    if not no_code.empty:
        no_code["municipio_norm"] = no_code["municipio"].map(_norm)
        no_code["uf_norm"] = no_code["uf"].astype(str).str.upper()
        no_code = no_code.merge(
            geo[["codigo_ibge", "uf_geo", "municipio_geo", "municipio_norm", "uf_norm"]],
            on=["municipio_norm", "uf_norm"],
            how="left",
        )

    out = pd.concat([by_code, no_code], ignore_index=True, sort=False)
    out["codigo_ibge"] = out["codigo_ibge"].fillna(out.get("codigo_ibge_y"))
    out["uf"] = out["uf"].fillna(out["uf_geo"])
    out["municipio"] = out["municipio"].fillna(out["municipio_geo"])

    out = out.dropna(subset=["codigo_ibge", "idhm"])
    out = out.drop_duplicates(subset=["codigo_ibge"], keep="first")

    records = []
    for row in out.to_dict(orient="records"):
        ranking = row.get("ranking")
        try:
            ranking = int(float(ranking)) if pd.notna(ranking) else None
        except Exception:
            ranking = None

        records.append({
            "codigo_ibge": str(row.get("codigo_ibge")),
            "municipio": row.get("municipio"),
            "uf": row.get("uf"),
            "ano": int(row.get("ano") or 2010),
            "idhm": row.get("idhm"),
            "idhm_renda": row.get("idhm_renda"),
            "idhm_longevidade": row.get("idhm_longevidade"),
            "idhm_educacao": row.get("idhm_educacao"),
            "ranking": ranking,
            "fonte": "Atlas Brasil / PNUD",
            "url_fonte": metadata.get("url_usada") or metadata.get("undp_url") or metadata.get("dataset_page"),
        })

    with engine.begin() as conn:
        if records:
            conn.execute(text("""
                INSERT INTO app.fato_idhm_municipal (
                    codigo_ibge, municipio, uf, ano, idhm, idhm_renda, idhm_longevidade,
                    idhm_educacao, ranking, fonte, url_fonte
                )
                VALUES (
                    :codigo_ibge, :municipio, :uf, :ano, :idhm, :idhm_renda, :idhm_longevidade,
                    :idhm_educacao, :ranking, :fonte, :url_fonte
                )
                ON CONFLICT (codigo_ibge)
                DO UPDATE SET
                    municipio = EXCLUDED.municipio,
                    uf = EXCLUDED.uf,
                    ano = EXCLUDED.ano,
                    idhm = EXCLUDED.idhm,
                    idhm_renda = EXCLUDED.idhm_renda,
                    idhm_longevidade = EXCLUDED.idhm_longevidade,
                    idhm_educacao = EXCLUDED.idhm_educacao,
                    ranking = EXCLUDED.ranking,
                    fonte = EXCLUDED.fonte,
                    url_fonte = EXCLUDED.url_fonte,
                    data_carga = NOW();
            """), records)

        updated = conn.execute(text("""
            UPDATE app.fato_expansao_municipio e
            SET idh = i.idhm,
                idhm_ano = i.ano,
                idhm_renda = i.idhm_renda,
                idhm_longevidade = i.idhm_longevidade,
                idhm_educacao = i.idhm_educacao,
                fonte_idh = i.fonte || ' (' || i.ano || ')',
                data_atualizacao = NOW()
            FROM app.fato_idhm_municipal i
            WHERE e.codigo_ibge = i.codigo_ibge;
        """)).rowcount

    return {
        "status": "OK",
        "qtd": len(records),
        "municipios_atualizados": updated,
        "metadata": metadata,
    }

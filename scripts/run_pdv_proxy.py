
from __future__ import annotations

from pathlib import Path
import sys
import math
import json

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


def _ceil_min(value: float, min_value: int = 0) -> int:
    if value is None or pd.isna(value):
        return min_value
    return max(min_value, int(math.ceil(float(value))))


def _calc_pdv(row: dict) -> dict:
    pop = row.get("populacao") or 0
    renda = row.get("renda_media")
    pib_pc = row.get("pib_per_capita")

    try:
        pop = float(pop or 0)
    except Exception:
        pop = 0

    renda_factor = 1.0
    try:
        if renda and float(renda) > 3500:
            renda_factor += 0.12
        elif renda and float(renda) < 1600:
            renda_factor -= 0.08
    except Exception:
        pass

    try:
        if pib_pc and float(pib_pc) > 100:
            renda_factor += 0.08
    except Exception:
        pass

    # Proxy operacional: útil para ranking, não para contagem oficial.
    supermercados = _ceil_min((pop / 18000) * renda_factor, 1 if pop > 15000 else 0)
    restaurantes = _ceil_min((pop / 4200) * renda_factor, 1 if pop > 8000 else 0)
    peixarias = _ceil_min((pop / 65000) * renda_factor, 0)
    outros_pdv = _ceil_min((pop / 12000) * renda_factor, 1 if pop > 12000 else 0)

    return {
        "supermercados": supermercados,
        "restaurantes": restaurantes,
        "peixarias": peixarias,
        "outros_pdv": outros_pdv,
        "payload_json": {
            "populacao": pop,
            "renda_media": renda,
            "pib_per_capita": pib_pc,
            "renda_factor": renda_factor,
            "formula": {
                "supermercados": "ceil(pop/18000*renda_factor)",
                "restaurantes": "ceil(pop/4200*renda_factor)",
                "peixarias": "ceil(pop/65000*renda_factor)",
                "outros_pdv": "ceil(pop/12000*renda_factor)",
            }
        }
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Etapa 25 — PDV proxy: supermercados/restaurantes/peixarias/outros")
    parser.add_argument("--estados", default="MG,SP,RJ,ES")
    parser.add_argument("--sobrescrever", action="store_true")
    args = parser.parse_args()

    estados = [x.strip().upper() for x in args.estados.split(",") if x.strip()]
    engine = get_engine()

    with engine.begin() as conn:
        df = pd.read_sql(text("""
            SELECT codigo_ibge, uf, municipio, populacao, renda_media, pib_per_capita,
                   supermercados, restaurantes, peixarias, outros_pdv
            FROM app.fato_expansao_municipio
            WHERE uf = ANY(:estados)
            ORDER BY uf, municipio
        """), conn, params={"estados": estados})

    if df.empty:
        print("⚠️ Nenhum município encontrado. Rode antes a expansão pública.")
        return

    records = []
    for row in df.to_dict(orient="records"):
        if not args.sobrescrever and any(row.get(c) is not None for c in ["supermercados", "restaurantes", "peixarias", "outros_pdv"]):
            continue

        pdv = _calc_pdv(row)
        records.append({
            "codigo_ibge": str(row["codigo_ibge"]),
            "uf": row["uf"],
            "municipio": row.get("municipio"),
            "supermercados": pdv["supermercados"],
            "restaurantes": pdv["restaurantes"],
            "peixarias": pdv["peixarias"],
            "outros_pdv": pdv["outros_pdv"],
            "fonte_pdv": "Proxy estimado por população/renda — não oficial",
            "metodo": "pdv_proxy_pop_renda_v1",
            "nivel_confianca": 45,
            "payload_json": json.dumps(pdv["payload_json"], ensure_ascii=False),
        })

    if not records:
        print("✅ PDV já preenchido. Use --sobrescrever para recalcular.")
        return

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.fato_pdv_proxy_municipio (
                codigo_ibge, uf, municipio, supermercados, restaurantes, peixarias, outros_pdv,
                fonte_pdv, metodo, nivel_confianca, payload_json
            )
            VALUES (
                :codigo_ibge, :uf, :municipio, :supermercados, :restaurantes, :peixarias, :outros_pdv,
                :fonte_pdv, :metodo, :nivel_confianca, CAST(:payload_json AS JSONB)
            )
            ON CONFLICT (codigo_ibge)
            DO UPDATE SET
                uf = EXCLUDED.uf,
                municipio = EXCLUDED.municipio,
                supermercados = EXCLUDED.supermercados,
                restaurantes = EXCLUDED.restaurantes,
                peixarias = EXCLUDED.peixarias,
                outros_pdv = EXCLUDED.outros_pdv,
                fonte_pdv = EXCLUDED.fonte_pdv,
                metodo = EXCLUDED.metodo,
                nivel_confianca = EXCLUDED.nivel_confianca,
                payload_json = EXCLUDED.payload_json,
                data_atualizacao = NOW();
        """), records)

        conn.execute(text("""
            UPDATE app.fato_expansao_municipio e
            SET
                supermercados = p.supermercados,
                restaurantes = p.restaurantes,
                peixarias = p.peixarias,
                outros_pdv = p.outros_pdv,
                fonte_pdv = p.fonte_pdv,
                data_atualizacao = NOW()
            FROM app.fato_pdv_proxy_municipio p
            WHERE e.codigo_ibge = p.codigo_ibge
              AND e.uf = ANY(:estados);
        """), {"estados": estados})

    print("\n✅ Etapa 25 concluída — PDV proxy preenchido.")
    print(f"- municípios processados: {len(records)}")
    print("- fonte_pdv: Proxy estimado por população/renda — não oficial")


if __name__ == "__main__":
    main()

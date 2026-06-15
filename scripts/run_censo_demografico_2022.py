
from __future__ import annotations

from pathlib import Path
import sys
import math

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


UF_PROFILE = {
    # Perfis iniciais por UF para preencher a estrutura até a carga SIDRA fina.
    # Percentuais somam 100 nas faixas etárias.
    "MG": {"masc": 49.2, "fem": 50.8, "a0_14": 19.0, "a15_29": 22.5, "a30_44": 23.0, "a45_59": 20.0, "a60": 15.5},
    "SP": {"masc": 48.7, "fem": 51.3, "a0_14": 18.2, "a15_29": 21.8, "a30_44": 23.8, "a45_59": 20.5, "a60": 15.7},
    "RJ": {"masc": 47.6, "fem": 52.4, "a0_14": 17.0, "a15_29": 21.0, "a30_44": 23.0, "a45_59": 21.0, "a60": 18.0},
    "ES": {"masc": 49.0, "fem": 51.0, "a0_14": 19.0, "a15_29": 22.5, "a30_44": 23.0, "a45_59": 20.0, "a60": 15.5},
}


def _renda_media_proxy(row: dict) -> float | None:
    """Proxy conservador de renda média mensal a partir de PIB per capita.

    O PIB municipal da tabela atual costuma estar em mil R$.
    A conversão abaixo não pretende ser dado oficial: é apenas estimativa
    operacional até carga de renda do Censo/SIDRA/POF.
    """
    pib_pc = row.get("pib_per_capita")
    pop = row.get("populacao")
    try:
        pib_pc = float(pib_pc) if pib_pc is not None else None
    except Exception:
        pib_pc = None
    if pib_pc is None or math.isnan(pib_pc) or pib_pc <= 0:
        return None

    # Se estiver em mil R$/ano, transforma em R$/ano. Depois aproxima renda mensal.
    anual_reais = pib_pc * 1000 if pib_pc < 1000 else pib_pc
    renda = anual_reais / 12 * 0.38

    # Limites defensivos para não criar extremos absurdos.
    return round(max(900, min(renda, 8500)), 2)


def _classes_renda_proxy(renda_media: float | None) -> tuple[float | None, float | None, float | None, float | None]:
    if renda_media is None:
        return None, None, None, None

    # Distribuição aproximada em % das famílias/classes econômicas.
    # Mais renda desloca participação para A/B, mas mantém soma 100.
    a = min(18.0, max(2.0, (renda_media - 1800) / 450))
    b = min(30.0, max(8.0, 12 + (renda_media - 1800) / 350))
    c = min(45.0, max(28.0, 42 - (renda_media - 2500) / 900))
    de = max(5.0, 100 - a - b - c)

    total = a + b + c + de
    return round(a / total * 100, 4), round(b / total * 100, 4), round(c / total * 100, 4), round(de / total * 100, 4)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Etapa 24 — Censo Demográfico 2022: sexo, faixa etária, renda e classes")
    parser.add_argument("--estados", default="MG,SP,RJ,ES", help="Lista de UFs separadas por vírgula")
    parser.add_argument("--modo", default="proxy", choices=["proxy"], help="Modo atual: proxy controlado até carga SIDRA fina")
    parser.add_argument("--sobrescrever", action="store_true", help="Sobrescreve valores já preenchidos")
    args = parser.parse_args()

    estados = [x.strip().upper() for x in args.estados.split(",") if x.strip()]
    engine = get_engine()

    with engine.begin() as conn:
        df = pd.read_sql(text("""
            SELECT codigo_ibge, uf, municipio, populacao, pib, pib_per_capita,
                   pct_masculina, pct_feminina, renda_media
            FROM app.fato_expansao_municipio
            WHERE uf = ANY(:estados)
            ORDER BY uf, municipio
        """), conn, params={"estados": estados})

    if df.empty:
        print("⚠️ Nenhum município encontrado. Rode antes a carga de expansão pública.")
        return

    records = []
    for row in df.to_dict(orient="records"):
        if not args.sobrescrever and row.get("pct_masculina") is not None and row.get("renda_media") is not None:
            continue

        uf = row["uf"]
        prof = UF_PROFILE.get(uf, UF_PROFILE["MG"])
        renda = _renda_media_proxy(row)
        a, b, c, de = _classes_renda_proxy(renda)

        records.append({
            "codigo_ibge": str(row["codigo_ibge"]),
            "uf": uf,
            "municipio": row.get("municipio"),
            "ano": 2022,
            "populacao": row.get("populacao"),
            "pct_masculina": prof["masc"],
            "pct_feminina": prof["fem"],
            "pct_0_14": prof["a0_14"],
            "pct_15_29": prof["a15_29"],
            "pct_30_44": prof["a30_44"],
            "pct_45_59": prof["a45_59"],
            "pct_60_plus": prof["a60"],
            "renda_media": renda,
            "renda_classe_a": a,
            "renda_classe_b": b,
            "renda_classe_c": c,
            "renda_classe_de": de,
            "fonte_demografia": "Proxy controlado baseado em Censo 2022 por UF; substituir por SIDRA municipal fino",
            "fonte_renda": "Proxy operacional por PIB per capita; substituir por Censo/SIDRA/POF",
            "metodo": "proxy_censo_2022_uf_v1",
            "nivel_confianca": 55,
        })

    if not records:
        print("✅ Demografia/renda já preenchidas. Use --sobrescrever para recalcular.")
        return

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.fato_demografia_renda_municipio (
                codigo_ibge, uf, municipio, ano, populacao,
                pct_masculina, pct_feminina, pct_0_14, pct_15_29, pct_30_44,
                pct_45_59, pct_60_plus,
                renda_media, renda_classe_a, renda_classe_b, renda_classe_c, renda_classe_de,
                fonte_demografia, fonte_renda, metodo, nivel_confianca
            )
            VALUES (
                :codigo_ibge, :uf, :municipio, :ano, :populacao,
                :pct_masculina, :pct_feminina, :pct_0_14, :pct_15_29, :pct_30_44,
                :pct_45_59, :pct_60_plus,
                :renda_media, :renda_classe_a, :renda_classe_b, :renda_classe_c, :renda_classe_de,
                :fonte_demografia, :fonte_renda, :metodo, :nivel_confianca
            )
            ON CONFLICT (codigo_ibge)
            DO UPDATE SET
                uf = EXCLUDED.uf,
                municipio = EXCLUDED.municipio,
                ano = EXCLUDED.ano,
                populacao = EXCLUDED.populacao,
                pct_masculina = EXCLUDED.pct_masculina,
                pct_feminina = EXCLUDED.pct_feminina,
                pct_0_14 = EXCLUDED.pct_0_14,
                pct_15_29 = EXCLUDED.pct_15_29,
                pct_30_44 = EXCLUDED.pct_30_44,
                pct_45_59 = EXCLUDED.pct_45_59,
                pct_60_plus = EXCLUDED.pct_60_plus,
                renda_media = EXCLUDED.renda_media,
                renda_classe_a = EXCLUDED.renda_classe_a,
                renda_classe_b = EXCLUDED.renda_classe_b,
                renda_classe_c = EXCLUDED.renda_classe_c,
                renda_classe_de = EXCLUDED.renda_classe_de,
                fonte_demografia = EXCLUDED.fonte_demografia,
                fonte_renda = EXCLUDED.fonte_renda,
                metodo = EXCLUDED.metodo,
                nivel_confianca = EXCLUDED.nivel_confianca,
                data_atualizacao = NOW();
        """), records)

        conn.execute(text("""
            UPDATE app.fato_expansao_municipio e
            SET
                pct_masculina = d.pct_masculina,
                pct_feminina = d.pct_feminina,
                pct_0_14 = d.pct_0_14,
                pct_15_29 = d.pct_15_29,
                pct_30_44 = d.pct_30_44,
                pct_45_59 = d.pct_45_59,
                pct_60_plus = d.pct_60_plus,
                renda_media = d.renda_media,
                renda_classe_a = d.renda_classe_a,
                renda_classe_b = d.renda_classe_b,
                renda_classe_c = d.renda_classe_c,
                renda_classe_de = d.renda_classe_de,
                fonte_demografia = d.fonte_demografia,
                fonte_renda = d.fonte_renda,
                data_atualizacao = NOW()
            FROM app.fato_demografia_renda_municipio d
            WHERE e.codigo_ibge = d.codigo_ibge
              AND e.uf = ANY(:estados);
        """), {"estados": estados})

    print("\n✅ Etapa 24 concluída — demografia/renda preenchidas.")
    print(f"- municípios processados: {len(records)}")
    print("- método: proxy_censo_2022_uf_v1")
    print("- observação: fonte marcada como proxy/controlada até carga SIDRA fina.")


if __name__ == "__main__":
    main()

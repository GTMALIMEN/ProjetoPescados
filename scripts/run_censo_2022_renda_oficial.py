from pathlib import Path
import sys
import time
import requests
import pandas as pd
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database.connection import get_engine

BASE_URL = "https://apisidra.ibge.gov.br/values/t/10295"

VAR_RENDA_MEDIA = "13431"
VAR_RENDA_MEDIANA = "13534"



def normalizar_valor(v):
    if v is None:
        return None

    s = str(v).strip()

    if s in {"", "-", "...", "X", "x"}:
        return None

    # SIDRA pode retornar:
    # 2748.85  -> decimal com ponto
    # 2.748,85 -> milhar com ponto e decimal com vírgula
    # 2748,85  -> decimal com vírgula
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    else:
        # Se tiver só ponto, mantém como decimal
        s = s

    try:
        return float(s)
    except Exception:
        return None


def coletar_renda_municipio(codigo_ibge):
    codigo_ibge = str(codigo_ibge).strip()

    url = (
        f"{BASE_URL}/n6/{codigo_ibge}"
        f"/v/{VAR_RENDA_MEDIA},{VAR_RENDA_MEDIANA}"
        f"/p/2022?formato=json"
    )

    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    data = resp.json()

    if not data or len(data) < 2:
        return None

    header = data[0]
    rows = data[1:]

    out = {
        "codigo_ibge": codigo_ibge,
        "municipio": None,
        "renda_media": None,
        "renda_mediana": None,
        "fonte_renda": "IBGE SIDRA Censo 2022 tabela 10295",
        "metodo_renda": "sidra_api_10295",
        "nivel_confianca_renda": 100,
    }

    for r in rows:
        municipio = r.get("D1N")
        var_cod = str(r.get("D2C", "")).strip()
        valor = normalizar_valor(r.get("V"))

        if municipio:
            out["municipio"] = municipio

        if var_cod == VAR_RENDA_MEDIA:
            out["renda_media"] = valor

        elif var_cod == VAR_RENDA_MEDIANA:
            out["renda_mediana"] = valor

    return out


def main():
    engine = get_engine()

    with engine.begin() as conn:
        municipios = pd.read_sql(
            text("""
                SELECT DISTINCT codigo_ibge::text AS codigo_ibge, uf
                FROM app.fato_expansao_municipio
                WHERE uf IN ('MG','SP','RJ','ES')
                  AND codigo_ibge IS NOT NULL
                ORDER BY uf, codigo_ibge
            """),
            conn,
        )

    if municipios.empty:
        print("Nenhum município encontrado em app.fato_expansao_municipio.")
        return

    print(f"Municípios para coletar renda: {len(municipios)}")

    registros = []
    erros = []

    for i, row in municipios.iterrows():
        codigo = row["codigo_ibge"]

        print(f"Coletando renda SIDRA 10295: {i + 1}/{len(municipios)} | {codigo}")

        try:
            item = coletar_renda_municipio(codigo)

            if item and item.get("renda_media") is not None:
                item["uf"] = row["uf"]
                registros.append(item)
                print(f"   ✅ renda_media={item['renda_media']}")
            else:
                erros.append({"codigo_ibge": codigo, "uf": row["uf"], "erro": "sem renda_media"})
                print("   ⚠️ sem renda_media")

        except Exception as e:
            erros.append({"codigo_ibge": codigo, "uf": row["uf"], "erro": str(e)})
            print(f"   ⚠️ erro: {e}")

        time.sleep(0.12)

    if not registros:
        print("Nenhum dado de renda foi coletado.")
        if erros:
            print(pd.DataFrame(erros).head(20).to_string(index=False))
        return

    df = pd.DataFrame(registros)

    print(f"Municípios com renda coletada: {len(df)}")

    df.to_sql(
        "tmp_censo_2022_renda",
        engine,
        schema="app",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
    )

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS app.fato_demografia_renda_municipio (
                codigo_ibge TEXT PRIMARY KEY
            );

            ALTER TABLE app.fato_demografia_renda_municipio
                ADD COLUMN IF NOT EXISTS uf TEXT,
                ADD COLUMN IF NOT EXISTS municipio TEXT,
                ADD COLUMN IF NOT EXISTS ano INTEGER DEFAULT 2022,
                ADD COLUMN IF NOT EXISTS renda_media NUMERIC,
                ADD COLUMN IF NOT EXISTS renda_mediana NUMERIC,
                ADD COLUMN IF NOT EXISTS fonte_renda TEXT,
                ADD COLUMN IF NOT EXISTS metodo_renda TEXT,
                ADD COLUMN IF NOT EXISTS nivel_confianca_renda INTEGER,
                ADD COLUMN IF NOT EXISTS data_atualizacao TIMESTAMP DEFAULT NOW();

            ALTER TABLE app.fato_expansao_municipio
                ADD COLUMN IF NOT EXISTS renda_media NUMERIC,
                ADD COLUMN IF NOT EXISTS renda_mediana NUMERIC,
                ADD COLUMN IF NOT EXISTS fonte_renda TEXT;

            INSERT INTO app.fato_demografia_renda_municipio (
                codigo_ibge,
                uf,
                municipio,
                ano,
                renda_media,
                renda_mediana,
                fonte_renda,
                metodo_renda,
                nivel_confianca_renda,
                data_atualizacao
            )
            SELECT
                codigo_ibge::text,
                uf,
                municipio,
                2022,
                renda_media,
                renda_mediana,
                fonte_renda,
                metodo_renda,
                nivel_confianca_renda,
                NOW()
            FROM app.tmp_censo_2022_renda
            ON CONFLICT (codigo_ibge) DO UPDATE SET
                uf = EXCLUDED.uf,
                municipio = COALESCE(app.fato_demografia_renda_municipio.municipio, EXCLUDED.municipio),
                renda_media = EXCLUDED.renda_media,
                renda_mediana = EXCLUDED.renda_mediana,
                fonte_renda = EXCLUDED.fonte_renda,
                metodo_renda = EXCLUDED.metodo_renda,
                nivel_confianca_renda = EXCLUDED.nivel_confianca_renda,
                data_atualizacao = NOW();

            UPDATE app.fato_expansao_municipio e
            SET
                renda_media = d.renda_media,
                renda_mediana = d.renda_mediana,
                fonte_renda = 'IBGE SIDRA Censo 2022 tabela 10295',
                data_atualizacao = NOW()
            FROM app.fato_demografia_renda_municipio d
            WHERE e.codigo_ibge::text = d.codigo_ibge
              AND e.uf IN ('MG','SP','RJ','ES');

            DROP TABLE IF EXISTS app.tmp_censo_2022_renda;
        """))

    if erros:
        pd.DataFrame(erros).to_sql(
            "etl_censo_2022_renda_erros",
            engine,
            schema="app",
            if_exists="replace",
            index=False,
        )

    print("✅ Renda oficial IBGE/SIDRA 10295 carregada e aplicada.")
    print(f"Municípios atualizados: {len(df)}")
    print(f"Municípios com erro: {len(erros)}")


if __name__ == "__main__":
    main()

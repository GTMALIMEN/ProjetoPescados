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

SIDRA_TABELA = "4712"
SIDRA_ANO = "2022"
FONTE = "IBGE SIDRA Censo 2022 tabela 4712"


def to_num(v):
    if v is None:
        return None

    s = str(v).strip()

    if s in {"", "-", "...", "X", "x", "N/A", "NaN"}:
        return None

    s = s.replace(" ", "")

    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")

    try:
        return float(s)
    except Exception:
        return None


def normaliza_codigo(c):
    if c is None:
        return None
    return str(c).strip().split(".")[0]


def buscar_sidra_codigos(codigos):
    codigos_txt = ",".join(codigos)

    url = (
        f"https://apisidra.ibge.gov.br/values/"
        f"t/{SIDRA_TABELA}/n6/{codigos_txt}/v/all/p/{SIDRA_ANO}?formato=json"
    )

    resp = requests.get(url, timeout=120)

    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code} | {resp.text[:500]}")

    data = resp.json()

    if not data or len(data) < 2:
        return pd.DataFrame()

    header = data[0]
    df = pd.DataFrame(data[1:])

    # Renomeia para nomes humanos quando possível
    df = df.rename(columns={k: v for k, v in header.items() if k in df.columns})

    return df


def parse_4712(df_raw):
    if df_raw.empty:
        return pd.DataFrame()

    col_codigo = next((c for c in df_raw.columns if "Município (Código)" in c), None)
    col_variavel = next((c for c in df_raw.columns if c == "Variável" or "Variável" in c and "Código" not in c), None)
    col_valor = "Valor" if "Valor" in df_raw.columns else "V"

    if not col_codigo or not col_variavel or col_valor not in df_raw.columns:
        raise RuntimeError(f"Colunas inesperadas no retorno SIDRA 4712: {list(df_raw.columns)}")

    registros = {}

    for _, row in df_raw.iterrows():
        codigo = normaliza_codigo(row.get(col_codigo))
        variavel = str(row.get(col_variavel, "")).lower()
        valor = to_num(row.get(col_valor))

        if not codigo:
            continue

        if codigo not in registros:
            registros[codigo] = {
                "codigo_ibge": codigo,
                "domicilios_particulares_ocupados": None,
                "moradores_domicilios_particulares_ocupados": None,
                "moradores_por_domicilio": None,
            }

        if "média de moradores" in variavel or "media de moradores" in variavel:
            registros[codigo]["moradores_por_domicilio"] = valor

        elif "moradores em domicílios particulares permanentes ocupados" in variavel or "moradores em domicilios particulares permanentes ocupados" in variavel:
            registros[codigo]["moradores_domicilios_particulares_ocupados"] = valor

        elif "domicílios particulares permanentes ocupados" in variavel or "domicilios particulares permanentes ocupados" in variavel:
            registros[codigo]["domicilios_particulares_ocupados"] = valor

    out = pd.DataFrame(list(registros.values()))

    if out.empty:
        return out

    # Fallback: se a média não vier, calcula moradores / domicílios
    dom = pd.to_numeric(out["domicilios_particulares_ocupados"], errors="coerce")
    mor = pd.to_numeric(out["moradores_domicilios_particulares_ocupados"], errors="coerce")
    media = pd.to_numeric(out["moradores_por_domicilio"], errors="coerce")

    out["moradores_por_domicilio"] = media.where(
        media.notna(),
        mor.where(dom > 0) / dom.where(dom > 0)
    )

    return out


def chunks(lista, n):
    for i in range(0, len(lista), n):
        yield lista[i:i+n]


def main():
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE app.fato_expansao_municipio
                ADD COLUMN IF NOT EXISTS domicilios_particulares_ocupados NUMERIC,
                ADD COLUMN IF NOT EXISTS moradores_domicilios_particulares_ocupados NUMERIC,
                ADD COLUMN IF NOT EXISTS moradores_por_domicilio NUMERIC,
                ADD COLUMN IF NOT EXISTS fonte_moradores_domicilio TEXT,
                ADD COLUMN IF NOT EXISTS data_carga_moradores_domicilio TIMESTAMP;

            CREATE TABLE IF NOT EXISTS app.auditoria_fonte_dados (
                id BIGSERIAL PRIMARY KEY,
                nome_fonte TEXT NOT NULL,
                tabela_destino TEXT,
                status TEXT NOT NULL,
                registros INTEGER DEFAULT 0,
                registros_distintos INTEGER DEFAULT 0,
                duplicatas INTEGER DEFAULT 0,
                nulos_criticos INTEGER DEFAULT 0,
                data_min DATE,
                data_max DATE,
                detalhe TEXT,
                executado_em TIMESTAMP DEFAULT NOW()
            );
        """))

        rows = conn.execute(text("""
            SELECT DISTINCT codigo_ibge::text AS codigo_ibge
            FROM app.fato_expansao_municipio
            WHERE codigo_ibge IS NOT NULL
              AND uf IN ('MG','SP','RJ','ES')
            ORDER BY codigo_ibge
        """)).fetchall()

    codigos = [normaliza_codigo(r[0]) for r in rows if normaliza_codigo(r[0])]

    print(f"Municípios para buscar no IBGE/SIDRA 4712: {len(codigos)}")

    todos = []

    for idx, parte in enumerate(chunks(codigos, 80), start=1):
        print(f"Coletando SIDRA 4712: lote {idx} | {len(parte)} municípios")

        try:
            raw = buscar_sidra_codigos(parte)
            parsed = parse_4712(raw)
            todos.append(parsed)
        except Exception as e:
            print(f"⚠️ Lote falhou, tentando individualmente. Erro: {e}")

            for codigo in parte:
                try:
                    raw = buscar_sidra_codigos([codigo])
                    parsed = parse_4712(raw)
                    todos.append(parsed)
                    time.sleep(0.1)
                except Exception as e2:
                    print(f"   ❌ Falhou município {codigo}: {e2}")

        time.sleep(0.3)

    if not todos:
        raise RuntimeError("Nenhum dado retornado do SIDRA 4712.")

    df = pd.concat(todos, ignore_index=True)
    df = df.drop_duplicates(subset=["codigo_ibge"], keep="last")

    print(f"Registros SIDRA 4712 tratados: {len(df)}")

    nulos = df["moradores_por_domicilio"].isna().sum()
    print(f"Registros sem média de moradores: {nulos}")

    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                UPDATE app.fato_expansao_municipio
                SET
                    domicilios_particulares_ocupados = :domicilios,
                    moradores_domicilios_particulares_ocupados = :moradores,
                    moradores_por_domicilio = :media,
                    fonte_moradores_domicilio = :fonte,
                    data_carga_moradores_domicilio = NOW()
                WHERE codigo_ibge::text = :codigo
            """), {
                "codigo": str(row["codigo_ibge"]),
                "domicilios": row["domicilios_particulares_ocupados"],
                "moradores": row["moradores_domicilios_particulares_ocupados"],
                "media": row["moradores_por_domicilio"],
                "fonte": FONTE,
            })

        conn.execute(text("""
            INSERT INTO app.auditoria_fonte_dados (
                nome_fonte,
                tabela_destino,
                status,
                registros,
                registros_distintos,
                duplicatas,
                nulos_criticos,
                detalhe
            )
            VALUES (
                :fonte,
                'app.fato_expansao_municipio',
                :status,
                :registros,
                :distintos,
                :duplicatas,
                :nulos,
                :detalhe
            )
        """), {
            "fonte": FONTE,
            "status": "OK" if nulos == 0 else "OK_COM_NULOS",
            "registros": int(len(df)),
            "distintos": int(df["codigo_ibge"].nunique()),
            "duplicatas": int(len(df) - df["codigo_ibge"].nunique()),
            "nulos": int(nulos),
            "detalhe": "Carga oficial SIDRA 4712: domicílios, moradores e média de moradores por domicílio.",
        })

    print("✅ Carga IBGE SIDRA 4712 finalizada.")
    print("✅ Coluna moradores_por_domicilio atualizada no banco.")


if __name__ == "__main__":
    main()

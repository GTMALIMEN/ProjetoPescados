from pathlib import Path
import sys
import time
import re
import unicodedata
import requests
import pandas as pd
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database.connection import get_engine

BASE_URL = "https://apisidra.ibge.gov.br/values/t/9514"


def normalizar_texto(s):
    s = "" if s is None else str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def normalizar_valor(v):
    if v is None:
        return 0.0

    s = str(v).strip()

    if s in {"", "-", "...", "X", "x"}:
        return 0.0

    s = s.replace(".", "").replace(",", ".")

    try:
        return float(s)
    except Exception:
        return 0.0


def achar_coluna(header, termo, preferir_codigo=False):
    termo_norm = normalizar_texto(termo)

    candidatos = []
    for k, v in header.items():
        nome = normalizar_texto(v)
        if termo_norm in nome:
            candidatos.append((k, nome))

    if not candidatos:
        return None

    if preferir_codigo:
        for k, nome in candidatos:
            if "codigo" in nome:
                return k
    else:
        for k, nome in candidatos:
            if "codigo" not in nome:
                return k

    return candidatos[0][0]


def idade_intervalo(label):
    n = normalizar_texto(label)

    if not n or "total" in n or "ignorada" in n:
        return None

    if "menos de 1" in n:
        return (0, 0)

    nums = [int(x) for x in re.findall(r"\d+", n)]

    if not nums:
        return None

    if "ou mais" in n:
        return (nums[0], 120)

    if len(nums) >= 2:
        return (nums[0], nums[1])

    return (nums[0], nums[0])


def distribuir_faixa(valor, idade_ini, idade_fim):
    bins = {
        "pop_0_14": (0, 14),
        "pop_15_29": (15, 29),
        "pop_30_44": (30, 44),
        "pop_45_59": (45, 59),
        "pop_60_plus": (60, 120),
    }

    saida = {k: 0.0 for k in bins}

    if idade_ini is None or idade_fim is None:
        return saida

    idade_ini = max(0, int(idade_ini))
    idade_fim = min(120, int(idade_fim))

    if idade_fim < idade_ini:
        return saida

    total_anos = idade_fim - idade_ini + 1

    for nome, (b_ini, b_fim) in bins.items():
        ini = max(idade_ini, b_ini)
        fim = min(idade_fim, b_fim)

        if fim >= ini:
            anos = fim - ini + 1
            saida[nome] += valor * anos / total_anos

    return saida


def sidra_para_dataframe(data):
    if not data or len(data) < 2:
        return pd.DataFrame()

    header = data[0]
    rows = data[1:]

    col_mun_cod = achar_coluna(header, "município", preferir_codigo=True)
    col_mun_nome = achar_coluna(header, "município", preferir_codigo=False)
    col_sexo = achar_coluna(header, "sexo", preferir_codigo=False)
    col_idade = achar_coluna(header, "idade", preferir_codigo=False)
    col_valor = achar_coluna(header, "valor", preferir_codigo=False)

    if col_valor is None and "V" in header:
        col_valor = "V"

    faltantes = []
    if col_mun_cod is None:
        faltantes.append("codigo_municipio")
    if col_mun_nome is None:
        faltantes.append("nome_municipio")
    if col_sexo is None:
        faltantes.append("sexo")
    if col_idade is None:
        faltantes.append("idade")
    if col_valor is None:
        faltantes.append("valor")

    if faltantes:
        raise RuntimeError(f"Colunas não encontradas: {faltantes}. Header={header}")

    out = []

    for r in rows:
        out.append({
            "codigo_ibge": str(r.get(col_mun_cod, "")).strip(),
            "municipio": str(r.get(col_mun_nome, "")).strip(),
            "sexo": str(r.get(col_sexo, "")).strip(),
            "idade": str(r.get(col_idade, "")).strip(),
            "valor": normalizar_valor(r.get(col_valor)),
        })

    return pd.DataFrame(out)


def calcular_por_municipio(df):
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df["sexo_norm"] = df["sexo"].map(normalizar_texto)
    df["idade_norm"] = df["idade"].map(normalizar_texto)

    resultados = []

    for codigo, g in df.groupby("codigo_ibge"):
        municipio = g["municipio"].dropna().astype(str).iloc[0]

        sexo_total = g["sexo_norm"].eq("total")
        sexo_masc = g["sexo_norm"].isin(["homens", "homem", "masculino"])
        sexo_fem = g["sexo_norm"].isin(["mulheres", "mulher", "feminino"])
        idade_total = g["idade_norm"].eq("total")

        total = g[sexo_total & idade_total]["valor"].sum()
        homens = g[sexo_masc & idade_total]["valor"].sum()
        mulheres = g[sexo_fem & idade_total]["valor"].sum()

        if total <= 0:
            total = g[sexo_total & ~idade_total]["valor"].sum()

        if homens <= 0:
            homens = g[sexo_masc & ~idade_total]["valor"].sum()

        if mulheres <= 0:
            mulheres = g[sexo_fem & ~idade_total]["valor"].sum()

        if total <= 0 and homens + mulheres > 0:
            total = homens + mulheres

        if total <= 0:
            continue

        g_idade = g[sexo_total & ~idade_total].copy()

        faixas = {
            "pop_0_14": 0.0,
            "pop_15_29": 0.0,
            "pop_30_44": 0.0,
            "pop_45_59": 0.0,
            "pop_60_plus": 0.0,
        }

        for _, row in g_idade.iterrows():
            intervalo = idade_intervalo(row["idade"])
            if intervalo is None:
                continue

            dist = distribuir_faixa(row["valor"], intervalo[0], intervalo[1])

            for k, v in dist.items():
                faixas[k] += v

        resultados.append({
            "codigo_ibge": str(codigo),
            "municipio": municipio,
            "populacao": total,
            "pop_masculina": homens,
            "pop_feminina": mulheres,
            "pop_0_14": faixas["pop_0_14"],
            "pop_15_29": faixas["pop_15_29"],
            "pop_30_44": faixas["pop_30_44"],
            "pop_45_59": faixas["pop_45_59"],
            "pop_60_plus": faixas["pop_60_plus"],
            "pct_masculina": homens / total * 100 if total else None,
            "pct_feminina": mulheres / total * 100 if total else None,
            "pct_0_14": faixas["pop_0_14"] / total * 100 if total else None,
            "pct_15_29": faixas["pop_15_29"] / total * 100 if total else None,
            "pct_30_44": faixas["pop_30_44"] / total * 100 if total else None,
            "pct_45_59": faixas["pop_45_59"] / total * 100 if total else None,
            "pct_60_plus": faixas["pop_60_plus"] / total * 100 if total else None,
            "fonte_demografia": "IBGE SIDRA Censo 2022 tabela 9514",
            "metodo": "sidra_api_9514_n6_codigo_municipio",
            "nivel_confianca": 100,
        })

    return pd.DataFrame(resultados)


def montar_urls(codigo):
    codigo = str(codigo).strip()

    return [
        (
            "9514_n6_codigo_sem_forma",
            f"{BASE_URL}/n6/{codigo}/v/93/p/2022/c2/all/c287/all?formato=json"
        ),
        (
            "9514_n6_codigo_forma_total",
            f"{BASE_URL}/n6/{codigo}/v/93/p/2022/c2/all/c287/all/c286/113635?formato=json"
        ),
        (
            "9514_n6_codigo_forma_all",
            f"{BASE_URL}/n6/{codigo}/v/93/p/2022/c2/all/c287/all/c286/all?formato=json"
        ),
    ]


def coletar_municipio(codigo):
    ultimo_erro = None

    for nome, url in montar_urls(codigo):
        try:
            resp = requests.get(url, timeout=60)

            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 1:
                    return nome, data

            ultimo_erro = f"{nome}: HTTP {resp.status_code} | {resp.text[:250]}"

        except Exception as e:
            ultimo_erro = f"{nome}: {e}"

    raise RuntimeError(ultimo_erro)


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

    codigos = municipios["codigo_ibge"].astype(str).tolist()

    print(f"Municípios para coletar: {len(codigos)}")

    dfs = []
    erros = []

    for i, codigo in enumerate(codigos, start=1):
        print(f"Coletando SIDRA 9514: {i}/{len(codigos)} | município {codigo}")

        try:
            nome_url, data = coletar_municipio(codigo)
            df_raw = sidra_para_dataframe(data)
            df_calc = calcular_por_municipio(df_raw)

            if not df_calc.empty:
                dfs.append(df_calc)
                print(f"   ✅ OK: {nome_url}")
            else:
                erros.append({"codigo_ibge": codigo, "erro": "retorno vazio após cálculo"})
                print("   ⚠️ Retorno vazio após cálculo")

        except Exception as e:
            erros.append({"codigo_ibge": codigo, "erro": str(e)})
            print(f"   ⚠️ Falha: {e}")

        time.sleep(0.15)

    if not dfs:
        print("Nenhum dado retornado do SIDRA 9514.")
        if erros:
            print("Primeiros erros:")
            print(pd.DataFrame(erros).head(20).to_string(index=False))
        return

    df_final = pd.concat(dfs, ignore_index=True)
    df_final = df_final.merge(municipios, on="codigo_ibge", how="left")

    print(f"Registros municipais calculados: {len(df_final)}")

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS app.fato_demografia_renda_municipio (
                codigo_ibge TEXT PRIMARY KEY,
                uf TEXT,
                municipio TEXT,
                ano INTEGER DEFAULT 2022,
                populacao NUMERIC,
                pop_masculina NUMERIC,
                pop_feminina NUMERIC,
                pop_0_14 NUMERIC,
                pop_15_29 NUMERIC,
                pop_30_44 NUMERIC,
                pop_45_59 NUMERIC,
                pop_60_plus NUMERIC,
                pct_masculina NUMERIC,
                pct_feminina NUMERIC,
                pct_0_14 NUMERIC,
                pct_15_29 NUMERIC,
                pct_30_44 NUMERIC,
                pct_45_59 NUMERIC,
                pct_60_plus NUMERIC,
                renda_media NUMERIC,
                renda_classe_a NUMERIC,
                renda_classe_b NUMERIC,
                renda_classe_c NUMERIC,
                renda_classe_de NUMERIC,
                fonte_demografia TEXT,
                fonte_renda TEXT,
                metodo TEXT,
                nivel_confianca INTEGER,
                data_atualizacao TIMESTAMP DEFAULT NOW()
            );

            ALTER TABLE app.fato_expansao_municipio
                ADD COLUMN IF NOT EXISTS pop_masculina NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_feminina NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_0_14 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_15_29 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_30_44 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_45_59 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_60_plus NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_masculina NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_feminina NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_0_14 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_15_29 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_30_44 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_45_59 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_60_plus NUMERIC,
                ADD COLUMN IF NOT EXISTS fonte_demografia TEXT;
        """))

    df_final.to_sql(
        "tmp_censo_2022_demografia",
        engine,
        schema="app",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
    )

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.fato_demografia_renda_municipio (
                codigo_ibge,
                uf,
                municipio,
                ano,
                populacao,
                pop_masculina,
                pop_feminina,
                pop_0_14,
                pop_15_29,
                pop_30_44,
                pop_45_59,
                pop_60_plus,
                pct_masculina,
                pct_feminina,
                pct_0_14,
                pct_15_29,
                pct_30_44,
                pct_45_59,
                pct_60_plus,
                fonte_demografia,
                metodo,
                nivel_confianca,
                data_atualizacao
            )
            SELECT
                codigo_ibge,
                uf,
                municipio,
                2022,
                populacao,
                pop_masculina,
                pop_feminina,
                pop_0_14,
                pop_15_29,
                pop_30_44,
                pop_45_59,
                pop_60_plus,
                pct_masculina,
                pct_feminina,
                pct_0_14,
                pct_15_29,
                pct_30_44,
                pct_45_59,
                pct_60_plus,
                fonte_demografia,
                metodo,
                nivel_confianca,
                NOW()
            FROM app.tmp_censo_2022_demografia
            ON CONFLICT (codigo_ibge) DO UPDATE SET
                uf = EXCLUDED.uf,
                municipio = EXCLUDED.municipio,
                populacao = EXCLUDED.populacao,
                pop_masculina = EXCLUDED.pop_masculina,
                pop_feminina = EXCLUDED.pop_feminina,
                pop_0_14 = EXCLUDED.pop_0_14,
                pop_15_29 = EXCLUDED.pop_15_29,
                pop_30_44 = EXCLUDED.pop_30_44,
                pop_45_59 = EXCLUDED.pop_45_59,
                pop_60_plus = EXCLUDED.pop_60_plus,
                pct_masculina = EXCLUDED.pct_masculina,
                pct_feminina = EXCLUDED.pct_feminina,
                pct_0_14 = EXCLUDED.pct_0_14,
                pct_15_29 = EXCLUDED.pct_15_29,
                pct_30_44 = EXCLUDED.pct_30_44,
                pct_45_59 = EXCLUDED.pct_45_59,
                pct_60_plus = EXCLUDED.pct_60_plus,
                fonte_demografia = EXCLUDED.fonte_demografia,
                metodo = EXCLUDED.metodo,
                nivel_confianca = EXCLUDED.nivel_confianca,
                data_atualizacao = NOW();

            UPDATE app.fato_expansao_municipio e
            SET
                pct_masculina = d.pct_masculina,
                pct_feminina = d.pct_feminina,
                pct_0_14 = d.pct_0_14,
                pct_15_29 = d.pct_15_29,
                pct_30_44 = d.pct_30_44,
                pct_45_59 = d.pct_45_59,
                pct_60_plus = d.pct_60_plus,
                pop_masculina = d.pop_masculina,
                pop_feminina = d.pop_feminina,
                pop_0_14 = d.pop_0_14,
                pop_15_29 = d.pop_15_29,
                pop_30_44 = d.pop_30_44,
                pop_45_59 = d.pop_45_59,
                pop_60_plus = d.pop_60_plus,
                fonte_demografia = 'IBGE SIDRA Censo 2022 tabela 9514',
                data_atualizacao = NOW()
            FROM app.fato_demografia_renda_municipio d
            WHERE e.codigo_ibge::text = d.codigo_ibge
              AND e.uf IN ('MG','SP','RJ','ES');

            DROP TABLE IF EXISTS app.tmp_censo_2022_demografia;
        """))

    if erros:
        pd.DataFrame(erros).to_sql(
            "etl_censo_2022_demografia_erros",
            engine,
            schema="app",
            if_exists="replace",
            index=False,
        )

    print("✅ Carga oficial IBGE/SIDRA 9514 concluída.")
    print(f"Municípios atualizados: {len(df_final)}")
    print(f"Municípios com erro: {len(erros)}")


if __name__ == "__main__":
    main()

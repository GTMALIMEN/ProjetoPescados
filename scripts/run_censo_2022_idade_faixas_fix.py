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

    # Evita falso positivo: "Unidade de Medida" contém "idade"
    ignorar = {
        "nivel territorial",
        "unidade de medida",
        "variavel",
        "ano",
        "valor",
    }

    candidatos = []

    for k, v in header.items():
        nome = normalizar_texto(v)

        if any(x in nome for x in ignorar):
            continue

        if termo_norm == "idade":
            if nome.startswith("idade"):
                candidatos.append((k, nome))
        elif termo_norm == "sexo":
            if nome.startswith("sexo"):
                candidatos.append((k, nome))
        elif termo_norm == "municipio":
            if "municipio" in nome:
                candidatos.append((k, nome))
        else:
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
    header = data[0]
    rows = data[1:]

    col_mun_cod = achar_coluna(header, "município", preferir_codigo=True)
    col_mun_nome = achar_coluna(header, "município", preferir_codigo=False)
    col_sexo = achar_coluna(header, "sexo", preferir_codigo=False)
    col_idade = achar_coluna(header, "idade", preferir_codigo=False)
    col_valor = achar_coluna(header, "valor", preferir_codigo=False)

    if col_valor is None and "V" in header:
        col_valor = "V"

    if None in [col_mun_cod, col_mun_nome, col_sexo, col_idade, col_valor]:
        raise RuntimeError(f"Colunas não encontradas no SIDRA. Header={header}")

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



def calcular_faixas(df):
    df = df.copy()
    df["sexo_norm"] = df["sexo"].map(normalizar_texto)
    df["idade_norm"] = df["idade"].map(normalizar_texto)

    resultados = []

    for codigo, g in df.groupby("codigo_ibge"):
        municipio = g["municipio"].dropna().astype(str).iloc[0]

        idade_total = g["idade_norm"].eq("total")
        sexo_total = g["sexo_norm"].eq("total")
        sexo_masc = g["sexo_norm"].isin(["homens", "homem", "masculino"])
        sexo_fem = g["sexo_norm"].isin(["mulheres", "mulher", "feminino"])

        # 1) Preferência: usar idade detalhada com sexo Total.
        base_idade = g[sexo_total & ~idade_total].copy()

        # 2) Se não vier sexo Total, soma Homens + Mulheres por idade.
        if base_idade.empty or base_idade["valor"].sum() <= 0:
            base_idade = g[(sexo_masc | sexo_fem) & ~idade_total].copy()

            if not base_idade.empty:
                base_idade = (
                    base_idade
                    .groupby(["idade", "idade_norm"], as_index=False)["valor"]
                    .sum()
                )

        # 3) Último fallback: usa qualquer idade detalhada, mas evita linha Total.
        if base_idade.empty or base_idade["valor"].sum() <= 0:
            base_idade = g[~idade_total].copy()

            if not base_idade.empty:
                base_idade = (
                    base_idade
                    .groupby(["idade", "idade_norm"], as_index=False)["valor"]
                    .max()
                )

        total = g[sexo_total & idade_total]["valor"].sum()

        if total <= 0:
            total = base_idade["valor"].sum()

        if total <= 0 or base_idade.empty:
            continue

        faixas = {
            "pop_0_14": 0.0,
            "pop_15_29": 0.0,
            "pop_30_44": 0.0,
            "pop_45_59": 0.0,
            "pop_60_plus": 0.0,
        }

        for _, row in base_idade.iterrows():
            intervalo = idade_intervalo(row["idade"])

            if intervalo is None:
                continue

            dist = distribuir_faixa(row["valor"], intervalo[0], intervalo[1])

            for k, v in dist.items():
                faixas[k] += v

        soma_faixas = sum(faixas.values())

        if soma_faixas <= 0:
            continue

        resultados.append({
            "codigo_ibge": str(codigo),
            "municipio": municipio,
            "populacao_idade": total,
            "pop_0_14": faixas["pop_0_14"],
            "pop_15_29": faixas["pop_15_29"],
            "pop_30_44": faixas["pop_30_44"],
            "pop_45_59": faixas["pop_45_59"],
            "pop_60_plus": faixas["pop_60_plus"],
            "pct_0_14": faixas["pop_0_14"] / total * 100,
            "pct_15_29": faixas["pop_15_29"] / total * 100,
            "pct_30_44": faixas["pop_30_44"] / total * 100,
            "pct_45_59": faixas["pop_45_59"] / total * 100,
            "pct_60_plus": faixas["pop_60_plus"] / total * 100,
        })

    return pd.DataFrame(resultados)


def coletar_idade_municipio(codigo):
    codigo = str(codigo).strip()

    urls = [
        f"{BASE_URL}/n6/{codigo}/v/93/p/2022/c2/all/c287/allxt?formato=json",
        f"{BASE_URL}/n6/{codigo}/v/93/p/2022/c2/all/c287/all/c286/allxt?formato=json",
        f"{BASE_URL}/n6/{codigo}/v/93/p/2022/c2/all/c287/allxt/c286/allxt?formato=json",
    ]

    ultimo_erro = None

    for url in urls:
        try:
            resp = requests.get(url, timeout=90)

            if resp.status_code == 200:
                data = resp.json()

                if data and len(data) > 1:
                    df = sidra_para_dataframe(data)
                    calc = calcular_faixas(df)

                    if not calc.empty:
                        return calc

            ultimo_erro = f"HTTP {resp.status_code} | {resp.text[:250]}"

        except Exception as e:
            ultimo_erro = str(e)

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

    print(f"Municípios para corrigir idade: {len(municipios)}")

    dfs = []
    erros = []

    for i, row in municipios.iterrows():
        codigo = row["codigo_ibge"]

        print(f"Coletando idade SIDRA 9514: {i + 1}/{len(municipios)} | {codigo}")

        try:
            df_calc = coletar_idade_municipio(codigo)
            df_calc["uf"] = row["uf"]
            dfs.append(df_calc)
            print("   ✅ idade OK")
        except Exception as e:
            erros.append({"codigo_ibge": codigo, "uf": row["uf"], "erro": str(e)})
            print(f"   ⚠️ idade falhou: {e}")

        time.sleep(0.15)

    if not dfs:
        print("Nenhuma faixa etária foi coletada.")
        if erros:
            print(pd.DataFrame(erros).head(20).to_string(index=False))
        return

    df_final = pd.concat(dfs, ignore_index=True)

    print(f"Municípios com faixa etária calculada: {len(df_final)}")

    df_final.to_sql(
        "tmp_censo_2022_idade_faixas",
        engine,
        schema="app",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
    )

    with engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE app.fato_demografia_renda_municipio
                ADD COLUMN IF NOT EXISTS pop_0_14 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_15_29 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_30_44 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_45_59 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_60_plus NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_0_14 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_15_29 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_30_44 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_45_59 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_60_plus NUMERIC,
                ADD COLUMN IF NOT EXISTS fonte_demografia TEXT,
                ADD COLUMN IF NOT EXISTS data_atualizacao TIMESTAMP DEFAULT NOW();

            ALTER TABLE app.fato_expansao_municipio
                ADD COLUMN IF NOT EXISTS pop_0_14 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_15_29 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_30_44 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_45_59 NUMERIC,
                ADD COLUMN IF NOT EXISTS pop_60_plus NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_0_14 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_15_29 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_30_44 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_45_59 NUMERIC,
                ADD COLUMN IF NOT EXISTS pct_60_plus NUMERIC;

            UPDATE app.fato_demografia_renda_municipio d
            SET
                pop_0_14 = t.pop_0_14,
                pop_15_29 = t.pop_15_29,
                pop_30_44 = t.pop_30_44,
                pop_45_59 = t.pop_45_59,
                pop_60_plus = t.pop_60_plus,
                pct_0_14 = t.pct_0_14,
                pct_15_29 = t.pct_15_29,
                pct_30_44 = t.pct_30_44,
                pct_45_59 = t.pct_45_59,
                pct_60_plus = t.pct_60_plus,
                fonte_demografia = 'IBGE SIDRA Censo 2022 tabela 9514',
                data_atualizacao = NOW()
            FROM app.tmp_censo_2022_idade_faixas t
            WHERE d.codigo_ibge = t.codigo_ibge::text;

            UPDATE app.fato_expansao_municipio e
            SET
                pop_0_14 = d.pop_0_14,
                pop_15_29 = d.pop_15_29,
                pop_30_44 = d.pop_30_44,
                pop_45_59 = d.pop_45_59,
                pop_60_plus = d.pop_60_plus,
                pct_0_14 = d.pct_0_14,
                pct_15_29 = d.pct_15_29,
                pct_30_44 = d.pct_30_44,
                pct_45_59 = d.pct_45_59,
                pct_60_plus = d.pct_60_plus,
                fonte_demografia = 'IBGE SIDRA Censo 2022 tabela 9514',
                data_atualizacao = NOW()
            FROM app.fato_demografia_renda_municipio d
            WHERE e.codigo_ibge::text = d.codigo_ibge
              AND e.uf IN ('MG','SP','RJ','ES');

            DROP TABLE IF EXISTS app.tmp_censo_2022_idade_faixas;
        """))

    if erros:
        pd.DataFrame(erros).to_sql(
            "etl_censo_2022_idade_faixas_erros",
            engine,
            schema="app",
            if_exists="replace",
            index=False,
        )

    print("✅ Faixas etárias oficiais atualizadas.")
    print(f"Erros: {len(erros)}")


if __name__ == "__main__":
    main()

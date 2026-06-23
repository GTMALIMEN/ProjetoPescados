from pathlib import Path
import sys
import re
import unicodedata
import requests
import pandas as pd
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database.connection import get_engine

AGREGADO = "6977"
FONTE = "IBGE SIDRA POF 2017-2018 tabela 6977"
NIVEL_FONTE = "N2 - Grande Região"
REGIAO_SUDESTE = "3"
SALARIO_MINIMO_REF = 1621.0


def norm(s):
    s = str(s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s


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


def extrair_faixa_reais(nome):
    t = norm(nome)
    t_sem_ponto = t.replace(".", "")
    nums = [float(x) for x in re.findall(r"\d+", t_sem_ponto)]

    if "total" == t.strip():
        return None, None

    if "ate" in t and nums:
        return 0.0, nums[0]

    if "mais de" in t and " a " in t and len(nums) >= 2:
        return nums[0], nums[1]

    if "mais de" in t and nums:
        return nums[0], None

    return None, None


def distribuir_em_classes_ae(pct, faixa_nome):
    low, high = extrair_faixa_reais(faixa_nome)

    out = {
        "Classe A": 0.0,
        "Classe B": 0.0,
        "Classe C": 0.0,
        "Classe D": 0.0,
        "Classe E": 0.0,
    }

    if pct is None or low is None:
        return out

    # Classes da imagem, usando salário mínimo de referência 1.621
    limites = {
        "Classe E": (0.0, 1 * SALARIO_MINIMO_REF),
        "Classe D": (1 * SALARIO_MINIMO_REF, 1 * SALARIO_MINIMO_REF),
        "Classe D": (1 * SALARIO_MINIMO_REF, 3 * SALARIO_MINIMO_REF),
        "Classe C": (3 * SALARIO_MINIMO_REF, 5 * SALARIO_MINIMO_REF),
        "Classe B": (5 * SALARIO_MINIMO_REF, 15 * SALARIO_MINIMO_REF),
        "Classe A": (15 * SALARIO_MINIMO_REF, None),
    }

    # Faixa aberta superior: a POF usa "Mais de 23.850".
    # Como o corte A é 24.315, classificamos como Classe A e registramos como mapeamento aproximado.
    if high is None:
        if low >= 15 * SALARIO_MINIMO_REF * 0.95:
            out["Classe A"] = pct
        else:
            out["Classe B"] = pct
        return out

    largura = high - low
    if largura <= 0:
        return out

    for classe, (c_low, c_high) in limites.items():
        if c_high is None:
            c_high = high

        ini = max(low, c_low)
        fim = min(high, c_high)

        overlap = max(0.0, fim - ini)

        if overlap > 0:
            out[classe] += pct * (overlap / largura)

    return out


def buscar_metadados():
    url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{AGREGADO}/metadados"
    resp = requests.get(url, timeout=60)

    if resp.status_code != 200:
        raise RuntimeError(f"Metadados {AGREGADO} falharam | HTTP {resp.status_code} | {resp.text[:500]}")

    meta = resp.json()
    if isinstance(meta, list):
        meta = meta[0]

    print("Agregado:", AGREGADO)
    print("Nome:", meta.get("nome", ""))

    class_renda = None
    for c in meta.get("classificacoes", []):
        nome_c = norm(c.get("nome"))
        if "classe" in nome_c and "rendimento" in nome_c:
            class_renda = c
            break

    if not class_renda:
        raise RuntimeError("Não encontrei classificação de classe de rendimento na tabela 6977.")

    print("Classificação renda:", class_renda.get("id"), "|", class_renda.get("nome"))
    return str(class_renda.get("id"))


def buscar_dados(class_id):
    urls = [
        f"https://apisidra.ibge.gov.br/values/t/{AGREGADO}/n2/{REGIAO_SUDESTE}/v/1001211/p/all/c{class_id}/all?formato=json",
        f"https://apisidra.ibge.gov.br/values/t/{AGREGADO}/n2/{REGIAO_SUDESTE}/v/1211/p/all/c{class_id}/all?formato=json",
        f"https://apisidra.ibge.gov.br/values/t/{AGREGADO}/n2/{REGIAO_SUDESTE}/v/all/p/all/c{class_id}/all?formato=json",
    ]

    ultimo_erro = None

    for url in urls:
        print("Buscando:", url)
        resp = requests.get(url, timeout=120)

        if resp.status_code != 200:
            ultimo_erro = f"HTTP {resp.status_code} | {resp.text[:500]}"
            print("Falhou:", ultimo_erro)
            continue

        data = resp.json()

        if not data or len(data) < 2:
            ultimo_erro = "Retorno vazio"
            print("Falhou:", ultimo_erro)
            continue

        header = data[0]
        df = pd.DataFrame(data[1:])
        df = df.rename(columns={k: v for k, v in header.items() if k in df.columns})
        return df

    raise RuntimeError(f"Nenhuma URL SIDRA 6977 retornou dados. Último erro: {ultimo_erro}")


def parse_dados(df):
    col_valor = "Valor" if "Valor" in df.columns else "V"
    col_variavel = next((c for c in df.columns if "Variável" in c and "Código" not in c), None)
    col_regiao = next((c for c in df.columns if "Grande Região" in c and "Código" not in c), None)
    col_regiao_cod = next((c for c in df.columns if "Grande Região (Código)" in c), None)
    col_ano = next((c for c in df.columns if c == "Ano" or c.endswith("Ano")), None)
    col_classe = next((c for c in df.columns if "Classes" in c and "rendimento" in c.lower() and "Código" not in c), None)

    if any(c is None for c in [col_valor, col_variavel, col_regiao, col_classe]):
        raise RuntimeError(f"Colunas inesperadas no retorno: {list(df.columns)}")

    df["valor_num"] = df[col_valor].apply(to_num)

    mask_pct = df[col_variavel].astype(str).str.contains("percentual", case=False, na=False)
    df_pct = df[mask_pct].copy()

    if df_pct.empty:
        print("Percentual não encontrado. Calculando a partir de Número de famílias.")
        mask_num = df[col_variavel].astype(str).str.contains("Número de famílias", case=False, na=False)
        df_num = df[mask_num].copy()

        if df_num.empty:
            raise RuntimeError("Não encontrei percentual nem número de famílias.")

        total = df_num[df_num[col_classe].astype(str).str.lower().str.strip() == "total"]["valor_num"].sum()

        if not total:
            raise RuntimeError("Não encontrei total de famílias.")

        df_num["pct"] = df_num["valor_num"] / total * 100
        base = df_num
    else:
        df_pct["pct"] = df_pct["valor_num"]
        base = df_pct

    linhas = []

    for _, row in base.iterrows():
        faixa = row[col_classe]
        pct = row["pct"]

        if str(faixa).strip().lower() == "total":
            continue

        dist = distribuir_em_classes_ae(pct, faixa)

        linha = {
            "codigo_regiao": str(row[col_regiao_cod]) if col_regiao_cod else REGIAO_SUDESTE,
            "regiao_ibge": str(row[col_regiao]),
            "ano": str(row[col_ano]) if col_ano else "2017-2018",
            "faixa_original": str(faixa),
            **dist,
        }

        linhas.append(linha)

    detalhado = pd.DataFrame(linhas)

    if detalhado.empty:
        raise RuntimeError("Nenhuma faixa foi mapeada para Classe A-E.")

    pivot = (
        detalhado
        .groupby(["codigo_regiao", "regiao_ibge", "ano"], dropna=False)[
            ["Classe A", "Classe B", "Classe C", "Classe D", "Classe E"]
        ]
        .sum()
        .reset_index()
    )

    pivot = pivot.rename(columns={
        "Classe A": "classe_a_pct",
        "Classe B": "classe_b_pct",
        "Classe C": "classe_c_pct",
        "Classe D": "classe_d_pct",
        "Classe E": "classe_e_pct",
    })

    pivot["salario_minimo_ref"] = SALARIO_MINIMO_REF
    pivot["fonte_classe_renda"] = FONTE
    pivot["nivel_fonte_classe_renda"] = NIVEL_FONTE
    pivot["metodo_classe_renda"] = (
        "Distribuição oficial POF 2017-2018 por faixas de rendimento familiar, "
        "mapeada para Classe A-E usando salário mínimo de referência 1621. "
        "Como as faixas POF são em reais e não batem exatamente com múltiplos de salário mínimo, "
        "foi aplicado rateio proporcional por sobreposição de faixas. Fonte regional N2 replicada para microrregiões do Sudeste."
    )

    return pivot, detalhado



def salvar(pivot):
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS app"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS app.fato_classe_renda_oficial_regiao (
                id BIGSERIAL PRIMARY KEY,
                codigo_regiao TEXT,
                regiao_ibge TEXT,
                ano TEXT,
                classe_a_pct NUMERIC,
                classe_b_pct NUMERIC,
                classe_c_pct NUMERIC,
                classe_d_pct NUMERIC,
                classe_e_pct NUMERIC,
                salario_minimo_ref NUMERIC,
                fonte_classe_renda TEXT,
                nivel_fonte_classe_renda TEXT,
                metodo_classe_renda TEXT,
                data_carga TIMESTAMP DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            ALTER TABLE app.fato_classe_renda_oficial_regiao
                ADD COLUMN IF NOT EXISTS codigo_regiao TEXT,
                ADD COLUMN IF NOT EXISTS regiao_ibge TEXT,
                ADD COLUMN IF NOT EXISTS ano TEXT,
                ADD COLUMN IF NOT EXISTS classe_a_pct NUMERIC,
                ADD COLUMN IF NOT EXISTS classe_b_pct NUMERIC,
                ADD COLUMN IF NOT EXISTS classe_c_pct NUMERIC,
                ADD COLUMN IF NOT EXISTS classe_d_pct NUMERIC,
                ADD COLUMN IF NOT EXISTS classe_e_pct NUMERIC,
                ADD COLUMN IF NOT EXISTS salario_minimo_ref NUMERIC,
                ADD COLUMN IF NOT EXISTS fonte_classe_renda TEXT,
                ADD COLUMN IF NOT EXISTS nivel_fonte_classe_renda TEXT,
                ADD COLUMN IF NOT EXISTS metodo_classe_renda TEXT,
                ADD COLUMN IF NOT EXISTS data_carga TIMESTAMP DEFAULT NOW()
        """))

        conn.execute(
            text("""
                DELETE FROM app.fato_classe_renda_oficial_regiao
                WHERE fonte_classe_renda = :fonte
            """),
            {"fonte": FONTE}
        )

        for _, row in pivot.iterrows():
            conn.execute(text("""
                INSERT INTO app.fato_classe_renda_oficial_regiao (
                    codigo_regiao,
                    regiao_ibge,
                    ano,
                    classe_a_pct,
                    classe_b_pct,
                    classe_c_pct,
                    classe_d_pct,
                    classe_e_pct,
                    salario_minimo_ref,
                    fonte_classe_renda,
                    nivel_fonte_classe_renda,
                    metodo_classe_renda
                )
                VALUES (
                    :codigo_regiao,
                    :regiao_ibge,
                    :ano,
                    :classe_a_pct,
                    :classe_b_pct,
                    :classe_c_pct,
                    :classe_d_pct,
                    :classe_e_pct,
                    :salario_minimo_ref,
                    :fonte,
                    :nivel,
                    :metodo
                )
            """), {
                "codigo_regiao": str(row["codigo_regiao"]),
                "regiao_ibge": str(row["regiao_ibge"]),
                "ano": str(row["ano"]),
                "classe_a_pct": float(row["classe_a_pct"]),
                "classe_b_pct": float(row["classe_b_pct"]),
                "classe_c_pct": float(row["classe_c_pct"]),
                "classe_d_pct": float(row["classe_d_pct"]),
                "classe_e_pct": float(row["classe_e_pct"]),
                "salario_minimo_ref": float(row["salario_minimo_ref"]),
                "fonte": row["fonte_classe_renda"],
                "nivel": row["nivel_fonte_classe_renda"],
                "metodo": row["metodo_classe_renda"],
            })

        conn.execute(text("""
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
            )
        """))

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
                'app.fato_classe_renda_oficial_regiao',
                'OK',
                :registros,
                :distintos,
                0,
                0,
                :detalhe
            )
        """), {
            "fonte": FONTE,
            "registros": int(len(pivot)),
            "distintos": int(pivot["codigo_regiao"].nunique()),
            "detalhe": "Carga POF 2017-2018 N2 Sudeste com distribuição Classe A-E por rateio de faixas."
        })

def main():
    class_id = buscar_metadados()
    df = buscar_dados(class_id)
    pivot, detalhado = parse_dados(df)

    print("\nFaixas tratadas:")
    print(detalhado.to_string(index=False))

    print("\nResultado consolidado:")
    print(pivot.to_string(index=False))

    total = pivot[["classe_a_pct", "classe_b_pct", "classe_c_pct", "classe_d_pct", "classe_e_pct"]].sum(axis=1).iloc[0]
    print("\nSoma das classes:", total)

    if not (95 <= total <= 105):
        raise RuntimeError(f"Soma das classes fora do esperado: {total}")

    salvar(pivot)

    print("\n✅ Carga oficial de classes A-E finalizada.")
    print("✅ Dados salvos em app.fato_classe_renda_oficial_regiao")


if __name__ == "__main__":
    main()

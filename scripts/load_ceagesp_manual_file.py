
from __future__ import annotations

from pathlib import Path
import hashlib
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


COLS_OBRIGATORIAS = [
    "data_referencia",
    "produto",
    "preco_comum",
]


def _norm_col(col: str) -> str:
    col = str(col).strip().lower()
    repl = {
        "data": "data_referencia",
        "data cotacao": "data_referencia",
        "data_cotacao": "data_referencia",
        "mercadoria": "produto",
        "nome": "produto",
        "menor": "preco_minimo",
        "mínimo": "preco_minimo",
        "minimo": "preco_minimo",
        "preço mínimo": "preco_minimo",
        "preco mínimo": "preco_minimo",
        "comum": "preco_comum",
        "preço comum": "preco_comum",
        "preco comum": "preco_comum",
        "maior": "preco_maximo",
        "máximo": "preco_maximo",
        "maximo": "preco_maximo",
        "preço máximo": "preco_maximo",
        "preco máximo": "preco_maximo",
        "unid": "unidade",
        "unidade": "unidade",
        "class": "classificacao",
        "classificação": "classificacao",
        "classificacao": "classificacao",
        "obs": "observacao",
    }
    col = col.replace(".", "").replace("-", " ").replace("_", " ")
    col = " ".join(col.split())
    return repl.get(col, col.replace(" ", "_"))


def _to_number(value):
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().replace("R$", "").replace("\xa0", " ")
    if text in ("", "-", "...", "nan", "None"):
        return None
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def _read_file(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    if path.suffix.lower() in [".xlsx", ".xls"]:
        return pd.read_excel(path, dtype=str)

    # CSV com autodetecção básica. O template usa ;.
    for sep in [";", ",", "\t", "|"]:
        try:
            df = pd.read_csv(path, sep=sep, dtype=str, encoding="utf-8-sig")
            if len(df.columns) >= 3:
                return df
        except Exception:
            pass

    return pd.read_csv(path, sep=None, engine="python", dtype=str)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Carregar CEAGESP manual CSV/XLSX")
    parser.add_argument("--arquivo", required=True, help="Caminho do arquivo CSV/XLSX")
    args = parser.parse_args()

    path = Path(args.arquivo)
    if not path.is_absolute():
        path = ROOT_DIR / path

    df = _read_file(path)
    df = df.rename(columns={c: _norm_col(c) for c in df.columns})
    df = df.dropna(how="all")

    missing = [c for c in COLS_OBRIGATORIAS if c not in df.columns]
    if missing:
        raise ValueError(
            "Colunas obrigatórias ausentes: "
            + ", ".join(missing)
            + "\nColunas esperadas mínimas: data_referencia, produto, preco_comum"
        )

    for col in ["classificacao", "unidade", "preco_minimo", "preco_maximo", "fonte", "url_fonte", "observacao"]:
        if col not in df.columns:
            df[col] = None

    df["data_referencia"] = pd.to_datetime(df["data_referencia"], dayfirst=True, errors="coerce").dt.date
    df = df.dropna(subset=["data_referencia", "produto"])

    for col in ["preco_minimo", "preco_comum", "preco_maximo"]:
        df[col] = df[col].map(_to_number)

    df = df.dropna(subset=["preco_comum"])

    if df.empty:
        raise ValueError("Nenhuma linha válida encontrada. Verifique data_referencia, produto e preco_comum.")

    records = []
    for row in df.to_dict(orient="records"):
        produto = str(row.get("produto") or "").strip()
        classificacao = str(row.get("classificacao") or "").strip()
        unidade = str(row.get("unidade") or "").strip()
        data_ref = row.get("data_referencia")
        chave_base = "|".join([str(data_ref), produto.upper(), classificacao.upper(), unidade.upper()])
        chave = hashlib.sha256(chave_base.encode("utf-8")).hexdigest()

        records.append({
            "chave_registro": chave,
            "data_referencia": data_ref,
            "categoria": "Pescados",
            "produto": produto,
            "classificacao": classificacao or None,
            "unidade": unidade or None,
            "preco_minimo": row.get("preco_minimo"),
            "preco_comum": row.get("preco_comum"),
            "preco_maximo": row.get("preco_maximo"),
            "fonte": row.get("fonte") or "CEAGESP Manual",
            "url_fonte": row.get("url_fonte") or "https://ceagesp.gov.br/cotacoes/",
            "hash_carga": chave,
            "observacao": row.get("observacao"),
        })

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.fato_ceagesp_pescados (
                chave_registro, data_referencia, categoria, produto, classificacao, unidade,
                preco_minimo, preco_comum, preco_maximo, fonte, url_fonte, hash_carga, observacao
            )
            VALUES (
                :chave_registro, :data_referencia, :categoria, :produto, :classificacao, :unidade,
                :preco_minimo, :preco_comum, :preco_maximo, :fonte, :url_fonte, :hash_carga, :observacao
            )
            ON CONFLICT (chave_registro)
            DO UPDATE SET
                preco_minimo = EXCLUDED.preco_minimo,
                preco_comum = EXCLUDED.preco_comum,
                preco_maximo = EXCLUDED.preco_maximo,
                fonte = EXCLUDED.fonte,
                url_fonte = EXCLUDED.url_fonte,
                observacao = EXCLUDED.observacao,
                data_coleta = NOW();
        """), records)

    print(f"✅ CEAGESP manual carregado/atualizado: {len(records)} registros")
    print(f"Arquivo: {path}")


if __name__ == "__main__":
    main()

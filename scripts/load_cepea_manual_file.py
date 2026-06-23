from __future__ import annotations

from pathlib import Path
import hashlib
import sys
import time
import uuid

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine
from src.etl.load_fontes_reais import finalizar_run, registrar_controle, registrar_run, upsert_setorial


COLS_OBRIGATORIAS = [
    "data_fim_periodo",
    "preco_ajustado",
]

INDICADOR_CEPEA_TILAPIA = "preco_tilapia_cepea_produtor_independente"
URL_CEPEA_TILAPIA = "https://www.cepea.org.br/br/indicador/tilapia.aspx"


def _norm_col(col: str) -> str:
    import unicodedata

    original = str(col or "").strip()
    text = unicodedata.normalize("NFKD", original).encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace(".", " ").replace("-", " ").replace("_", " ")
    text = " ".join(text.split())

    repl = {
        "data": "data_fim_periodo",
        "data referencia": "data_fim_periodo",
        "data_referencia": "data_fim_periodo",
        "categoria": "produto",
        "a vista r": "preco_rs_kg",
        "a vista r$": "preco_rs_kg",
        "a_vista_r": "preco_rs_kg",
        "a_vista_r$": "preco_rs_kg",
        "a vista rs": "preco_rs_kg",
        "a_vista_rs": "preco_rs_kg",
        "avista r": "preco_rs_kg",
        "avista_r": "preco_rs_kg",
        "a vista us": "preco_usd_aux",
        "a vista us$": "preco_usd_aux",
        "a_vista_us": "preco_usd_aux",
        "a_vista_us$": "preco_usd_aux",
        "a vista uss": "preco_usd_aux",
        "a_vista_uss": "preco_usd_aux",
        "ano": "ano_aux",
        "mes": "mes_aux",
        "mes ano": "data_fim_periodo",
        "mes_ano": "data_fim_periodo",
        "mes/ano": "data_fim_periodo",
        "data final": "data_fim_periodo",
        "data fim": "data_fim_periodo",
        "data fim periodo": "data_fim_periodo",
        "data_fim_periodo": "data_fim_periodo",
        "data inicio": "data_inicio_periodo",
        "data inicial": "data_inicio_periodo",
        "data inicio periodo": "data_inicio_periodo",
        "data_inicio_periodo": "data_inicio_periodo",
        "periodo": "periodo_original",
        "periodo original": "periodo_original",
        "periodo_original": "periodo_original",
        "produto": "produto",
        "regiao": "regiao_cepea",
        "regiao cepea": "regiao_cepea",
        "regiao_cepea": "regiao_cepea",
        "praca": "regiao_cepea",
        "praça": "regiao_cepea",
        "uf": "uf",
        "estado": "uf",
        "valor": "preco_ajustado",
        "preco": "preco_ajustado",
        "preco ajustado": "preco_ajustado",
        "preco_ajustado": "preco_ajustado",
        "preco rs kg": "preco_rs_kg",
        "preco r kg": "preco_rs_kg",
        "preco r$/kg": "preco_rs_kg",
        "preco_rs_kg": "preco_rs_kg",
        "r kg": "preco_rs_kg",
        "r$/kg": "preco_rs_kg",
        "variacao": "variacao_semana_pct",
        "variacao semana": "variacao_semana_pct",
        "variacao semana pct": "variacao_semana_pct",
        "variacao_semana_pct": "variacao_semana_pct",
        "var": "variacao_semana_pct",
        "var pct": "variacao_semana_pct",
        "unidade": "unidade",
        "url": "url_fonte",
        "url fonte": "url_fonte",
        "url_fonte": "url_fonte",
        "fonte": "fonte",
        "obs": "observacao",
        "observacao": "observacao",
        "observação": "observacao",
    }
    return repl.get(text, text.replace(" ", "_"))


def _to_number(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text_value = str(value).strip().replace("R$", "").replace("%", "").replace("\xa0", " ")
    text_value = text_value.strip()
    if text_value in ("", "-", "...", "nan", "None"):
        return None
    if "," in text_value and "." in text_value:
        text_value = text_value.replace(".", "").replace(",", ".")
    elif "," in text_value:
        text_value = text_value.replace(",", ".")
    try:
        return float(text_value)
    except ValueError:
        return None

def _to_date_safe(value):
    if value is None or pd.isna(value):
        return None
    if hasattr(value, "date") and not isinstance(value, (int, float, str)):
        try:
            d = value.date()
            return d if 1900 <= d.year <= 9999 else None
        except Exception:
            return None
    if isinstance(value, (int, float)):
        if 20000 <= float(value) <= 60000:
            d = (pd.Timestamp("1899-12-30") + pd.to_timedelta(float(value), unit="D")).date()
            return d if 1900 <= d.year <= 9999 else None
        return None
    txt = str(value).strip()
    if not txt or txt.lower() in {"nan", "none", "nat"}:
        return None
    try:
        num = float(txt.replace(",", "."))
        if 20000 <= num <= 60000:
            d = (pd.Timestamp("1899-12-30") + pd.to_timedelta(num, unit="D")).date()
            return d if 1900 <= d.year <= 9999 else None
    except Exception:
        pass
    if __import__("re").match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:\s.*)?$", txt):
        d = pd.to_datetime(txt, errors="coerce", yearfirst=True)
    else:
        d = pd.to_datetime(txt, errors="coerce", dayfirst=True)
        if pd.isna(d):
            d = pd.to_datetime(txt, errors="coerce")
    if pd.isna(d):
        return None
    d = d.date()
    return d if 1900 <= d.year <= 9999 else None


def _normalizar_produto(value):
    import unicodedata, re
    txt = str(value or "").strip()
    if not txt or txt.lower() in {"nan", "none", "nat"}:
        return "Tilápia"
    norm = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii").upper().strip()
    norm = re.sub(r"\s+", " ", norm)
    mapa = {"BOI": "Bovino", "BOVINO": "Bovino", "BOI GORDO": "Bovino", "TILAPIA": "Tilápia", "CAMARAO": "Camarão", "SALMAO": "Salmão"}
    return mapa.get(norm, txt)


def _read_file(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    if path.suffix.lower() in [".xlsx", ".xls"]:
        return pd.read_excel(path, dtype=str)

    for sep in [";", ",", "\t", "|"]:
        try:
            df = pd.read_csv(path, sep=sep, dtype=str, encoding="utf-8-sig")
            if len(df.columns) >= 3:
                return df
        except Exception:
            pass

    return pd.read_csv(path, sep=None, engine="python", dtype=str)


def _uf_por_regiao(regiao: str) -> str:
    r = str(regiao or "").strip().lower()
    if "morada nova" in r or "triâng" in r or "triang" in r or "alto parana" in r:
        return "MG"
    if "paraná" in r or "parana" in r:
        return "PR"
    if "grandes lagos" in r:
        return "SP/MS"
    return "BR"


def _ensure_structure(engine) -> None:
    sql_path = ROOT_DIR / "src" / "database" / "cepea_manual.sql"
    sql = sql_path.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.execute(text(sql))


def _clean_records(df: pd.DataFrame) -> list[dict]:
    out = []
    for row in df.astype(object).to_dict(orient="records"):
        out.append({k: (None if pd.isna(v) else v) for k, v in row.items()})
    return out


def _chave_registro(row: dict) -> str:
    parts = [
        "CEPEA",
        str(row.get("data_fim_periodo") or ""),
        str(row.get("produto") or "Tilápia").strip().upper(),
        str(row.get("regiao_cepea") or "").strip().upper(),
        str(row.get("unidade") or "R$/kg").strip().upper(),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _hash_linha(row: dict, arquivo: str) -> str:
    base = {k: row.get(k) for k in sorted(row.keys())}
    parts = ["cepea_manual", arquivo] + [f"{k}={v}" for k, v in base.items()]
    return hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).hexdigest()


def _upsert_manual_table(engine, df: pd.DataFrame) -> int:
    records = _clean_records(df)
    if not records:
        return 0

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.fato_cepea_tilapia_manual (
                chave_registro, hash_linha, data_inicio_periodo, data_fim_periodo,
                periodo_original, produto, regiao_cepea, uf, preco_ajustado, preco_rs_kg,
                variacao_semana_pct, unidade, fonte, tipo_fonte, url_fonte,
                arquivo_origem, usuario_carga, observacao
            )
            VALUES (
                :chave_registro, :hash_linha, :data_inicio_periodo, :data_fim_periodo,
                :periodo_original, :produto, :regiao_cepea, :uf, :preco_ajustado, :preco_rs_kg,
                :variacao_semana_pct, :unidade, :fonte, :tipo_fonte, :url_fonte,
                :arquivo_origem, :usuario_carga, :observacao
            )
            ON CONFLICT (chave_registro)
            DO UPDATE SET
                hash_linha = EXCLUDED.hash_linha,
                data_inicio_periodo = EXCLUDED.data_inicio_periodo,
                periodo_original = EXCLUDED.periodo_original,
                uf = EXCLUDED.uf,
                preco_ajustado = EXCLUDED.preco_ajustado,
                preco_rs_kg = EXCLUDED.preco_rs_kg,
                variacao_semana_pct = EXCLUDED.variacao_semana_pct,
                unidade = EXCLUDED.unidade,
                tipo_fonte = EXCLUDED.tipo_fonte,
                url_fonte = EXCLUDED.url_fonte,
                arquivo_origem = EXCLUDED.arquivo_origem,
                usuario_carga = EXCLUDED.usuario_carga,
                observacao = EXCLUDED.observacao,
                data_coleta = NOW();
        """), records)

    return len(records)


def _prepare_records(path: Path, usuario: str) -> tuple[pd.DataFrame, int]:
    df_raw = _read_file(path)
    df = df_raw.rename(columns={c: _norm_col(c) for c in df_raw.columns})
    df = df.dropna(how="all")

    missing = [c for c in COLS_OBRIGATORIAS if c not in df.columns]
    if missing:
        raise ValueError(
            "Colunas obrigatórias ausentes: "
            + ", ".join(missing)
            + "\nColunas esperadas mínimas: data_fim_periodo, regiao_cepea, PREÇO AJUSTADO"
        )

    for col in [
        "data_inicio_periodo", "periodo_original", "produto", "regiao_cepea", "uf", "preco_rs_kg", "variacao_semana_pct",
        "unidade", "url_fonte", "fonte", "observacao"
    ]:
        if col not in df.columns:
            df[col] = None

    df["data_inicio_periodo"] = df["data_inicio_periodo"].map(_to_date_safe)
    df["data_fim_periodo"] = df["data_fim_periodo"].map(_to_date_safe)
    df["regiao_cepea"] = df["regiao_cepea"].fillna("CEPEA - série manual")
    df = df.dropna(subset=["data_fim_periodo"])

    df["preco_ajustado"] = df["preco_ajustado"].map(_to_number)
    df["preco_rs_kg"] = df["preco_rs_kg"].map(_to_number)
    df["preco_rs_kg"] = df["preco_rs_kg"].fillna(df["preco_ajustado"])
    df["variacao_semana_pct"] = df["variacao_semana_pct"].map(_to_number)
    df = df.dropna(subset=["preco_ajustado"])

    if df.empty:
        raise ValueError("Nenhuma linha válida encontrada. Verifique data_fim_periodo, regiao_cepea e PREÇO AJUSTADO.")

    df["produto"] = df["produto"].map(_normalizar_produto)
    df["regiao_cepea"] = df["regiao_cepea"].astype(str).str.strip()
    df["uf"] = df.apply(lambda r: str(r.get("uf") or "").strip().upper() or _uf_por_regiao(r.get("regiao_cepea")), axis=1)
    df["unidade"] = df["unidade"].fillna("R$/kg").astype(str).str.strip().replace({"": "R$/kg"})
    df["fonte"] = "CEPEA"
    df["tipo_fonte"] = "oficial_arquivo_manual"
    df["url_fonte"] = df["url_fonte"].fillna(URL_CEPEA_TILAPIA).astype(str).str.strip().replace({"": URL_CEPEA_TILAPIA})
    df["arquivo_origem"] = path.name
    df["usuario_carga"] = usuario
    df["chave_registro"] = [_chave_registro(r) for r in _clean_records(df)]
    df["hash_linha"] = [_hash_linha(r, path.name) for r in _clean_records(df)]

    cols = [
        "chave_registro", "hash_linha", "data_inicio_periodo", "data_fim_periodo",
        "periodo_original", "produto", "regiao_cepea", "uf", "preco_ajustado", "preco_rs_kg",
        "variacao_semana_pct", "unidade", "fonte", "tipo_fonte", "url_fonte",
        "arquivo_origem", "usuario_carga", "observacao"
    ]
    return df[cols].copy(), len(df_raw)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Carregar CEPEA manual oficial CSV/XLSX")
    parser.add_argument("--arquivo", required=True, help="Caminho do arquivo CSV/XLSX preenchido")
    parser.add_argument("--usuario", default="manual", help="Usuário/responsável pela carga")
    parser.add_argument("--criar-estrutura", action="store_true", help="Cria/atualiza estrutura app.fato_cepea_tilapia_manual antes da carga")
    parser.add_argument("--substituir-tudo", action="store_true", help="Limpa CEPEA manual antigo antes de carregar este arquivo")
    args = parser.parse_args()

    path = Path(args.arquivo)
    if not path.is_absolute():
        path = ROOT_DIR / path

    engine = get_engine()
    run_id = str(uuid.uuid4())
    inicio = time.perf_counter()
    fonte = "CEPEA"
    registrar_run(engine, run_id, fonte, f"Carga CEPEA manual oficial: {path.name}")

    try:
        if args.criar_estrutura:
            _ensure_structure(engine)

        df_manual, qtd_raw = _prepare_records(path, usuario=args.usuario)
        if args.substituir_tudo:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM app.fato_cepea_tilapia_manual"))
                # Manual-only: remove CEPEA proxy/scraper/automático e republica apenas este arquivo.
                conn.execute(text("""
                    DELETE FROM dw.fato_indicador_setorial
                    WHERE fonte ILIKE '%CEPEA%'
                       OR COALESCE(subcategoria, '') ILIKE '%cepea%'
                       OR COALESCE(indicador, '') ILIKE '%cepea%'
                """))
        qtd_manual = _upsert_manual_table(engine, df_manual)

        df_dw = pd.DataFrame({
            "data": df_manual["data_fim_periodo"],
            "fonte": "CEPEA",
            "indicador": INDICADOR_CEPEA_TILAPIA,
            "categoria": "proteina",
            "subcategoria": "oficial_arquivo_manual",
            "produto": df_manual["produto"],
            "uf": df_manual["uf"],
            "regiao": df_manual["regiao_cepea"],
            "valor": df_manual["preco_ajustado"],
            "unidade": df_manual["unidade"],
            "periodicidade": "semanal",
        })
        qtd_dw = upsert_setorial(engine, df_dw)

        tempo = time.perf_counter() - inicio
        mensagem = f"CEPEA manual oficial concluído | lidos={qtd_raw} | app={qtd_manual} | dw={qtd_dw}"
        registrar_controle(engine, run_id, fonte, "SUCESSO", mensagem, qtd_raw, qtd_dw, tempo)
        finalizar_run(engine, run_id, "SUCESSO", mensagem)

        print(f"✅ {mensagem}")
        print(f"Arquivo: {path}")
        print("Fonte conceitual: CEPEA oficial | Método: arquivo manual controlado")

    except Exception as exc:
        tempo = time.perf_counter() - inicio
        mensagem = str(exc)
        registrar_controle(engine, run_id, fonte, "ERRO_VALIDACAO", mensagem, 0, 0, tempo)
        finalizar_run(engine, run_id, "ERRO_VALIDACAO", mensagem)
        raise


if __name__ == "__main__":
    main()

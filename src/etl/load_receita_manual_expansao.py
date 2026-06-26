
from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd
from src.utils.normalizacao_produtos import normalizar_produto
from sqlalchemy import text

from src.database.connection import get_engine


TOP_RECEITA_EXPANSAO_OBRIGATORIO = "1100 - VENDA DE MERCADORIA"


def _norm_col(col: Any) -> str:
    s = str(col or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    aliases = {
        "cliente": "parceiro",
        "nome_parceiro": "parceiro",
        "parceiro_cliente": "parceiro",
        "municipio": "cidade",
        "uf": "estado",
        "data": "data_competencia",
        "dt_competencia": "data_competencia",
        "data_comp": "data_competencia",
        "competencia": "data_competencia",
        "grupo_de_produto": "grupo_produto",
        "grupo_produtos": "grupo_produto",
        "grupo_produto": "grupo_produto",
        "produto_grupo": "grupo_produto",
        "vlr_total_liquido": "vlr_total_liquido",
        "valor_total_liquido": "vlr_total_liquido",
        "valor_liquido": "vlr_total_liquido",
        "vlr_liquido": "vlr_total_liquido",
        "receita": "vlr_total_liquido",
        "faturamento": "vlr_total_liquido",
        "valor": "vlr_total_liquido",
        "volume": "volume",
        "qtd": "volume",
        "quantidade": "volume",
        "produto": "produto",
        "item": "produto",
        "top": "top",
        "tipo_operacao": "top",
        "tipo_de_operacao": "top",
    }
    return aliases.get(s, s)


def _read_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    if path.suffix.lower() in {".xlsx", ".xlsm", ".xls"}:
        return pd.read_excel(path, dtype=str)

    for sep in [";", ",", "\t", "|"]:
        try:
            df = pd.read_csv(path, sep=sep, dtype=str, encoding="utf-8-sig")
            if len(df.columns) >= 5:
                return df
        except Exception:
            pass

    return pd.read_csv(path, sep=None, engine="python", dtype=str)


def _to_number(value):
    if value is None or pd.isna(value):
        return None
    s = str(value).strip().replace("R$", "").replace("\xa0", " ")
    if s in ("", "-", "...", "nan", "None"):
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _to_date(value):
    if value is None or pd.isna(value):
        return None
    dt = pd.to_datetime(value, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return None
    return dt.date()


def _normalizar_top_receita(valor: Any) -> str | None:
    txt = str(valor or "").strip()
    if not txt or txt.lower() in {"nan", "none"}:
        return None
    txt_norm = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii").upper()
    txt_norm = re.sub(r"\s+", " ", txt_norm).strip()
    if txt_norm == "1100" or txt_norm.startswith("1100") or txt_norm == "VENDA DE MERCADORIA":
        return TOP_RECEITA_EXPANSAO_OBRIGATORIO
    return txt


def _hash(values: list[Any]) -> str:
    parts = []
    for v in values:
        if v is None:
            parts.append("")
        else:
            try:
                parts.append("" if pd.isna(v) else str(v))
            except TypeError:
                parts.append(str(v))
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _categoria_pescado(grupo: str) -> str:
    """
    Classifica o produto usando aliases oficiais.

    Exemplos:
    CAMARAO, CAMAR?O, CAMARAO CATIVEIRO -> Camar?o
    TILAPIA, TIL?PIA, FILE TILAPIA -> Til?pia
    """
    return normalizar_produto(grupo)


def carregar_receita_manual_expansao(arquivo: str | Path) -> dict:
    root_dir = Path(__file__).resolve().parents[2]
    path = Path(arquivo)
    if not path.is_absolute():
        path = root_dir / path

    df = _read_table(path)
    df = df.rename(columns={c: _norm_col(c) for c in df.columns}).dropna(how="all")

    obrigatorias = ["parceiro", "cidade", "estado", "data_competencia", "grupo_produto", "vlr_total_liquido", "top"]
    missing = [c for c in obrigatorias if c not in df.columns]
    if missing:
        raise ValueError(
            "Colunas obrigatórias ausentes: "
            + ", ".join(missing)
            + "\nEsperado: parceiro, cidade, estado, data_competencia, grupo_produto, vlr_total_liquido, TOP"
        )

    records = []
    rejeitados = 0
    rejeitados_top = 0

    for _, row in df.iterrows():
        parceiro = str(row.get("parceiro") or "").strip()
        cidade = str(row.get("cidade") or "").strip()
        estado = str(row.get("estado") or "").strip().upper()
        data_comp = _to_date(row.get("data_competencia"))
        grupo = str(row.get("grupo_produto") or "").strip()
        valor = _to_number(row.get("vlr_total_liquido"))
        volume = _to_number(row.get("volume"))
        produto = str(row.get("produto") or "").strip() or None
        top = _normalizar_top_receita(row.get("top"))

        if top != TOP_RECEITA_EXPANSAO_OBRIGATORIO:
            rejeitados += 1
            rejeitados_top += 1
            continue

        if not cidade or not estado or not data_comp or not grupo or valor is None:
            rejeitados += 1
            continue

        mes = data_comp.replace(day=1)
        categoria = _categoria_pescado(grupo)
        hash_linha = _hash([
            parceiro.upper(), cidade.upper(), estado.upper(), data_comp,
            grupo.upper(), produto or "", valor, volume, top, path.name
        ])

        records.append({
            "parceiro": parceiro or None,
            "cidade": cidade,
            "estado": estado,
            "data_competencia": data_comp,
            "mes": mes,
            "grupo_produto": grupo,
            "categoria_pescado": categoria,
            "vlr_total_liquido": valor,
            "volume": volume,
            "produto": produto,
            "top": top,
            "fonte_arquivo": path.name,
            "hash_linha": hash_linha,
        })

    if records:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                ALTER TABLE app.fato_receita_manual_expansao
                    ADD COLUMN IF NOT EXISTS volume NUMERIC,
                    ADD COLUMN IF NOT EXISTS produto TEXT,
                    ADD COLUMN IF NOT EXISTS top TEXT;
            """))
            conn.execute(text("""
                INSERT INTO app.fato_receita_manual_expansao (
                    parceiro, cidade, estado, data_competencia, mes,
                    grupo_produto, categoria_pescado, vlr_total_liquido,
                    volume, produto, top, fonte_arquivo, hash_linha
                )
                VALUES (
                    :parceiro, :cidade, :estado, :data_competencia, :mes,
                    :grupo_produto, :categoria_pescado, :vlr_total_liquido,
                    :volume, :produto, :top, :fonte_arquivo, :hash_linha
                )
                ON CONFLICT (hash_linha)
                DO UPDATE SET
                    parceiro = EXCLUDED.parceiro,
                    cidade = EXCLUDED.cidade,
                    estado = EXCLUDED.estado,
                    data_competencia = EXCLUDED.data_competencia,
                    mes = EXCLUDED.mes,
                    grupo_produto = EXCLUDED.grupo_produto,
                    categoria_pescado = EXCLUDED.categoria_pescado,
                    vlr_total_liquido = EXCLUDED.vlr_total_liquido,
                    volume = EXCLUDED.volume,
                    produto = EXCLUDED.produto,
                    top = EXCLUDED.top,
                    fonte_arquivo = EXCLUDED.fonte_arquivo,
                    data_carga = NOW();
            """), records)

    return {
        "tipo": "RECEITA_MANUAL_EXPANSAO",
        "arquivo": str(path),
        "registros_lidos": int(len(df)),
        "registros_processados": int(len(records)),
        "registros_rejeitados": int(rejeitados),
        "registros_rejeitados_top": int(rejeitados_top),
        "top_obrigatorio": TOP_RECEITA_EXPANSAO_OBRIGATORIO,
    }

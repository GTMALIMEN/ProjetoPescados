from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


def _norm_col(col: Any) -> str:
    s = str(col or "").strip().lower()
    table = str.maketrans("áàãâéêíóôõúç", "aaaaeeiooouc")
    s = s.translate(table)
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _read_table(arquivo: str | Path) -> pd.DataFrame:
    path = Path(arquivo)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")
    if path.suffix.lower() in {".xlsx", ".xlsm", ".xls"}:
        df = pd.read_excel(path)
    elif path.suffix.lower() in {".csv", ".txt"}:
        df = pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")
    else:
        raise ValueError("Formato não suportado. Use .xlsx, .xls, .csv ou .txt")
    df = df.rename(columns={c: _norm_col(c) for c in df.columns}).dropna(how="all")
    return df


def _pick(df: pd.DataFrame, aliases: list[str], required: bool = False) -> str | None:
    for alias in [_norm_col(a) for a in aliases]:
        if alias in df.columns:
            return alias
    if required:
        raise ValueError(f"Coluna obrigatória ausente. Aceitas: {aliases}")
    return None


def _to_number(value):
    if value is None or pd.isna(value):
        return None
    s = str(value).strip().replace("R$", "").replace("%", "").replace("\xa0", " ")
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
    return None if pd.isna(dt) else dt.date()


def _hash_row(values: list[Any]) -> str:
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


def _log(tipo: str, arquivo: str | Path, status: str, lidos: int, processados: int, rejeitados: int, detalhe: str = "") -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.importacao_manual_log (
                tipo_importacao, arquivo, status, registros_lidos,
                registros_processados, registros_rejeitados, detalhe
            ) VALUES (:tipo, :arquivo, :status, :lidos, :processados, :rejeitados, :detalhe)
        """), {
            "tipo": tipo, "arquivo": str(arquivo), "status": status,
            "lidos": int(lidos or 0), "processados": int(processados or 0),
            "rejeitados": int(rejeitados or 0), "detalhe": detalhe,
        })


def carregar_ceagesp_manual(arquivo: str | Path) -> dict:
    df = _read_table(arquivo)
    lidos = len(df)
    col_data = _pick(df, ["data_referencia", "data", "dt_referencia", "referencia"], True)
    col_produto = _pick(df, ["produto", "pescado", "item"], True)
    col_class = _pick(df, ["classificacao", "classificação", "tipo", "descricao"])
    col_unidade = _pick(df, ["unidade", "unid", "embalagem"])
    col_min = _pick(df, ["preco_minimo", "preço mínimo", "menor", "minimo"])
    col_comum = _pick(df, ["preco_comum", "preço comum", "comum", "preco", "valor"])
    col_max = _pick(df, ["preco_maximo", "preço máximo", "maior", "maximo"])
    col_fonte = _pick(df, ["fonte"])
    col_url = _pick(df, ["url_fonte", "url", "link"])
    records, rejeitados = [], 0
    for _, row in df.iterrows():
        data_ref = _to_date(row.get(col_data))
        produto = str(row.get(col_produto) or "").strip()
        if not data_ref or not produto:
            rejeitados += 1
            continue
        classificacao = str(row.get(col_class) or "").strip() if col_class else ""
        unidade = str(row.get(col_unidade) or "").strip() if col_unidade else ""
        chave = _hash_row([data_ref, produto.upper(), classificacao.upper(), unidade.upper()])
        records.append({
            "chave_registro": chave,
            "data_referencia": data_ref,
            "produto": produto,
            "classificacao": classificacao or None,
            "unidade": unidade or None,
            "preco_minimo": _to_number(row.get(col_min)) if col_min else None,
            "preco_comum": _to_number(row.get(col_comum)) if col_comum else None,
            "preco_maximo": _to_number(row.get(col_max)) if col_max else None,
            "fonte": str(row.get(col_fonte) or "CEAGESP manual").strip() if col_fonte else "CEAGESP manual",
            "url_fonte": str(row.get(col_url) or "").strip() if col_url else None,
            "hash_carga": chave,
        })
    if records:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO app.fato_ceagesp_pescados (
                    chave_registro, data_referencia, produto, classificacao, unidade,
                    preco_minimo, preco_comum, preco_maximo, fonte, url_fonte, hash_carga
                ) VALUES (
                    :chave_registro, :data_referencia, :produto, :classificacao, :unidade,
                    :preco_minimo, :preco_comum, :preco_maximo, :fonte, :url_fonte, :hash_carga
                )
                ON CONFLICT (chave_registro) DO UPDATE SET
                    preco_minimo = EXCLUDED.preco_minimo,
                    preco_comum = EXCLUDED.preco_comum,
                    preco_maximo = EXCLUDED.preco_maximo,
                    fonte = EXCLUDED.fonte,
                    url_fonte = EXCLUDED.url_fonte,
                    hash_carga = EXCLUDED.hash_carga,
                    data_coleta = NOW();
            """), records)
    _log("CEAGESP_MANUAL", arquivo, "SUCESSO", lidos, len(records), rejeitados)
    return {"tipo": "CEAGESP_MANUAL", "lidos": lidos, "processados": len(records), "rejeitados": rejeitados}


def carregar_compra_manual(arquivo: str | Path) -> dict:
    df = _read_table(arquivo)
    lidos = len(df)
    col_data = _pick(df, ["data", "dt_compra", "data_compra", "mes"], True)
    col_fornecedor = _pick(df, ["fornecedor"])
    col_marca = _pick(df, ["marca"])
    col_produto = _pick(df, ["produto", "item"], True)
    col_categoria = _pick(df, ["categoria"])
    col_preco = _pick(df, ["preco_compra", "preço compra", "preco", "valor_unitario", "valor"], True)
    col_qtd = _pick(df, ["quantidade_comprada", "quantidade", "qtd", "volume"])
    col_unidade = _pick(df, ["unidade", "unid"])
    col_obs = _pick(df, ["observacao", "observação", "obs"])
    records, rejeitados = [], 0
    for _, row in df.iterrows():
        data = _to_date(row.get(col_data))
        produto = str(row.get(col_produto) or "").strip()
        preco = _to_number(row.get(col_preco))
        if not data or not produto or preco is None:
            rejeitados += 1
            continue
        mes = data.replace(day=1)
        fornecedor = str(row.get(col_fornecedor) or "").strip() if col_fornecedor else ""
        marca = str(row.get(col_marca) or "").strip() if col_marca else ""
        unidade = str(row.get(col_unidade) or "").strip() if col_unidade else ""
        hash_linha = _hash_row([data, fornecedor.upper(), marca.upper(), produto.upper(), preco, row.get(col_qtd) if col_qtd else None, unidade.upper()])
        records.append({
            "data": data, "mes": mes, "fornecedor": fornecedor or None, "marca": marca or None,
            "produto": produto, "categoria": str(row.get(col_categoria) or "").strip() if col_categoria else None,
            "preco_compra": preco, "quantidade_comprada": _to_number(row.get(col_qtd)) if col_qtd else None,
            "unidade": unidade or None, "observacao": str(row.get(col_obs) or "").strip() if col_obs else None,
            "fonte_arquivo": Path(arquivo).name, "hash_linha": hash_linha,
        })
    if records:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO app.fato_compra_manual (
                    data, mes, fornecedor, marca, produto, categoria, preco_compra,
                    quantidade_comprada, unidade, observacao, fonte_arquivo, hash_linha
                ) VALUES (
                    :data, :mes, :fornecedor, :marca, :produto, :categoria, :preco_compra,
                    :quantidade_comprada, :unidade, :observacao, :fonte_arquivo, :hash_linha
                )
                ON CONFLICT (hash_linha) DO UPDATE SET
                    preco_compra = EXCLUDED.preco_compra,
                    quantidade_comprada = EXCLUDED.quantidade_comprada,
                    observacao = EXCLUDED.observacao,
                    data_carga = NOW();
            """), records)
    _log("COMPRA_MANUAL", arquivo, "SUCESSO", lidos, len(records), rejeitados)
    return {"tipo": "COMPRA_MANUAL", "lidos": lidos, "processados": len(records), "rejeitados": rejeitados}


def carregar_previa_vendedores(arquivo: str | Path) -> dict:
    df = _read_table(arquivo)
    lidos = len(df)
    col_vendedor = _pick(df, ["vendedor", "nome_vendedor"], True)
    col_produto = _pick(df, ["produto", "item"], True)
    col_preco = _pick(df, ["preco", "preço", "preco_venda", "valor_unitario"], True)
    col_data = _pick(df, ["data_venda", "data", "dt_venda"], True)
    col_qtd = _pick(df, ["quantidade_vendida", "quantidade", "qtd"], True)
    col_receita = _pick(df, ["receita_total", "receita", "valor_total", "total"])
    col_cliente = _pick(df, ["cliente", "parceiro"])
    col_regiao = _pick(df, ["regiao", "regiao_comercial", "microrregiao"])
    col_obs = _pick(df, ["observacao", "observação", "obs"])
    records, rejeitados = [], 0
    for _, row in df.iterrows():
        vendedor = str(row.get(col_vendedor) or "").strip()
        produto = str(row.get(col_produto) or "").strip()
        data = _to_date(row.get(col_data))
        preco = _to_number(row.get(col_preco))
        qtd = _to_number(row.get(col_qtd))
        if not vendedor or not produto or not data or preco is None or qtd is None:
            rejeitados += 1
            continue
        receita = _to_number(row.get(col_receita)) if col_receita else None
        if receita is None:
            receita = preco * qtd
        cliente = str(row.get(col_cliente) or "").strip() if col_cliente else ""
        regiao = str(row.get(col_regiao) or "").strip() if col_regiao else ""
        hash_linha = _hash_row([vendedor.upper(), produto.upper(), data, preco, qtd, cliente.upper(), regiao.upper()])
        records.append({
            "vendedor": vendedor, "produto": produto, "preco": preco, "data_venda": data,
            "quantidade_vendida": qtd, "receita_total": receita, "cliente": cliente or None,
            "regiao": regiao or None, "observacao": str(row.get(col_obs) or "").strip() if col_obs else None,
            "fonte": f"manual:{Path(arquivo).name}", "hash_linha": hash_linha,
        })
    if records:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO app.fato_previa_vendedores (
                    vendedor, produto, preco, data_venda, quantidade_vendida,
                    receita_total, cliente, regiao, observacao, fonte, hash_linha
                ) VALUES (
                    :vendedor, :produto, :preco, :data_venda, :quantidade_vendida,
                    :receita_total, :cliente, :regiao, :observacao, :fonte, :hash_linha
                )
                ON CONFLICT (hash_linha) DO UPDATE SET
                    preco = EXCLUDED.preco,
                    quantidade_vendida = EXCLUDED.quantidade_vendida,
                    receita_total = EXCLUDED.receita_total,
                    observacao = EXCLUDED.observacao,
                    data_carga = NOW();
            """), records)
    _log("PREVIA_VENDEDORES", arquivo, "SUCESSO", lidos, len(records), rejeitados)
    return {"tipo": "PREVIA_VENDEDORES", "lidos": lidos, "processados": len(records), "rejeitados": rejeitados}


def carregar_idh_municipal(arquivo: str | Path) -> dict:
    df = _read_table(arquivo)
    lidos = len(df)
    col_cod = _pick(df, ["codigo_ibge", "cod_ibge", "codmun", "cod_municipio", "codigo_municipio", "ibge"])
    col_uf = _pick(df, ["uf", "estado"])
    col_mun = _pick(df, ["municipio", "município", "nome_municipio"])
    col_idh = _pick(df, ["idh", "idhm", "id_humano_municipal", "indice_desenvolvimento_humano_municipal"], True)
    col_ano = _pick(df, ["ano", "periodo", "referencia"])
    col_fonte = _pick(df, ["fonte"])
    records, rejeitados = [], 0
    for _, row in df.iterrows():
        codigo = str(row.get(col_cod) or "").strip() if col_cod else ""
        uf = str(row.get(col_uf) or "").strip().upper() if col_uf else ""
        municipio = str(row.get(col_mun) or "").strip() if col_mun else ""
        idh = _to_number(row.get(col_idh))
        if idh is None or (not codigo and not (uf and municipio)):
            rejeitados += 1
            continue
        fonte = str(row.get(col_fonte) or "").strip() if col_fonte else "Atlas Brasil/IPEA/PNUD/FJP - importação manual"
        ano = str(row.get(col_ano) or "").strip() if col_ano else ""
        records.append({"codigo_ibge": codigo, "uf": uf, "municipio": municipio, "idh": idh, "fonte": fonte, "ano": ano})
    processados = 0
    if records:
        engine = get_engine()
        with engine.begin() as conn:
            for rec in records:
                if rec["codigo_ibge"]:
                    sql = """
                        UPDATE app.fato_expansao_municipio
                        SET idh = :idh,
                            fonte_idh = :fonte,
                            observacao = COALESCE(observacao, '') || CASE WHEN :ano <> '' THEN ' | IDH ano ' || :ano ELSE '' END,
                            data_atualizacao = NOW()
                        WHERE codigo_ibge = :codigo_ibge
                    """
                else:
                    sql = """
                        UPDATE app.fato_expansao_municipio
                        SET idh = :idh,
                            fonte_idh = :fonte,
                            observacao = COALESCE(observacao, '') || CASE WHEN :ano <> '' THEN ' | IDH ano ' || :ano ELSE '' END,
                            data_atualizacao = NOW()
                        WHERE uf = :uf
                          AND unaccent(lower(municipio)) = unaccent(lower(:municipio))
                    """
                result = conn.execute(text(sql), rec)
                processados += result.rowcount or 0
    _log("IDH_MUNICIPAL", arquivo, "SUCESSO", lidos, processados, rejeitados)
    return {"tipo": "IDH_MUNICIPAL", "lidos": lidos, "processados": processados, "rejeitados": rejeitados}

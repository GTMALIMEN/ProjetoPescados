from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
import uuid
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.collectors.comexstat_collector import ComexStatCollector
from src.config.settings import settings
from src.database.connection import get_engine
from src.utils.logs import get_logger


logger = get_logger(__name__)


def parse_decimal(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)

    txt = str(value).strip().replace("R$", "").replace("US$", "").replace(" ", "")
    if not txt:
        return None
    if "," in txt and "." in txt:
        txt = txt.replace(".", "").replace(",", ".")
    elif "," in txt:
        txt = txt.replace(",", ".")
    try:
        return float(txt)
    except Exception:
        return None


def parse_date(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, str):
        txt = value.strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}", txt):
            dt = pd.to_datetime(txt, errors="coerce", yearfirst=True)
        else:
            dt = pd.to_datetime(txt, errors="coerce", dayfirst=True)
    else:
        dt = pd.to_datetime(value, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return None
    return dt.date()


def safe_str(value, default=""):
    if value is None or pd.isna(value):
        return default
    out = str(value).strip()
    return out if out else default


def clean_records(df: pd.DataFrame) -> list[dict]:
    out = []
    for row in df.astype(object).to_dict(orient="records"):
        out.append({k: (None if pd.isna(v) else v) for k, v in row.items()})
    return out


def natural_key(row: dict) -> str:
    key = "|".join([
        str(row.get("data") or ""),
        safe_str(row.get("fonte")),
        safe_str(row.get("indicador")),
        safe_str(row.get("categoria")),
        safe_str(row.get("subcategoria")),
        safe_str(row.get("produto")),
        safe_str(row.get("uf")),
        safe_str(row.get("regiao")),
        safe_str(row.get("periodicidade")),
    ])
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def registrar_run(engine, run_id: str, fonte: str, mensagem: str):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.etl_run (
                run_id, fonte, tipo_execucao, ambiente, status, mensagem
            )
            VALUES (
                :run_id, :fonte, 'fonte_real_setorial', :ambiente, 'INICIADO', :mensagem
            )
        """), {
            "run_id": run_id,
            "fonte": fonte,
            "ambiente": settings.app_env,
            "mensagem": mensagem,
        })


def finalizar_run(engine, run_id: str, status: str, mensagem: str):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE app.etl_run
            SET status = :status,
                mensagem = :mensagem,
                finalizado_em = NOW()
            WHERE run_id = :run_id
        """), {"run_id": run_id, "status": status, "mensagem": mensagem})


def registrar_controle(engine, run_id: str, fonte: str, status: str, mensagem: str, qtd_raw: int, qtd_dw: int, tempo: float):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.etl_controle_carga (
                run_id, fonte, indicador, status, mensagem, qtd_registros,
                qtd_raw, qtd_staging, qtd_dw, qtd_rejeitados, tempo_execucao_segundos
            )
            VALUES (
                :run_id, :fonte, 'Fonte real setorial', :status, :mensagem, :qtd_dw,
                :qtd_raw, :qtd_dw, :qtd_dw, 0, :tempo
            )
        """), {
            "run_id": run_id,
            "fonte": fonte,
            "status": status,
            "mensagem": mensagem,
            "qtd_raw": qtd_raw,
            "qtd_dw": qtd_dw,
            "tempo": tempo,
        })

        conn.execute(text("""
            INSERT INTO app.etl_fonte_real_resumo (
                run_id, fonte, origem, status, registros_lidos, registros_dw, detalhe
            )
            VALUES (
                :run_id, :fonte, :origem, :status, :registros_lidos, :registros_dw, :detalhe
            )
        """), {
            "run_id": run_id,
            "fonte": fonte,
            "origem": fonte,
            "status": status,
            "registros_lidos": qtd_raw,
            "registros_dw": qtd_dw,
            "detalhe": mensagem,
        })


def upsert_setorial(engine, df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    temp = df.copy()
    temp["natural_key_hash"] = temp.apply(lambda r: natural_key(r.to_dict()), axis=1)
    records = clean_records(temp)

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO dw.fato_indicador_setorial (
                data,
                fonte,
                indicador,
                categoria,
                subcategoria,
                produto,
                uf,
                regiao,
                valor,
                unidade,
                periodicidade,
                natural_key_hash
            )
            VALUES (
                :data,
                :fonte,
                :indicador,
                :categoria,
                :subcategoria,
                :produto,
                :uf,
                :regiao,
                :valor,
                :unidade,
                :periodicidade,
                :natural_key_hash
            )
            ON CONFLICT (natural_key_hash)
            DO UPDATE SET
                valor = EXCLUDED.valor,
                unidade = EXCLUDED.unidade,
                data_coleta = NOW();
        """), records)

    return len(records)


def load_comex_config(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def salvar_raw_comex(engine, run_id: str, metadata: dict):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO raw.comexstat_payload (
                run_id,
                endpoint,
                request_payload,
                response_payload,
                status_http
            )
            VALUES (
                :run_id,
                :endpoint,
                CAST(:request_payload AS JSONB),
                CAST(:response_payload AS JSONB),
                :status_http
            )
        """), {
            "run_id": run_id,
            "endpoint": metadata.get("endpoint"),
            "request_payload": json.dumps(metadata.get("request_payload", {}), ensure_ascii=False),
            "response_payload": json.dumps(metadata.get("response_payload", {}), ensure_ascii=False),
            "status_http": metadata.get("status_http"),
        })


def carregar_comex_pescados(
    ano_inicio: int,
    ano_fim: int,
    config_path: str = "config/comex_pescados_ncm.json",
    delay_entre_grupos: int = 12,
) -> None:
    engine = get_engine()
    run_id = str(uuid.uuid4())
    inicio = time.perf_counter()
    fonte = "Comex Stat"

    registrar_run(engine, run_id, fonte, f"Comex pescados {ano_inicio}-{ano_fim}")

    try:
        cfg = load_comex_config(config_path)
        collector = ComexStatCollector()

        all_records = []
        raw_rows = 0

        grupos = list(cfg["groups"].items())

        for idx_grupo, (grupo, grupo_cfg) in enumerate(grupos, start=1):
            ncms = grupo_cfg["ncms"]
            produto_nome = grupo_cfg.get("produto", grupo)

            if idx_grupo > 1 and delay_entre_grupos > 0:
                print(f"⏳ Aguardando {delay_entre_grupos}s antes do próximo grupo Comex...")
                time.sleep(delay_entre_grupos)

            print(f"🔎 Consultando Comex Stat: {grupo} | NCMs={ncms}")

            df_raw, metadata = collector.consultar_general(
                flow=cfg.get("flow", "import"),
                year_start=ano_inicio,
                year_end=ano_fim,
                ncms=ncms,
                month_detail=cfg.get("month_detail", True),
            )
            salvar_raw_comex(engine, run_id, metadata)
            raw_rows += len(df_raw)

            if df_raw.empty:
                continue

            # Agrega por mês e grupo.
            agg = (
                df_raw
                .groupby("data", as_index=False)
                .agg(valor_usd_fob=("valor_usd_fob", "sum"), peso_kg=("peso_kg", "sum"))
            )

            for _, row in agg.iterrows():
                data = row["data"]
                valor_usd = float(row["valor_usd_fob"] or 0)
                peso_kg = float(row["peso_kg"] or 0)
                preco_medio = (valor_usd / peso_kg) if peso_kg else None

                all_records.extend([
                    {
                        "data": data,
                        "fonte": fonte,
                        "indicador": f"importacao_{grupo}_usd_fob",
                        "categoria": "comercio_exterior",
                        "subcategoria": "importacao",
                        "produto": produto_nome,
                        "uf": "BR",
                        "regiao": "",
                        "valor": valor_usd,
                        "unidade": "US$ FOB",
                        "periodicidade": "mensal",
                    },
                    {
                        "data": data,
                        "fonte": fonte,
                        "indicador": f"importacao_{grupo}_kg",
                        "categoria": "comercio_exterior",
                        "subcategoria": "importacao",
                        "produto": produto_nome,
                        "uf": "BR",
                        "regiao": "",
                        "valor": peso_kg,
                        "unidade": "kg",
                        "periodicidade": "mensal",
                    },
                    {
                        "data": data,
                        "fonte": fonte,
                        "indicador": f"preco_medio_importacao_{grupo}_usd_kg",
                        "categoria": "comercio_exterior",
                        "subcategoria": "preco_medio_importacao",
                        "produto": produto_nome,
                        "uf": "BR",
                        "regiao": "",
                        "valor": preco_medio,
                        "unidade": "US$/kg",
                        "periodicidade": "mensal",
                    },
                ])

        df = pd.DataFrame(all_records)
        df = df[df["valor"].notna()].copy() if not df.empty else df
        qtd_dw = upsert_setorial(engine, df)

        tempo = time.perf_counter() - inicio
        mensagem = f"Carga Comex Stat concluída | raw={raw_rows} | dw={qtd_dw}"

        registrar_controle(engine, run_id, fonte, "SUCESSO", mensagem, raw_rows, qtd_dw, tempo)
        finalizar_run(engine, run_id, "SUCESSO", mensagem)

        print(f"\n✅ {mensagem}")

    except Exception as exc:
        tempo = time.perf_counter() - inicio
        logger.exception("Erro na carga Comex Stat")
        registrar_controle(engine, run_id, fonte, "ERRO_API", str(exc), 0, 0, tempo)
        finalizar_run(engine, run_id, "ERRO_API", str(exc))
        raise


def read_generic_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")
    if suffix in [".xlsx", ".xls"]:
        return pd.read_excel(path)
    if suffix == ".xlsb":
        return pd.read_excel(path, engine="pyxlsb")
    raise ValueError(f"Formato não suportado: {suffix}")


def normalize_col(value: object) -> str:
    import unicodedata
    txt = str(value or "").strip().lower()
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(ch for ch in txt if not unicodedata.combining(ch))
    txt = re.sub(r"[^a-z0-9]+", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()


def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols = {normalize_col(c): c for c in df.columns}
    for cand in candidates:
        key = normalize_col(cand)
        if key in cols:
            return cols[key]
    for cand in candidates:
        key = normalize_col(cand)
        for norm, original in cols.items():
            if key and key in norm:
                return original
    return None


def guess_produto(row, produto_col, indicador_default: str) -> str:
    if produto_col:
        return safe_str(row.get(produto_col), indicador_default)
    return indicador_default


def carregar_arquivo_fonte_real(
    arquivo: str,
    fonte: str,
    categoria_default: str,
    produto_default: str,
    uf_default: str = "MG",
    subcategoria_default: str = "fonte_real",
) -> None:
    """
    Loader genérico para planilhas reais baixadas manualmente.
    Funciona bem para arquivos CEPEA/CONAB quando há colunas de data/período e valor/preço.
    """
    engine = get_engine()
    path = Path(arquivo)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

    run_id = str(uuid.uuid4())
    inicio = time.perf_counter()

    registrar_run(engine, run_id, fonte, f"Carga arquivo real: {path.name}")

    try:
        df_raw = read_generic_file(path)

        data_col = find_col(df_raw, ["data", "dt", "periodo", "período", "mes", "mês"])
        valor_col = find_col(df_raw, ["valor", "preco", "preço", "r$", "valor r", "valor rs"])
        produto_col = find_col(df_raw, ["produto", "mercadoria", "item"])
        uf_col = find_col(df_raw, ["uf", "estado"])
        unidade_col = find_col(df_raw, ["unidade", "medida"])
        indicador_col = find_col(df_raw, ["indicador", "serie", "série"])

        if not data_col or not valor_col:
            raise ValueError(
                f"Não consegui detectar colunas de data e valor. "
                f"data_col={data_col}, valor_col={valor_col}, colunas={list(df_raw.columns)}"
            )

        records = []
        for _, row in df_raw.iterrows():
            data = parse_date(row.get(data_col))
            valor = parse_decimal(row.get(valor_col))
            if not data or valor is None:
                continue

            produto = guess_produto(row, produto_col, produto_default)
            indicador = safe_str(row.get(indicador_col), f"preco_{produto.lower().replace(' ', '_')}")
            uf = safe_str(row.get(uf_col), uf_default).upper()
            unidade = safe_str(row.get(unidade_col), "R$")

            records.append({
                "data": data,
                "fonte": fonte,
                "indicador": indicador,
                "categoria": categoria_default,
                "subcategoria": subcategoria_default,
                "produto": produto,
                "uf": uf,
                "regiao": "",
                "valor": valor,
                "unidade": unidade,
                "periodicidade": "mensal",
            })

        df = pd.DataFrame(records)
        qtd_dw = upsert_setorial(engine, df)

        tempo = time.perf_counter() - inicio
        mensagem = f"Carga {fonte} concluída | arquivo={path.name} | lidos={len(df_raw)} | dw={qtd_dw}"

        registrar_controle(engine, run_id, fonte, "SUCESSO", mensagem, len(df_raw), qtd_dw, tempo)
        finalizar_run(engine, run_id, "SUCESSO", mensagem)

        print(f"\n✅ {mensagem}")

    except Exception as exc:
        tempo = time.perf_counter() - inicio
        logger.exception("Erro na carga de fonte real")
        registrar_controle(engine, run_id, fonte, "ERRO_VALIDACAO", str(exc), 0, 0, tempo)
        finalizar_run(engine, run_id, "ERRO_VALIDACAO", str(exc))
        raise


def main():
    parser = argparse.ArgumentParser(description="Fontes reais setoriais")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_comex = sub.add_parser("comex-pescados", help="Carregar importações de pescados via Comex Stat")
    p_comex.add_argument("--ano-inicio", type=int, required=True)
    p_comex.add_argument("--ano-fim", type=int, required=True)
    p_comex.add_argument("--config", default="config/comex_pescados_ncm.json")
    p_comex.add_argument("--delay", type=int, default=12, help="Delay em segundos entre grupos/NCMs")

    p_file = sub.add_parser("arquivo", help="Carregar planilha real genérica")
    p_file.add_argument("--arquivo", required=True)
    p_file.add_argument("--fonte", required=True, choices=["CEPEA", "CONAB"])
    p_file.add_argument("--categoria", required=True)
    p_file.add_argument("--produto-default", required=True)
    p_file.add_argument("--uf-default", default="MG")
    p_file.add_argument("--subcategoria-default", default="fonte_real")

    args = parser.parse_args()

    if args.cmd == "comex-pescados":
        carregar_comex_pescados(args.ano_inicio, args.ano_fim, args.config, delay_entre_grupos=args.delay)
    elif args.cmd == "arquivo":
        carregar_arquivo_fonte_real(
            arquivo=args.arquivo,
            fonte=args.fonte,
            categoria_default=args.categoria,
            produto_default=args.produto_default,
            uf_default=args.uf_default,
            subcategoria_default=args.subcategoria_default,
        )


if __name__ == "__main__":
    main()

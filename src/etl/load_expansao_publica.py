
from __future__ import annotations

from datetime import date
import pandas as pd
import requests
from sqlalchemy import text

from src.database.connection import get_engine
from src.utils.logs import get_logger

logger = get_logger(__name__)

ESTADOS_PADRAO = ["MG", "SP", "RJ", "ES"]


def _to_number(value):
    if value is None:
        return None
    text_value = str(value).strip()
    if text_value in ("", "-", "...", "X"):
        return None
    if "," in text_value and "." in text_value:
        text_value = text_value.replace(".", "").replace(",", ".")
    elif "," in text_value:
        text_value = text_value.replace(",", ".")
    try:
        return float(text_value)
    except ValueError:
        return None


def _periodo_to_date(periodo: str) -> date:
    periodo = str(periodo or "").strip()
    if len(periodo) >= 4 and periodo[:4].isdigit():
        return date(int(periodo[:4]), 7, 1)
    return date.today()


def _get_sidra(tabela: str, variavel: str, periodo: str = "last") -> tuple[list[dict], dict]:
    url = f"https://apisidra.ibge.gov.br/values/t/{tabela}/n6/all/v/{variavel}/p/{periodo}"
    response = requests.get(
        url,
        params={"formato": "json"},
        headers={"Accept": "application/json", "User-Agent": "radar-pescados-ia/2.0"},
        timeout=180,
    )
    response.raise_for_status()
    return response.json(), {"url": response.url, "status_http": response.status_code}


def _parse_sidra(payload: list[dict], tabela: str, variavel: str, indicador: str, categoria: str, unidade: str) -> pd.DataFrame:
    if not payload or len(payload) <= 1:
        return pd.DataFrame()

    header = payload[0]
    rows = payload[1:]

    # SIDRA costuma retornar códigos como D1C/D1N ou D2C/D2N.
    code_keys = [k for k, v in header.items() if "município" in str(v).lower() and "código" in str(v).lower()]
    name_keys = [k for k, v in header.items() if str(v).lower() in ("município", "municipio")]
    period_keys = [k for k, v in header.items() if "ano" in str(v).lower() and "código" in str(v).lower()]
    value_key = "V" if "V" in header else None

    if not code_keys:
        code_keys = [k for k in header.keys() if str(k).endswith("C") and k.startswith("D")]
    if not name_keys:
        name_keys = [k for k in header.keys() if str(k).endswith("N") and k.startswith("D")]
    if not period_keys:
        period_keys = [k for k in header.keys() if str(k).endswith("C") and "D" in str(k)]

    key_cod = code_keys[-1] if code_keys else None
    key_nome = name_keys[-1] if name_keys else None
    key_periodo = period_keys[0] if period_keys else None

    records = []
    for row in rows:
        codigo = str(row.get(key_cod) or "").strip() if key_cod else ""
        # Remove Brasil/UF agregados; município tem 7 dígitos.
        if len(codigo) != 7 or not codigo.isdigit():
            continue

        valor = _to_number(row.get(value_key)) if value_key else None
        if valor is None:
            continue

        records.append({
            "codigo_ibge": codigo,
            "municipio": str(row.get(key_nome) or "").strip() if key_nome else None,
            "periodo": str(row.get(key_periodo) or "").strip() if key_periodo else "",
            "valor": valor,
            "tabela_sidra": tabela,
            "variavel_codigo": variavel,
            "variavel_nome": indicador,
            "indicador": indicador,
            "categoria": categoria,
            "unidade": unidade,
        })
    return pd.DataFrame(records)


def _upsert_indicador_municipal(df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    engine = get_engine()
    with engine.begin() as conn:
        geo = pd.read_sql(text("SELECT codigo_ibge, uf, municipio AS municipio_geo FROM dw.dim_geografia"), conn)

    out = df.merge(geo, on="codigo_ibge", how="left")
    out["uf"] = out["uf"].fillna("")
    out["municipio"] = out["municipio"].fillna(out["municipio_geo"])
    out["data_referencia"] = out["periodo"].apply(_periodo_to_date)

    records = []
    for row in out.to_dict(orient="records"):
        records.append({
            "data_referencia": row["data_referencia"],
            "fonte": "IBGE/SIDRA",
            "tabela_sidra": str(row["tabela_sidra"]),
            "variavel_codigo": str(row["variavel_codigo"]),
            "variavel_nome": str(row["variavel_nome"]),
            "indicador": str(row["indicador"]),
            "categoria": str(row["categoria"]),
            "uf": row.get("uf"),
            "codigo_ibge": str(row["codigo_ibge"]),
            "municipio": row.get("municipio"),
            "valor": row.get("valor"),
            "unidade": row.get("unidade"),
        })

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO dw.fato_indicador_municipal (
                data_referencia, fonte, tabela_sidra, variavel_codigo, variavel_nome,
                indicador, categoria, uf, codigo_ibge, municipio, valor, unidade
            )
            VALUES (
                :data_referencia, :fonte, :tabela_sidra, :variavel_codigo, :variavel_nome,
                :indicador, :categoria, :uf, :codigo_ibge, :municipio, :valor, :unidade
            )
            ON CONFLICT (
                data_referencia, fonte, tabela_sidra, variavel_codigo, indicador, codigo_ibge
            )
            DO UPDATE SET
                variavel_nome = EXCLUDED.variavel_nome,
                categoria = EXCLUDED.categoria,
                uf = EXCLUDED.uf,
                municipio = EXCLUDED.municipio,
                valor = EXCLUDED.valor,
                unidade = EXCLUDED.unidade,
                data_coleta = NOW();
        """), records)
    return len(records)


def preparar_base_expansao_municipal(estados: list[str] | None = None) -> int:
    estados = estados or ESTADOS_PADRAO
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(text("""
            INSERT INTO app.fato_expansao_municipio (
                codigo_ibge, uf, nome_uf, municipio, mesorregiao, microrregiao, regiao_comercial,
                status_dados, observacao, data_atualizacao
            )
            SELECT
                codigo_ibge, uf, nome_uf, municipio, mesorregiao, microrregiao, regiao_comercial,
                'parcial',
                'Base geográfica IBGE. Indicadores são preenchidos por cargas públicas/manuais.',
                NOW()
            FROM dw.dim_geografia
            WHERE uf = ANY(:estados)
              AND codigo_ibge IS NOT NULL
            ON CONFLICT (codigo_ibge)
            DO UPDATE SET
                uf = EXCLUDED.uf,
                nome_uf = EXCLUDED.nome_uf,
                municipio = EXCLUDED.municipio,
                mesorregiao = EXCLUDED.mesorregiao,
                microrregiao = EXCLUDED.microrregiao,
                regiao_comercial = EXCLUDED.regiao_comercial,
                data_atualizacao = NOW();
        """), {"estados": estados})
    return result.rowcount or 0


def atualizar_populacao_da_dw(estados: list[str] | None = None) -> int:
    estados = estados or ESTADOS_PADRAO
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(text("""
            WITH pop AS (
                SELECT DISTINCT ON (codigo_ibge)
                    codigo_ibge, valor AS populacao, tabela_sidra, variavel_codigo
                FROM dw.fato_indicador_municipal
                WHERE indicador ILIKE '%popula%'
                  AND valor IS NOT NULL
                ORDER BY codigo_ibge, data_referencia DESC, data_coleta DESC, id DESC
            )
            UPDATE app.fato_expansao_municipio e
            SET populacao = pop.populacao,
                fonte_populacao = 'IBGE/SIDRA tabela ' || pop.tabela_sidra || ' variável ' || pop.variavel_codigo,
                data_atualizacao = NOW()
            FROM pop
            WHERE e.codigo_ibge = pop.codigo_ibge
              AND e.uf = ANY(:estados);
        """), {"estados": estados})
    return result.rowcount or 0


def carregar_pib_municipal_sidra(estados: list[str] | None = None, periodo: str = "last", variavel: str = "37") -> int:
    estados = estados or ESTADOS_PADRAO
    logger.info("Coletando PIB municipal IBGE/SIDRA tabela 5938 variável %s", variavel)
    payload, metadata = _get_sidra(tabela="5938", variavel=variavel, periodo=periodo)
    df = _parse_sidra(payload, tabela="5938", variavel=variavel, indicador="PIB municipal", categoria="economia", unidade="Mil Reais")
    if df.empty:
        logger.warning("PIB SIDRA retornou vazio.")
        return 0

    qtd_dw = _upsert_indicador_municipal(df)
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(text("""
            WITH pib AS (
                SELECT DISTINCT ON (codigo_ibge)
                    codigo_ibge, valor AS pib, tabela_sidra, variavel_codigo
                FROM dw.fato_indicador_municipal
                WHERE indicador ILIKE '%PIB%'
                  AND valor IS NOT NULL
                ORDER BY codigo_ibge, data_referencia DESC, data_coleta DESC, id DESC
            )
            UPDATE app.fato_expansao_municipio e
            SET pib = pib.pib,
                pib_per_capita = CASE WHEN e.populacao IS NOT NULL AND e.populacao > 0 THEN pib.pib / e.populacao ELSE NULL END,
                fonte_pib = 'IBGE/SIDRA tabela ' || pib.tabela_sidra || ' variável ' || pib.variavel_codigo,
                data_atualizacao = NOW()
            FROM pib
            WHERE e.codigo_ibge = pib.codigo_ibge
              AND e.uf = ANY(:estados);
        """), {"estados": estados})
    return result.rowcount or qtd_dw


def carregar_expansao_publica(estados: list[str] | None = None, carregar_pib: bool = True) -> dict:
    estados = estados or ESTADOS_PADRAO
    resumo = {}
    resumo["base_municipal"] = preparar_base_expansao_municipal(estados=estados)
    resumo["populacao_atualizada"] = atualizar_populacao_da_dw(estados=estados)

    if carregar_pib:
        try:
            resumo["pib_atualizado"] = carregar_pib_municipal_sidra(estados=estados)
        except Exception as exc:
            logger.exception("Falha ao carregar PIB municipal IBGE/SIDRA")
            resumo["pib_atualizado"] = 0
            resumo["erro_pib"] = str(exc)

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE app.fato_expansao_municipio
            SET
                fonte_idh = COALESCE(fonte_idh, 'Pendente: fonte externa/Atlas Brasil'),
                fonte_renda = COALESCE(fonte_renda, 'Pendente: Censo/POF/renda por município'),
                fonte_demografia = COALESCE(fonte_demografia, 'Pendente: Censo por sexo/faixa etária'),
                fonte_pdv = COALESCE(fonte_pdv, 'Pendente: base CNPJ/OSM/Google Places ou cadastro interno'),
                status_dados = CASE
                    WHEN populacao IS NOT NULL AND pib IS NOT NULL THEN 'parcial_ok_ibge'
                    WHEN populacao IS NOT NULL THEN 'parcial_populacao'
                    ELSE 'parcial_sem_indicadores'
                END,
                data_atualizacao = NOW()
            WHERE uf = ANY(:estados);
        """), {"estados": estados})
    return resumo

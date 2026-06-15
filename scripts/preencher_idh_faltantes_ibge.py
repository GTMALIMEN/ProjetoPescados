
from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


# Fallback oficial para municípios não capturados pelo parser do PNUD/Jina.
# Fonte: IBGE Cidades e Estados, indicador "IDHM Índice de desenvolvimento humano municipal",
# fonte original PNUD, ano 2010.
IDH_FALTANTES = [
    {
        "codigo_ibge": "3105509",
        "uf": "MG",
        "municipio": "Barão do Monte Alto",
        "idhm": 0.649,
        "url_fonte": "https://www.ibge.gov.br/cidades-e-estados/mg/barao-do-monte-alto.html",
    },
    {
        "codigo_ibge": "3108909",
        "uf": "MG",
        "municipio": "Brazópolis",
        "idhm": 0.692,
        "url_fonte": "https://www.ibge.gov.br/cidades-e-estados/mg/brazopolis.html",
    },
    {
        "codigo_ibge": "3119609",
        "uf": "MG",
        "municipio": "Coronel Pacheco",
        "idhm": 0.669,
        "url_fonte": "https://www.ibge.gov.br/cidades-e-estados/mg/coronel-pacheco.html",
    },
    {
        "codigo_ibge": "3122900",
        "uf": "MG",
        "municipio": "Dona Euzébia",
        "idhm": 0.701,
        "url_fonte": "https://www.ibge.gov.br/cidades-e-estados/mg/dona-euzebia.html",
    },
    {
        "codigo_ibge": "3165206",
        "uf": "MG",
        "municipio": "São Tomé das Letras",
        "idhm": 0.667,
        "url_fonte": "https://www.ibge.gov.br/cidades-e-estados/mg/sao-tome-das-letras.html",
    },
    {
        "codigo_ibge": "3515004",
        "uf": "SP",
        "municipio": "Embu das Artes",
        "idhm": 0.735,
        "url_fonte": "https://www.ibge.gov.br/cidades-e-estados/sp/embu-das-artes.html",
    },
    {
        "codigo_ibge": "3516101",
        "uf": "SP",
        "municipio": "Florínea",
        "idhm": 0.713,
        "url_fonte": "https://www.ibge.gov.br/cidades-e-estados/sp/florinea.html",
    },
    {
        "codigo_ibge": "3550001",
        "uf": "SP",
        "municipio": "São Luiz do Paraitinga",
        "idhm": 0.697,
        "url_fonte": "https://www.ibge.gov.br/cidades-e-estados/sp/sao-luiz-do-paraitinga.html",
    },
]


def main():
    engine = get_engine()
    records = []

    for row in IDH_FALTANTES:
        records.append({
            **row,
            "ano": 2010,
            "fonte": "IBGE Cidades / PNUD - fallback oficial",
        })

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.fato_idhm_municipal (
                codigo_ibge, municipio, uf, ano, idhm,
                idhm_renda, idhm_longevidade, idhm_educacao,
                ranking, fonte, url_fonte
            )
            VALUES (
                :codigo_ibge, :municipio, :uf, :ano, :idhm,
                NULL, NULL, NULL,
                NULL, :fonte, :url_fonte
            )
            ON CONFLICT (codigo_ibge)
            DO UPDATE SET
                municipio = EXCLUDED.municipio,
                uf = EXCLUDED.uf,
                ano = EXCLUDED.ano,
                idhm = EXCLUDED.idhm,
                fonte = EXCLUDED.fonte,
                url_fonte = EXCLUDED.url_fonte,
                data_carga = NOW();
        """), records)

        updated = conn.execute(text("""
            UPDATE app.fato_expansao_municipio e
            SET idh = i.idhm,
                idhm_ano = i.ano,
                idhm_renda = i.idhm_renda,
                idhm_longevidade = i.idhm_longevidade,
                idhm_educacao = i.idhm_educacao,
                fonte_idh = i.fonte || ' (' || i.ano || ')',
                data_atualizacao = NOW()
            FROM app.fato_idhm_municipal i
            WHERE e.codigo_ibge = i.codigo_ibge
              AND e.uf IN ('MG','SP','RJ','ES')
              AND e.idh IS NULL;
        """)).rowcount

        faltantes = pd.read_sql(text("""
            SELECT uf, municipio, codigo_ibge
            FROM app.vw_expansao_municipio
            WHERE uf IN ('MG','SP','RJ','ES')
              AND idh IS NULL
            ORDER BY uf, municipio
        """), conn)

    print("\nPreenchimento IDH fallback oficial IBGE/PNUD")
    print(f"- registros de fallback: {len(records)}")
    print(f"- municípios atualizados na expansão: {updated}")

    if faltantes.empty:
        print("✅ Não há mais municípios sem IDH no recorte Sudeste.")
    else:
        print("⚠️ Ainda existem municípios sem IDH:")
        print(faltantes.to_string(index=False))


if __name__ == "__main__":
    main()

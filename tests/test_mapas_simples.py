import pandas as pd

from src.services.mapas_service import (
    fig_mapa_brasil_uf,
    fig_mapa_mg_regioes,
    fig_mapa_mg_metrica,
)


def test_fig_mapa_brasil_uf_returns_figure():
    df = pd.DataFrame({
        "regiao_brasil": ["Sudeste"],
        "uf": ["MG"],
        "nome_uf": ["Minas Gerais"],
        "qtd_municipios": [853],
        "faturamento": [1000.0],
        "volume_kg": [100.0],
        "qtd_clientes": [10],
        "faturamento_por_municipio": [1.17],
    })
    fig = fig_mapa_brasil_uf(df, "qtd_municipios", "Teste")
    assert fig is not None


def test_fig_mapa_mg_regioes_returns_figure():
    df = pd.DataFrame({
        "codigo_ibge": ["3106200", "3106705"],
        "regiao_comercial": ["Grande BH / Central", "Grande BH / Central"],
        "populacao_regiao": [100, 100],
        "faturamento_regiao": [1000.0, 1000.0],
        "volume_kg_regiao": [10.0, 10.0],
        "clientes_regiao": [2, 2],
        "score_potencial": [50.0, 50.0],
        "cenario_1_10": [5, 5],
        "confianca": [80.0, 80.0],
    })
    fig = fig_mapa_mg_regioes(df)
    assert fig is not None


def test_fig_mapa_mg_metrica_returns_figure():
    df = pd.DataFrame({
        "codigo_ibge": ["3106200"],
        "regiao_comercial": ["Grande BH / Central"],
        "populacao_regiao": [100],
        "faturamento_regiao": [1000.0],
        "volume_kg_regiao": [10.0],
        "clientes_regiao": [2],
        "score_potencial": [50.0],
        "cenario_1_10": [5],
        "confianca": [80.0],
    })
    fig = fig_mapa_mg_metrica(df, "score_potencial", "Teste")
    assert fig is not None

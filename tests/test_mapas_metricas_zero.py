import pandas as pd

from src.services.mapas_service import fig_mapa_brasil_uf, fig_mapa_mg_metrica


def test_brasil_faturamento_zero_nao_quebra():
    df = pd.DataFrame({
        "regiao_brasil": ["Sudeste", "Sudeste"],
        "uf": ["MG", "SP"],
        "nome_uf": ["Minas Gerais", "São Paulo"],
        "qtd_municipios": [853, 645],
        "faturamento": [0.0, 0.0],
        "volume_kg": [0.0, 0.0],
        "qtd_clientes": [0, 0],
        "faturamento_por_municipio": [0.0, 0.0],
    })

    fig = fig_mapa_brasil_uf(df, "faturamento", "Teste")
    assert fig is not None


def test_mg_faturamento_zero_nao_quebra():
    df = pd.DataFrame({
        "codigo_ibge": ["3106200", "3106705"],
        "regiao_comercial": ["Grande BH / Central", "Sul de MG"],
        "populacao_regiao": [100, 200],
        "faturamento_regiao": [0.0, 0.0],
        "volume_kg_regiao": [0.0, 0.0],
        "clientes_regiao": [0, 0],
        "score_potencial": [0.0, 0.0],
        "cenario_1_10": [0, 0],
        "confianca": [0.0, 0.0],
    })

    fig = fig_mapa_mg_metrica(df, "faturamento_regiao", "Teste")
    assert fig is not None

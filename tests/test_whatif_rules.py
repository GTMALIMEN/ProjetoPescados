from src.services.whatif_service import (
    calcular_competitividad_simulada,
    calcular_pressao_custo_simulada,
    calcular_risco_substituicao_simulado,
)


def test_tilapia_price_up_reduces_competitiveness():
    atual = 50
    simulado = calcular_competitividad_simulada(
        competitividade_atual=atual,
        variacao_tilapia_pct=10,
        variacao_frango_pct=0,
        variacao_bovino_pct=0,
        variacao_suino_pct=0,
    )

    assert simulado < atual


def test_competitor_price_down_increases_substitution_risk():
    atual = 40
    simulado = calcular_risco_substituicao_simulado(
        risco_atual=atual,
        variacao_tilapia_pct=0,
        variacao_frango_pct=-10,
        variacao_bovino_pct=0,
        variacao_suino_pct=0,
    )

    assert simulado > atual


def test_grains_and_dollar_up_increase_cost_pressure():
    atual = 40
    simulado = calcular_pressao_custo_simulada(
        pressao_atual=atual,
        variacao_dolar_pct=10,
        variacao_graos_pct=10,
    )

    assert simulado > atual

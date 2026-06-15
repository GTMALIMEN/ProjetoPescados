import pandas as pd

from src.services.expansao_service import simular_idc_expansao, _classificar_score
from src.services.previsao_mercado_service import carregar_base_ceagesp_historico


def test_classificar_score():
    assert _classificar_score(80) == "Alta prioridade"
    assert _classificar_score(60) == "Média prioridade"
    assert _classificar_score(40) == "Baixa prioridade"
    assert _classificar_score(10) == "Monitorar"


def test_ceagesp_schema_vazio():
    df = carregar_base_ceagesp_historico()
    assert isinstance(df, pd.DataFrame)
    assert "produto" in df.columns
    assert "preco_comum" in df.columns

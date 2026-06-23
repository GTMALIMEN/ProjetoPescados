
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_app_has_weight_normalizer():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert "_ajustar_pesos_idc" in text
    assert "Total dos pesos" in text
    assert "idc_w_pdv" in text


def test_service_uses_all_factors():
    text = (ROOT_DIR / "src/services/expansao_service.py").read_text(encoding="utf-8")
    for col in [
        "fator_pib",
        "fator_pop_30_44",
        "fator_masculino",
        "fator_feminino",
        "fator_restaurantes",
        "fator_pop_15_29",
        "fator_pdv_total",
    ]:
        assert col in text


def test_doc_exists():
    assert (ROOT_DIR / "docs/HOTFIX_IDC_SIMULADOR_PESOS_100.md").exists()

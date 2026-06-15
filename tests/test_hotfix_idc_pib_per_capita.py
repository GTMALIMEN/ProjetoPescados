
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_app_uses_pib_per_capita_instead_faixa_etaria():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert "idc_w_pib_per_capita" in text
    assert "Peso PIB per capita" in text
    assert "idc_w_idade" not in text
    assert "Peso faixa etária" not in text


def test_service_uses_pib_per_capita_factor():
    text = (ROOT_DIR / "src/services/expansao_service.py").read_text(encoding="utf-8")
    assert "peso_pib_per_capita" in text
    assert "fator_pib_per_capita" in text
    assert "peso_faixa_etaria" not in text
    assert "fator_faixa_etaria" not in text


def test_doc_exists():
    assert (ROOT_DIR / "docs/HOTFIX_IDC_PIB_PER_CAPITA.md").exists()

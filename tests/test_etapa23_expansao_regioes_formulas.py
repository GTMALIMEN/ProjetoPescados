
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_service_regioes_economicas_exists():
    text = (ROOT_DIR / "src/services/expansao_service.py").read_text(encoding="utf-8")
    assert "carregar_regioes_economicas_expansao" in text
    assert "carregar_municipios_regiao_economica_expansao" in text
    assert "regiao_economica" in text


def test_app_has_estado_e_regiao_selector():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert "Estado base" in text
    assert "Região econômica/comercial" in text
    assert "Municípios da região selecionada" in text


def test_formula_doc_exists():
    assert (ROOT_DIR / "docs/FORMULAS_E_ONDE_SAO_APLICADAS.md").exists()
    content = (ROOT_DIR / "docs/FORMULAS_E_ONDE_SAO_APLICADAS.md").read_text(encoding="utf-8")
    assert "IDC base" in content
    assert "Margin Pool" in content
    assert "Onde é aplicada" in content

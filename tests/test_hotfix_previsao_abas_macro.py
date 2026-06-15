
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

def test_previsao_abas_macro():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert "Cotação Dólar" in text
    assert "IPCA" in text
    assert "IPCA Alimentar" in text
    assert "Previsão Mercado" in text
    assert "tab_dolar, tab_ipca, tab_ipca_alim, tab_mercado" in text

def test_doc_exists():
    assert (ROOT_DIR / "docs/HOTFIX_PREVISAO_ABAS_MACRO.md").exists()

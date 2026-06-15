
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_layout_has_period_filter():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert "Filtro de período" in text
    assert "_filter_df_by_period" in text
    assert "Dólar / Câmbio" in text


def test_tabs_consolidated():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert '"🧭 Região Comercial MG"' not in text
    assert '"🥩 Proteínas e Grãos"' not in text
    assert "aba_regiao = aba_expansao" in text
    assert "aba_setorial = aba_previsao" in text


def test_doc_exists():
    assert (ROOT_DIR / "docs/HOTFIX_LAYOUT_V21_FILTROS_CONSOLIDACAO.md").exists()

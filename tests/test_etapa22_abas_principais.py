
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_duas_abas_principais_no_app():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert "area_expansao, area_previsao = st.tabs" in text
    assert "🌎 Análise de Expansão" in text
    assert "📈 Análise Previsão de Mercado" in text


def test_ordem_interna_expansao():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert "📈 Radar Econômico" in text
    assert "🗺️ Geografia IBGE" in text
    assert "🧭 Região Comercial MG" in text
    assert "🧪 What-if" in text


def test_doc_etapa22_existe():
    assert (ROOT_DIR / "docs/ETAPA22_ABAS_PRINCIPAIS.md").exists()


from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_requirements_has_lxml():
    req = (ROOT_DIR / "requirements.txt").read_text(encoding="utf-8")
    assert "lxml" in req
    assert "html5lib" in req


def test_ceagesp_collector_uses_stringio_and_handles_import_error():
    text = (ROOT_DIR / "src/collectors/ceagesp_collector.py").read_text(encoding="utf-8")
    assert "StringIO" in text
    assert "except ImportError" in text
    assert "pd.read_html(StringIO(response.text))" in text


def test_arrow_numeric_cast_exists():
    text = (ROOT_DIR / "src/services/previsao_mercado_service.py").read_text(encoding="utf-8")
    assert 'astype("float64")' in text
    assert "variacao_mensal_pct" in text

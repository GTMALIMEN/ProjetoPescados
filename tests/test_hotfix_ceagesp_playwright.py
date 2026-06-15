
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_playwright_collector_exists():
    text = (ROOT_DIR / "src/collectors/ceagesp_playwright_collector.py").read_text(encoding="utf-8")
    assert "playwright" in text.lower()
    assert "cot_grupo" in text
    assert "cot_data" in text


def test_run_script_exists():
    assert (ROOT_DIR / "scripts/run_ceagesp_playwright.py").exists()
    assert (ROOT_DIR / "scripts/instalar_playwright_ceagesp.bat").exists()


def test_doc_exists():
    assert (ROOT_DIR / "docs/HOTFIX_CEAGESP_PLAYWRIGHT.md").exists()

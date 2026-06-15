
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_idh_alias_script_exists():
    text = (ROOT_DIR / "scripts/corrigir_idh_aliases.py").read_text(encoding="utf-8")
    assert "Embu das Artes" in text
    assert "São Luiz do Paraitinga" in text
    assert "Brazópolis" in text


def test_ceagesp_collector_has_limits():
    text = (ROOT_DIR / "src/collectors/ceagesp_collector.py").read_text(encoding="utf-8")
    assert "max_tentativas" in text
    assert "timeout" in text
    assert "RequestException" in text


def test_doc_exists():
    assert (ROOT_DIR / "docs/HOTFIX_IDH_ALIAS_CEAGESP_FAST.md").exists()

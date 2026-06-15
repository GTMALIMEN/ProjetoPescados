
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_idh_fallback_script_has_8_values():
    text = (ROOT_DIR / "scripts/preencher_idh_faltantes_ibge.py").read_text(encoding="utf-8")
    assert "Barão do Monte Alto" in text
    assert "Brazópolis" in text
    assert "Embu das Artes" in text
    assert "São Luiz do Paraitinga" in text
    assert "0.697" in text


def test_ceagesp_uses_real_form_fields():
    text = (ROOT_DIR / "src/collectors/ceagesp_collector.py").read_text(encoding="utf-8")
    assert "cot_grupo" in text
    assert "cot_data" in text
    assert "PESCADOS" in text


def test_doc_exists():
    assert (ROOT_DIR / "docs/HOTFIX_IDH_IBGE_CEAGESP_FORM.md").exists()

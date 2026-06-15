
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_ceagesp_manual_files_exist():
    required = [
        "src/database/ceagesp_manual.sql",
        "scripts/apply_ceagesp_manual.py",
        "scripts/criar_template_ceagesp_manual.py",
        "scripts/load_ceagesp_manual_file.py",
        "docs/CEAGESP_MANUAL.md",
    ]
    for file in required:
        assert (ROOT_DIR / file).exists(), f"Arquivo ausente: {file}"


def test_loader_has_required_columns():
    text = (ROOT_DIR / "scripts/load_ceagesp_manual_file.py").read_text(encoding="utf-8")
    assert "data_referencia" in text
    assert "produto" in text
    assert "preco_comum" in text
    assert "ON CONFLICT" in text


def test_diagnostic_manual_label():
    text = (ROOT_DIR / "src/database/ceagesp_manual.sql").read_text(encoding="utf-8")
    assert "ceagesp_pescados_manual" in text
    assert "PENDENTE_IMPORTACAO_MANUAL" in text

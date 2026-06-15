
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_files_exist():
    required = [
        "src/database/hotfix_expansao_receita_manual_cepea.sql",
        "scripts/apply_hotfix_expansao_receita_cepea.py",
        "scripts/load_receita_manual_expansao_file.py",
        "scripts/criar_template_receita_manual_expansao.py",
        "docs/HOTFIX_EXPANSAO_RECEITA_IDC_CEPEA.md",
    ]
    for rel in required:
        assert (ROOT_DIR / rel).exists(), rel


def test_app_has_cepea_ceagesp():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert "Comparação CEPEA x CEAGESP" in text
    assert "carregar_comparacao_cepea_ceagesp" in text
    assert "carregar_cepea_series" in text


def test_expansao_service_has_receita_manual_and_idc():
    text = (ROOT_DIR / "src/services/expansao_service.py").read_text(encoding="utf-8")
    assert "fato_receita_manual_expansao" in text
    assert "idc_macro" in text
    assert "IDC estratégico" in text or "idc_base" in text
    assert "receita_media_12m" in text

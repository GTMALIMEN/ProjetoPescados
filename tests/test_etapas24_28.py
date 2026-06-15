
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_files_etapas24_28_exist():
    required = [
        "src/database/etapas24_28.sql",
        "scripts/apply_etapas24_28.py",
        "scripts/run_censo_demografico_2022.py",
        "scripts/run_pdv_proxy.py",
        "scripts/run_comex_refinado.py",
        "scripts/criar_templates_etapas27_28.py",
        "scripts/rodar_etapas24_28.bat",
        "docs/ETAPAS24_28_IMPLEMENTACAO.md",
    ]
    for rel in required:
        assert (ROOT_DIR / rel).exists(), rel


def test_diagnostic_items_present():
    text = (ROOT_DIR / "src/database/etapas24_28.sql").read_text(encoding="utf-8")
    assert "expansao_demografia_censo" in text
    assert "expansao_renda_censo" in text
    assert "expansao_pdv" in text
    assert "comex_stat_refinado" in text
    assert "base_compra_manual" in text
    assert "previa_vendedores" in text


def test_app_comex_logs_separated():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert "Últimas cargas com sucesso" in text
    assert "Últimos erros" in text
    assert "carregar_comex_status_atual" in text

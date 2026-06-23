from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_cepea_ceagesp_automatic_files_removed():
    removed = [
        "scripts/run_cepea_oficial.py",
        "scripts/load_cepea_file.py",
        "scripts/run_ceagesp_automatico.py",
        "scripts/run_ceagesp_playwright.py",
        "scripts/run_ceagesp_pescados.py",
        "src/collectors/cepea_collector.py",
        "src/collectors/ceagesp_collector.py",
        "src/collectors/ceagesp_playwright_collector.py",
    ]
    for rel in removed:
        assert not (ROOT_DIR / rel).exists(), f"Arquivo antigo deve permanecer removido: {rel}"


def test_app_uses_only_manual_price_sources():
    app = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert '["CEPEA Manual", "CEAGESP Manual"]' in app
    assert "carregar_cepea_manual_series" in app
    assert "run_cepea_oficial" not in app
    assert "run_ceagesp_playwright" not in app
    assert "run_ceagesp_automatico" not in app


def test_previsao_service_manual_aliases_only():
    text = (ROOT_DIR / "src/services/previsao_mercado_service.py").read_text(encoding="utf-8")
    assert "return carregar_cepea_manual_series" in text
    assert "app.vw_cepea_tilapia_manual_historico" in text
    assert "CEPEA_MANUAL_IMPORTADO" in text  # citado apenas para negar leitura desse legado
    assert "oficial_site_produtor_independente" not in text


def test_importer_substituir_tudo_cleans_legacy_dw():
    text = (ROOT_DIR / "src/services/importacoes_manuais_service.py").read_text(encoding="utf-8")
    assert "fonte ILIKE '%CEPEA%'" in text
    assert "fonte ILIKE '%CEAGESP%'" in text
    assert 'df["fonte"] = "CEAGESP Manual"' in text

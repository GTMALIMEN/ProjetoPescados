
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_idh_collector_has_dadosgov_api_and_undp_headers():
    text = (ROOT_DIR / "src/collectors/atlas_brasil_collector.py").read_text(encoding="utf-8")
    assert "dados/api/publico/conjuntos-dados" in text
    assert "Mozilla/5.0" in text
    assert "undp_url" in text


def test_idh_etl_join_by_municipio_uf():
    text = (ROOT_DIR / "src/etl/load_idh_automatico.py").read_text(encoding="utf-8")
    assert "municipio_norm" in text
    assert "uf_norm" in text
    assert "dw.dim_geografia" in text


def test_doc_exists():
    assert (ROOT_DIR / "docs/HOTFIX_IDH_AUTOMATICO_API_JOIN.md").exists()

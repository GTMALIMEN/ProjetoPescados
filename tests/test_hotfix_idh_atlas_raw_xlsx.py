
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_atlas_raw_xlsx_url_present():
    text = (ROOT_DIR / "src/collectors/atlas_brasil_collector.py").read_text(encoding="utf-8")
    assert "atlas2013_dadosbrutos_pt.xlsx" in text
    assert "MUN 91-00-10" in text
    assert "IDHM_L" in text
    assert "IDHM_R" in text


def test_year_2010_filter_present():
    text = (ROOT_DIR / "src/collectors/atlas_brasil_collector.py").read_text(encoding="utf-8")
    assert "anos == 2010" in text


def test_doc_exists():
    assert (ROOT_DIR / "docs/HOTFIX_IDH_ATLAS_RAW_XLSX.md").exists()

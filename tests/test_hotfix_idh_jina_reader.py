
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_jina_reader_url_present():
    text = (ROOT_DIR / "src/collectors/atlas_brasil_collector.py").read_text(encoding="utf-8")
    assert "https://r.jina.ai/https://www.undp.org/pt/brazil/idhm-municipios-2010" in text
    assert "_parse_markdown_or_text_idhm" in text


def test_doc_exists():
    assert (ROOT_DIR / "docs/HOTFIX_IDH_JINA_READER.md").exists()

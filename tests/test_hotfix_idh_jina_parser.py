from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_parser_accepts_optional_rank_and_dot_or_comma():
    text = (ROOT_DIR / "src/collectors/atlas_brasil_collector.py").read_text(encoding="utf-8")
    assert "number_tokens" in text
    assert "[01][\\.,]\\d{3}" in text
    assert "debug_file" in text


def test_debug_script_exists():
    assert (ROOT_DIR / "scripts/debug_idh_jina.py").exists()

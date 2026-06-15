
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

def test_estado_todos_no_selectbox():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert '["Todos", "MG", "SP", "RJ", "ES"]' in text
    assert 'estado_base == "Todos"' in text

def test_doc_hotfix_existe():
    assert (ROOT_DIR / "docs/HOTFIX_ESTADO_TODOS_EXPANSAO.md").exists()

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

def test_selectbox_tem_todos():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert '["Todos", "MG", "SP", "RJ", "ES"]' in text
    assert 'estado_base == "Todos"' in text

def test_hotfix_direto_existe():
    assert (ROOT_DIR / "scripts/hotfix_expansao_estado_todos.py").exists()


from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

def test_previsao_usa_base_comparacao():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert "Base de comparação" in text
    assert '["CEPEA Manual", "CEAGESP Manual"]' in text
    assert "tab_comparacao_fontes" not in text
    assert "Comparação CEPEA x CEAGESP" not in text

def test_expansao_abas_limpas():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert "Mapa e regiões" in text
    assert "Perfil demográfico" in text
    assert "Receita por categoria" in text
    assert "IDC / Margin Pool" in text
    assert "Simulador IDC" in text
    assert 'st.tabs(["Microrregiões"' not in text


from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_v2_plano_files_exist():
    required = [
        "src/database/expansao_v2_publica.sql",
        "src/etl/load_expansao_publica.py",
        "src/collectors/ceagesp_collector.py",
        "scripts/apply_expansao_v2_publica.py",
        "scripts/run_expansao_publica.py",
        "scripts/run_ceagesp_pescados.py",
        "scripts/diagnosticar_v2_plano.py",
        "docs/AJUSTE_PLANO_V2_DADOS_PUBLICOS.md",
    ]
    for file in required:
        assert (ROOT_DIR / file).exists(), f"Arquivo ausente: {file}"


def test_app_tabs_aligned():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert "🌎 Análise de Expansão" in text
    assert "📈 Análise Previsão de Mercado" in text
    assert "⚙️ Pipeline" not in text
    assert "📚 Projeto" not in text


from pathlib import Path
import re

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_app_has_final_plan_tabs_only():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    for tab in [
        "📈 Radar Econômico",
        "🗺️ Geografia IBGE",
        "🧭 Região Comercial MG",
        "🌎 Análise de Expansão",
        "🥩 Proteínas e Grãos",
        "🔌 Fontes Reais",
        "📈 Análise Previsão de Mercado",
        "🧪 What-if",
        "🚨 Alertas Ativos",
        "📄 Relatório Executivo",
        "🩺 Saúde do Sistema",
    ]:
        assert tab in text

    assert "⚙️ Pipeline" not in text
    assert "📚 Projeto" not in text
    assert "💰 Vendas Internas" not in text
    assert "⭐ Scores Iniciais" not in text


def test_app_whatif_uses_real_param_names():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert "variacao_dolar_pct" in text
    assert "dolar_delta_pct" not in text


def test_ceagesp_sql_uses_chave_registro():
    sql = (ROOT_DIR / "src/database/expansao_v2_publica.sql").read_text(encoding="utf-8")
    assert "chave_registro TEXT UNIQUE" in sql
    assert "COALESCE(classificacao" not in sql


def test_docs_exist():
    assert (ROOT_DIR / "docs/HOTFIX_V2_100_ALINHADO.md").exists()

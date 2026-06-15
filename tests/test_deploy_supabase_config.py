
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

def test_settings_accepts_database_url():
    text = (ROOT_DIR / "src/config/settings.py").read_text(encoding="utf-8")
    assert "DATABASE_URL" in text
    assert "_normalize_database_url" in text
    assert "database_url_env" in text

def test_connection_disables_prepared_statements():
    text = (ROOT_DIR / "src/database/connection.py").read_text(encoding="utf-8")
    assert "prepare_threshold" in text
    assert "pool_pre_ping" in text

def test_supabase_docs_and_scripts_exist():
    assert (ROOT_DIR / "docs/DEPLOY_STREAMLIT_SUPABASE.md").exists()
    assert (ROOT_DIR / "scripts/test_supabase_connection.py").exists()
    assert (ROOT_DIR / ".streamlit/secrets.toml.example").exists()

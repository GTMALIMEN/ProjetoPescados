
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_preflight_files_exist():
    assert (ROOT_DIR / "src/database/preflight_drop_conflicting_views.sql").exists()
    assert (ROOT_DIR / "scripts/preflight_drop_conflicting_views.py").exists()


def test_setorial_drops_conflicting_view():
    text = (ROOT_DIR / "src/database/setorial.sql").read_text(encoding="utf-8")
    assert "DROP VIEW IF EXISTS app.vw_indicador_setorial_mensal CASCADE" in text
    assert "DROP VIEW IF EXISTS app.vw_saude_setorial CASCADE" in text


def test_init_db_calls_preflight():
    text = (ROOT_DIR / "scripts/init_db.py").read_text(encoding="utf-8")
    assert "aplicar_preflight_views" in text
    assert "preflight_drop_conflicting_views.sql" in text

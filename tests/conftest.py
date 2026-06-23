import importlib.util
import pytest

_DB_TEST_FILES = {
    "test_database_connection.py",
    "test_database_tables.py",
    "test_database_views.py",
    "test_pipeline_metadata.py",
    "test_score_weights.py",
}


def pytest_collection_modifyitems(config, items):
    if importlib.util.find_spec("psycopg") is not None:
        return
    skip_db = pytest.mark.skip(reason="psycopg não instalado neste ambiente de teste; rode localmente com requirements.txt para validar banco.")
    for item in items:
        if item.path.name in _DB_TEST_FILES or "db" in item.keywords:
            item.add_marker(skip_db)

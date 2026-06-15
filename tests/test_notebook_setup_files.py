from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_notebook_setup_files_exist():
    required = [
        "scripts/create_database.py",
        "scripts/setup_notebook.bat",
        "scripts/primeiro_uso_notebook.bat",
        "docs/INSTALACAO_NOTEBOOK_POSTGRES.md",
        "LEIA_PRIMEIRO_NOTEBOOK.md",
    ]

    for file in required:
        assert (ROOT_DIR / file).exists(), f"Arquivo ausente: {file}"

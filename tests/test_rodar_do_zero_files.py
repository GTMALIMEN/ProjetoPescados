from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_rodar_do_zero_files_exist():
    required = [
        "RODAR_DO_ZERO.md",
        "scripts/setup_do_zero.bat",
        "scripts/primeira_execucao_do_zero.bat",
        "scripts/abrir_app.bat",
        "scripts/criar_env_local.bat",
        "scripts/create_database.py",
        ".env.example",
    ]

    for file in required:
        assert (ROOT_DIR / file).exists(), f"Arquivo ausente: {file}"

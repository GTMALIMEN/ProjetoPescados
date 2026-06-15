from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_python312_setup_files_exist():
    required = [
        ".env.example",
        "env.example.txt",
        "scripts/recriar_venv_python312.bat",
        "scripts/setup_do_zero.bat",
        "RODAR_DO_ZERO.md",
    ]

    for file in required:
        assert (ROOT_DIR / file).exists(), f"Arquivo ausente: {file}"


def test_rodar_do_zero_mentions_python312():
    text = (ROOT_DIR / "RODAR_DO_ZERO.md").read_text(encoding="utf-8")
    assert "Python 3.12" in text
    assert "Python 3.14" in text

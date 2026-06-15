from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_required_directories_exist():
    required_dirs = [
        "src",
        "scripts",
        "docs",
        "data",
        "config",
    ]

    for directory in required_dirs:
        assert (ROOT_DIR / directory).exists(), f"Diretório ausente: {directory}"


def test_required_files_exist():
    required_files = [
        "README.md",
        ".env.example",
        "app.py",
        "scripts/init_db.py",
        "scripts/run_pipeline_full.py",
        "scripts/check_db.py",
        "src/database/create_schemas.sql",
        "src/database/models.sql",
        "src/database/etapa16_pipeline.sql",
        "src/services/pipeline_service.py",
        "docs/ARQUITETURA.md",
        "docs/GUIA_EXECUCAO.md",
        "docs/DICIONARIO_DADOS.md",
        "docs/PORTFOLIO.md",
        "docs/TROUBLESHOOTING.md",
    ]

    for file in required_files:
        assert (ROOT_DIR / file).exists(), f"Arquivo ausente: {file}"


def test_readme_has_key_sections():
    readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")

    expected_sections = [
        "Objetivo do projeto",
        "Stack utilizada",
        "Arquitetura resumida",
        "Como rodar o projeto",
        "Pipeline principal",
    ]

    for section in expected_sections:
        assert section in readme, f"Seção ausente no README: {section}"

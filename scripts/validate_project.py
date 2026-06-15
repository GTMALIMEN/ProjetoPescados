from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
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
    "docs/TESTES.md",
    "pytest.ini",
    "scripts/run_tests.py",
    "scripts/run_tests_no_db.py",
    "docs/ETAPA22_ABAS_PRINCIPAIS.md",
    "tests/test_project_structure.py",
    "docs/HOTFIX_INIT_DB_VIEWS_CONFLITANTES.md",
    "scripts/preflight_drop_conflicting_views.py",
    "src/database/preflight_drop_conflicting_views.sql",
    "docs/RODAR_TUDO_ETAPA23.md",
    "scripts/abrir_app_etapa23.bat",
    "scripts/rodar_tudo_etapa23.bat",
    "scripts/validar_etapa23_integridade.py",
    "docs/ETAPA23_EXPANSAO_REGIOES_E_FORMULAS.md",
    "docs/FORMULAS_E_ONDE_SAO_APLICADAS.md",
    "docs/CEAGESP_MANUAL.md",
    "scripts/criar_template_ceagesp_manual.py",
    "scripts/apply_ceagesp_manual.py",
    "src/database/ceagesp_manual.sql",
    "docs/HOTFIX_CEAGESP_PLAYWRIGHT.md",
    "scripts/instalar_playwright_ceagesp.bat",
    "scripts/run_ceagesp_playwright.py",
    "src/collectors/ceagesp_playwright_collector.py",
    "docs/HOTFIX_IDH_IBGE_CEAGESP_FORM.md",
    "scripts/preencher_idh_faltantes_ibge.py",
    "docs/HOTFIX_IDH_ALIAS_CEAGESP_FAST.md",
    "scripts/corrigir_idh_aliases.py",
    "docs/HOTFIX_IDH_JINA_PARSER.md",
    "scripts/debug_idh_jina.py",
    "docs/HOTFIX_IDH_ATLAS_RAW_XLSX.md",
    "docs/HOTFIX_IDH_AUTOMATICO_API_JOIN.md",
    "docs/FONTES_AUTOMATICAS_IDH_CEAGESP.md",
    "scripts/rodar_fontes_automaticas.bat",
    "scripts/run_ceagesp_automatico.py",
    "scripts/run_idh_automatico.py",
    "scripts/apply_fontes_automaticas.py",
    "src/etl/load_idh_automatico.py",
    "src/collectors/atlas_brasil_collector.py",
    "src/database/fontes_automaticas_idh_ceagesp.sql",
    "docs/IMPORTADORES_MANUAIS_E_IDH.md",
    "scripts/rodar_importadores_manuais_exemplo.bat",
    "scripts/criar_templates_importacao.py",
    "scripts/load_idh_file.py",
    "scripts/load_previa_vendedores_file.py",
    "scripts/load_compra_manual_file.py",
    "scripts/load_ceagesp_manual_file.py",
    "src/etl/load_importadores_manuais.py",
    "src/database/importadores_manuais_v2.sql",
    "docs/HOTFIX_CEAGESP_ARROW.md",
    "scripts/instalar_dependencias_ceagesp.bat",
    "docs/HOTFIX_V2_100_ALINHADO.md",
    "docs/AJUSTE_PLANO_V2_DADOS_PUBLICOS.md",
    "scripts/diagnosticar_v2_plano.py",
    "scripts/run_ceagesp_pescados.py",
    "scripts/run_expansao_publica.py",
    "scripts/apply_expansao_v2_publica.py",
    "src/collectors/ceagesp_collector.py",
    "src/etl/load_expansao_publica.py",
    "src/database/expansao_v2_publica.sql",
    "scripts/recriar_venv_python312.bat",
    "env.example.txt",
    "scripts/criar_env_local.bat",
    "scripts/abrir_app.bat",
    "scripts/primeira_execucao_do_zero.bat",
    "scripts/setup_do_zero.bat",
    "RODAR_DO_ZERO.md",
    "README_V2_EXPANSAO_PREVISAO.md",
    "docs/ETAPA22_V2_ABAS_EXPANSAO_PREVISAO.md",
    "src/services/previsao_mercado_service.py",
    "src/services/expansao_service.py",
    "docs/ETAPA21_MAPAS_GEOGRAFICOS.md",
    "scripts/atualizar_mapas_ibge.bat",
    "scripts/baixar_malhas_ibge.py",
    "src/services/mapas_service.py",
    "docs/HOTFIX_FONTES_2020_2026.md",
    "scripts/diagnosticar_fontes_setoriais.py",
    "scripts/recarregar_fontes_2020_2026.bat",
    "LEIA_PRIMEIRO_NOTEBOOK.md",
    "docs/INSTALACAO_NOTEBOOK_POSTGRES.md",
    "scripts/primeiro_uso_notebook.bat",
    "scripts/setup_notebook.bat",
    "scripts/create_database.py",
]

REQUIRED_DIRS = [
    "src",
    "scripts",
    "docs",
    "data",
    "config",
    "tests",
]


def main():
    ok = True

    print("Validando estrutura do projeto...\n")

    for d in REQUIRED_DIRS:
        path = ROOT_DIR / d
        exists = path.exists() and path.is_dir()
        print(f"{'OK' if exists else 'ERRO'} DIR  {d}")
        ok = ok and exists

    print("")

    for f in REQUIRED_FILES:
        path = ROOT_DIR / f
        exists = path.exists() and path.is_file()
        print(f"{'OK' if exists else 'ERRO'} FILE {f}")
        ok = ok and exists

    print("")

    if ok:
        print("✅ Projeto validado com sucesso.")
        sys.exit(0)

    print("❌ Existem arquivos/pastas obrigatórios ausentes.")
    sys.exit(1)


if __name__ == "__main__":
    main()

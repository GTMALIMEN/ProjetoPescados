from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_importadores_files_exist():
    required = [
        'src/database/importadores_manuais_v2.sql',
        'src/etl/load_importadores_manuais.py',
        'scripts/load_ceagesp_manual_file.py',
        'scripts/load_compra_manual_file.py',
        'scripts/load_previa_vendedores_file.py',
        'scripts/load_idh_file.py',
        'scripts/criar_templates_importacao.py',
        'docs/IMPORTADORES_MANUAIS_E_IDH.md',
    ]
    for file in required:
        assert (ROOT_DIR / file).exists(), f'Arquivo ausente: {file}'


def test_sql_has_manual_log():
    sql = (ROOT_DIR / 'src/database/importadores_manuais_v2.sql').read_text(encoding='utf-8')
    assert 'app.importacao_manual_log' in sql
    assert 'app.vw_importacao_manual_resumo' in sql

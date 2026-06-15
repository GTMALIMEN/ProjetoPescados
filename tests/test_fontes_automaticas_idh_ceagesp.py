from pathlib import Path
ROOT_DIR=Path(__file__).resolve().parents[1]
def test_auto_sources_files_exist():
    for f in ['src/database/fontes_automaticas_idh_ceagesp.sql','src/collectors/atlas_brasil_collector.py','src/collectors/ceagesp_collector.py','src/etl/load_idh_automatico.py','scripts/apply_fontes_automaticas.py','scripts/run_idh_automatico.py','scripts/run_ceagesp_automatico.py','scripts/rodar_fontes_automaticas.bat','docs/FONTES_AUTOMATICAS_IDH_CEAGESP.md']:
        assert (ROOT_DIR/f).exists(), f
def test_idh_ceagesp_are_automatic():
    text=(ROOT_DIR/'docs/FONTES_AUTOMATICAS_IDH_CEAGESP.md').read_text(encoding='utf-8')
    assert 'deixam de ser importadores manuais' in text
    assert 'run_idh_automatico.py' in text
    assert 'run_ceagesp_automatico.py' in text

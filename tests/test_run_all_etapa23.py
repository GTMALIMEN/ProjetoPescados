
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_run_all_scripts_exist():
    assert (ROOT_DIR / "scripts/rodar_tudo_etapa23.bat").exists()
    assert (ROOT_DIR / "scripts/abrir_app_etapa23.bat").exists()
    assert (ROOT_DIR / "scripts/validar_etapa23_integridade.py").exists()


def test_run_all_has_main_steps():
    text = (ROOT_DIR / "scripts/rodar_tudo_etapa23.bat").read_text(encoding="utf-8")
    assert "run_expansao_publica.py --estados MG,SP,RJ,ES" in text
    assert "run_idh_automatico.py" in text
    assert "preencher_idh_faltantes_ibge.py" in text
    assert "diagnosticar_v2_plano.py" in text


def test_app_no_duplicate_region_merge_block():
    text = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert "df_micro = df_micro.merge" not in text

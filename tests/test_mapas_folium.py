from src.services.mapas_service import normalizar_codarea, UF_TO_CODIGO, REGIAO_CORES

def test_normalizar_codarea_folium():
    assert normalizar_codarea('3106200.0') == '3106200'
    assert normalizar_codarea('MG-3106200') == '3106200'
    assert normalizar_codarea(31) == '31'

def test_mg_codigo_uf():
    assert UF_TO_CODIGO['MG'] == '31'

def test_regiao_cores_tem_sem_regiao():
    assert 'Sem região' in REGIAO_CORES

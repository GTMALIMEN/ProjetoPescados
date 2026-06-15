
from src.services.mapas_service import normalizar_codarea, UF_TO_CODIGO


def test_normalizar_codarea():
    assert normalizar_codarea("3106200.0") == "3106200"
    assert normalizar_codarea(31) == "31"
    assert normalizar_codarea("MG-3106200") == "3106200"


def test_uf_to_codigo_mg():
    assert UF_TO_CODIGO["MG"] == "31"

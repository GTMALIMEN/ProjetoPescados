
from src.services.mapas_service import UF_TO_CODIGO, normalizar_codarea


def test_uf_to_codigo_contains_mg_sp_rj():
    assert UF_TO_CODIGO["MG"] == "31"
    assert UF_TO_CODIGO["SP"] == "35"
    assert UF_TO_CODIGO["RJ"] == "33"


def test_normalizar_codarea():
    assert normalizar_codarea("3106200.0") == "3106200"
    assert normalizar_codarea(31) == "31"
    assert normalizar_codarea(None) == ""

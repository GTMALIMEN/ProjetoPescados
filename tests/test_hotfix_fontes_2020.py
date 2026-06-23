from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_legacy_proxy_input_files_not_required_in_manual_mode():
    """Modo manual controlado não deve depender das bases proxy antigas.

    Os arquivos antigos de CEPEA/CONAB em data/input eram usados como fontes
    expandidas/proxy. Agora os modelos oficiais ficam em modelos_importacao e
    data/input deve receber somente arquivos reais enviados pelo usuário.
    """
    assert not (ROOT_DIR / "data/input/cepea_tilapia.xlsx").exists()
    assert not (ROOT_DIR / "data/input/conab_precos_milho_soja.xlsx").exists()


def test_manual_blank_models_exist():
    for name in [
        "modelo_cepea_manual.xlsx",
        "modelo_ceagesp_pescados.xlsx",
        "modelo_receita_vendas_expansao.xlsx",
        "modelo_scanntech_mercado_privado.xlsx",
        "modelo_curva_mercado_categoria.xlsx",
        "modelo_key_account_lojas.xlsx",
        "modelo_compra_manual.xlsx",
        "modelo_previa_vendedores.xlsx",
    ]:
        assert (ROOT_DIR / "modelos_importacao" / name).exists()

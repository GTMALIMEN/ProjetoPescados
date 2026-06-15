from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_expanded_protein_file_has_2020_2026_and_multiple_products():
    path = ROOT_DIR / "data/input/cepea_tilapia.xlsx"
    assert path.exists()

    df = pd.read_excel(path)
    assert pd.to_datetime(df["data"]).min().year <= 2020
    assert pd.to_datetime(df["data"]).max().year >= 2026
    assert df["produto"].nunique() >= 6


def test_expanded_grains_file_has_2020_2026_and_multiple_products():
    path = ROOT_DIR / "data/input/conab_precos_milho_soja.xlsx"
    assert path.exists()

    df = pd.read_excel(path)
    assert pd.to_datetime(df["data"]).min().year <= 2020
    assert pd.to_datetime(df["data"]).max().year >= 2026
    assert df["produto"].nunique() >= 5

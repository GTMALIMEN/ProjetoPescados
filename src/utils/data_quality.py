import pandas as pd


def validar_colunas_obrigatorias(df: pd.DataFrame, colunas: list[str]) -> list[str]:
    erros = []
    for coluna in colunas:
        if coluna not in df.columns:
            erros.append(f"Coluna obrigatória ausente: {coluna}")
    return erros


def validar_dataframe_nao_vazio(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["DataFrame vazio"]
    return []


def validar_valor_numerico(df: pd.DataFrame, coluna: str) -> list[str]:
    erros = []
    if coluna in df.columns:
        valores_invalidos = pd.to_numeric(df[coluna], errors="coerce").isna().sum()
        if valores_invalidos > 0:
            erros.append(f"Coluna {coluna} possui {valores_invalidos} valores não numéricos")
    return erros

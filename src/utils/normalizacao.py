import pandas as pd


def normalizar_percentil(
    serie: pd.Series,
    p_low: float = 0.05,
    p_high: float = 0.95,
) -> pd.Series:
    if serie.empty:
        return serie

    p5 = serie.quantile(p_low)
    p95 = serie.quantile(p_high)

    if p95 == p5:
        return pd.Series([50] * len(serie), index=serie.index)

    norm = ((serie - p5) / (p95 - p5)) * 100
    return norm.clip(lower=0, upper=100)

from pathlib import Path

p = Path("src/services/executive_report_service.py")
txt = p.read_text(encoding="utf-8")

if "def clean_date_or_none" not in txt:
    marker = """def safe_float(value, default=0.0):
    if value is None or pd.isna(value):
        return default
    return float(value)
"""
    helper = """def safe_float(value, default=0.0):
    if value is None or pd.isna(value):
        return default
    return float(value)


def clean_date_or_none(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    s = str(value).strip()
    if s.lower() in {"", "none", "nan", "nat", "null"}:
        return None

    # mantém YYYY-MM-DD quando vier timestamp
    return s[:10]
"""
    txt = txt.replace(marker, helper)

txt = txt.replace(
    '"periodo_inicio": parametros.get("periodo_inicio"),',
    '"periodo_inicio": clean_date_or_none(parametros.get("periodo_inicio")),'
)

txt = txt.replace(
    '"periodo_fim": parametros.get("periodo_fim"),',
    '"periodo_fim": clean_date_or_none(parametros.get("periodo_fim")),'
)

txt = txt.replace(
    '"periodo_inicio": str(vendas.get("primeira_data")) if hasattr(vendas, "get") else None,',
    '"periodo_inicio": clean_date_or_none(vendas.get("primeira_data") if hasattr(vendas, "get") else None),'
)

txt = txt.replace(
    '"periodo_fim": str(vendas.get("ultima_data")) if hasattr(vendas, "get") else None,',
    '"periodo_fim": clean_date_or_none(vendas.get("ultima_data") if hasattr(vendas, "get") else None),'
)

p.write_text(txt, encoding="utf-8")
print("✅ Hotfix aplicado em executive_report_service.py")

from pathlib import Path

path = Path("src/services/expansao_service.py")
txt = path.read_text(encoding="utf-8")

old = '''df["over_under_share_pct"] = df["participacao_receita_pct"] - pd.to_numeric(df["idc_base"], errors="coerce").fillna(0)'''

new = '''# Compatibilidade IDC:
# A view nova usa idc_planejado/idc/idc_final/score_idc.
# O código antigo ainda esperava idc_base.
if "idc_base" not in df.columns:
    for col_idc in ["idc_planejado", "idc_final", "idc", "score_idc", "score"]:
        if col_idc in df.columns:
            df["idc_base"] = pd.to_numeric(df[col_idc], errors="coerce").fillna(0)
            break
    else:
        df["idc_base"] = 0

if "participacao_receita_pct" not in df.columns:
    df["participacao_receita_pct"] = 0

df["over_under_share_pct"] = (
    pd.to_numeric(df["participacao_receita_pct"], errors="coerce").fillna(0)
    - pd.to_numeric(df["idc_base"], errors="coerce").fillna(0)
)'''

if old not in txt:
    print("⚠️ Linha exata não encontrada. Tentando correção alternativa...")

    marker = 'df["over_under_share_pct"]'
    pos = txt.find(marker)

    if pos == -1:
        raise RuntimeError("Não encontrei o trecho over_under_share_pct em expansao_service.py")

    start = txt.rfind("\n", 0, pos) + 1
    end = txt.find("\n", pos)

    txt = txt[:start] + new + txt[end:]
else:
    txt = txt.replace(old, new)

path.write_text(txt, encoding="utf-8")
print("✅ expansao_service.py corrigido: idc_base agora usa idc_planejado/idc como fallback.")

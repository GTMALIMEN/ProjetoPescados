from pathlib import Path
import py_compile

# ============================================================
# 1) Corrigir src/services/expansao_service.py
# ============================================================

service_path = Path("src/services/expansao_service.py")
txt = service_path.read_text(encoding="utf-8")

compat = """
# Compatibilidade classificação:
# A view nova usa classificacao_score; telas antigas esperam classificacao.
if "classificacao" not in df.columns:
    if "classificacao_score" in df.columns:
        df["classificacao"] = df["classificacao_score"]
    elif "score" in df.columns:
        score_tmp = pd.to_numeric(df["score"], errors="coerce").fillna(0)
        df["classificacao"] = pd.cut(
            score_tmp,
            bins=[-1, 35, 55, 75, 101],
            labels=["Monitorar", "Baixa", "Média", "Alta"]
        ).astype(str)
    else:
        df["classificacao"] = "Monitorar"

if "classificacao_score" not in df.columns:
    df["classificacao_score"] = df["classificacao"]
"""

if "Compatibilidade classificação:" not in txt:
    # Procura o ponto mais seguro dentro de calcular_idc_expansao: antes do return df
    pos = txt.find('df["receita_esperada_idc"]')
    if pos == -1:
        pos = txt.find('df["over_under_share_pct"]')
    if pos == -1:
        raise RuntimeError("Não encontrei ponto de cálculo IDC em expansao_service.py")

    return_pos = txt.find("return df", pos)
    if return_pos == -1:
        raise RuntimeError("Não encontrei return df depois do cálculo IDC")

    line_start = txt.rfind("\n", 0, return_pos) + 1
    return_line = txt[line_start:return_pos]
    indent = return_line[:len(return_line) - len(return_line.lstrip())]

    bloco = "\n".join(
        indent + linha if linha.strip() else ""
        for linha in compat.strip().splitlines()
    ) + "\n\n"

    txt = txt[:line_start] + bloco + txt[line_start:]

service_path.write_text(txt, encoding="utf-8")
py_compile.compile(str(service_path), doraise=True)
print("✅ expansao_service.py corrigido com alias classificacao/classificacao_score.")


# ============================================================
# 2) Corrigir app.py
# ============================================================

app_path = Path("app.py")
app = app_path.read_text(encoding="utf-8")

app = app.replace('color="classificacao"', 'color="classificacao_score"')
app = app.replace("color='classificacao'", "color='classificacao_score'")

app_path.write_text(app, encoding="utf-8")
py_compile.compile(str(app_path), doraise=True)
print("✅ app.py corrigido para usar classificacao_score nos gráficos.")

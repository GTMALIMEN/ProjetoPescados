from pathlib import Path
import py_compile
import shutil

service_path = Path("src/services/expansao_service.py")
backup = service_path.with_suffix(".py.bak_reparo_idc_indent")
shutil.copy2(service_path, backup)

txt = service_path.read_text(encoding="utf-8")

inicio = "# IDC_OFICIAL_NOVA_FORMULA_INICIO"
fim = "# IDC_OFICIAL_NOVA_FORMULA_FIM"

# Remove qualquer bloco quebrado já inserido
while inicio in txt and fim in txt:
    start = txt.find(inicio)
    end = txt.find(fim, start) + len(fim)

    # Remove a linha inteira do bloco
    line_start = txt.rfind("\n", 0, start)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1

    line_end = txt.find("\n", end)
    if line_end == -1:
        line_end = end

    txt = txt[:line_start] + txt[line_end + 1:]


anchor = 'df["participacao_receita_pct"] = df["total"] / receita_total * 100 if receita_total else 0.0'

if anchor not in txt:
    raise RuntimeError("Não encontrei a linha participacao_receita_pct no expansao_service.py")

pos = txt.find(anchor)
line_start = txt.rfind("\n", 0, pos) + 1
line_end = txt.find("\n", pos)

anchor_line = txt[line_start:line_end]
indent = anchor_line[:len(anchor_line) - len(anchor_line.lstrip())]

bloco = '''
# IDC_OFICIAL_NOVA_FORMULA_INICIO
# Garante que o IDC base/oficial use a mesma fórmula do simulador.
# Fórmula:
# PIB 25% + População 30-44 40% + Masculino 10% + Feminino 0%
# + Restaurantes 10% + População 15-29 10% + Total PDV 5%.
def _num_col_idc_base(df_base, col):
    if col not in df_base.columns:
        return pd.Series([0] * len(df_base), index=df_base.index, dtype="float64")
    return pd.to_numeric(df_base[col], errors="coerce").fillna(0)

def _fator_100_idc_base(df_base, col):
    s = _num_col_idc_base(df_base, col)
    max_v = s.max()
    if pd.isna(max_v) or max_v == 0:
        return pd.Series([0] * len(df_base), index=df_base.index, dtype="float64")
    return s / max_v * 100

# Regra correta de PDV:
# se total_pdv existir, usa total_pdv como base principal;
# se não existir, usa pdv_total;
# se nenhum existir, soma as colunas detalhadas.
if "total_pdv" not in df.columns:
    if "pdv_total" in df.columns:
        df["total_pdv"] = _num_col_idc_base(df, "pdv_total")
    else:
        df["total_pdv"] = (
            _num_col_idc_base(df, "supermercados")
            + _num_col_idc_base(df, "restaurantes")
            + _num_col_idc_base(df, "peixarias")
            + _num_col_idc_base(df, "outros_pdv")
        )

if "pdv_total" not in df.columns:
    df["pdv_total"] = _num_col_idc_base(df, "total_pdv")

if "restaurantes" not in df.columns:
    df["restaurantes"] = 0

df["fator_pib"] = _fator_100_idc_base(df, "pib")
df["fator_pop_30_44"] = _fator_100_idc_base(df, "pct_30_44")
df["fator_pop_15_29"] = _fator_100_idc_base(df, "pct_15_29")
df["fator_masculino"] = _fator_100_idc_base(df, "pct_masculina")
df["fator_feminino"] = _fator_100_idc_base(df, "pct_feminina")
df["fator_restaurantes"] = _fator_100_idc_base(df, "restaurantes")
df["fator_pdv_total"] = _fator_100_idc_base(df, "total_pdv")
df["fator_pdv"] = df["fator_pdv_total"]

df["idc_base"] = (
    df["fator_pib"] * 0.25
    + df["fator_pop_30_44"] * 0.40
    + df["fator_masculino"] * 0.10
    + df["fator_feminino"] * 0.00
    + df["fator_restaurantes"] * 0.10
    + df["fator_pop_15_29"] * 0.10
    + df["fator_pdv_total"] * 0.05
)

df["idc_planejado"] = df["idc_base"]
df["idc"] = df["idc_base"]
df["idc_final"] = df["idc_base"]
df["score"] = df["idc_base"]
df["score_idc"] = df["idc_base"]

if "_classificar_score" in globals():
    df["classificacao_score"] = df["idc_base"].apply(_classificar_score)
else:
    df["classificacao_score"] = pd.cut(
        pd.to_numeric(df["idc_base"], errors="coerce").fillna(0),
        bins=[-1, 35, 55, 75, 101],
        labels=["Monitorar", "Baixa", "Média", "Alta"]
    ).astype(str)

df["classificacao"] = df["classificacao_score"]

df["formula_idc"] = (
    "IDC = PIB 25% + População 30-44 40% + Masculino 10% + Feminino 0% "
    "+ Restaurantes 10% + População 15-29 10% + Total PDV 5%"
)
# IDC_OFICIAL_NOVA_FORMULA_FIM
'''

bloco_indentado = "\n".join(
    indent + linha if linha.strip() else ""
    for linha in bloco.strip("\n").splitlines()
) + "\n\n"

txt = txt[:line_end + 1] + bloco_indentado + txt[line_end + 1:]

service_path.write_text(txt, encoding="utf-8")
py_compile.compile(str(service_path), doraise=True)

print("✅ expansao_service.py reparado e compilando.")
print(f"Backup criado em: {backup}")

from pathlib import Path
import re
import py_compile

# ============================================================
# 1) Corrigir src/services/expansao_service.py
# ============================================================

service_path = Path("src/services/expansao_service.py")
txt = service_path.read_text(encoding="utf-8")

inicio = "# IDC_OFICIAL_NOVA_FORMULA_INICIO"
fim = "# IDC_OFICIAL_NOVA_FORMULA_FIM"

# Remove bloco antigo, se já existir
if inicio in txt and fim in txt:
    start = txt.find(inicio)
    end = txt.find(fim, start) + len(fim)
    txt = txt[:start] + txt[end:]

bloco_idc = '''
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

# Recalcula os fatores no mesmo recorte que está sendo exibido no app.
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

df["classificacao_score"] = df["idc_base"].apply(_classificar_score)
df["classificacao"] = df["classificacao_score"]

df["formula_idc"] = (
    "IDC = PIB 25% + População 30-44 40% + Masculino 10% + Feminino 0% "
    "+ Restaurantes 10% + População 15-29 10% + Total PDV 5%"
)
# IDC_OFICIAL_NOVA_FORMULA_FIM

'''

# Inserir depois de participacao_receita_pct e antes do over_under_share_pct
anchor = 'df["participacao_receita_pct"] = df["total"] / receita_total * 100 if receita_total else 0.0'

if anchor not in txt:
    raise RuntimeError("Não encontrei o ponto de inserção em expansao_service.py")

pos = txt.find(anchor) + len(anchor)
line_end = txt.find("\n", pos)
insert_at = line_end + 1

txt = txt[:insert_at] + bloco_idc + txt[insert_at:]

service_path.write_text(txt, encoding="utf-8")
py_compile.compile(str(service_path), doraise=True)

print("✅ expansao_service.py: IDC base/oficial alinhado à fórmula nova.")


# ============================================================
# 2) Corrigir app.py: simulador usa os mesmos fatores do IDC base
#    e cria gráfico Base x Simulado
# ============================================================

app_path = Path("app.py")
app = app_path.read_text(encoding="utf-8")

# Função nova para priorizar fator já calculado
if "def _fator_simulador_prioritario" not in app:
    alvo = '''def _fator_100(df, col, fallback=None):
                if col in df.columns:
                    s = _num_col(df, col)
                elif fallback and fallback in df.columns:
                    s = _num_col(df, fallback)
                else:
                    return pd.Series([0] * len(df), index=df.index, dtype="float64")

                max_v = s.max()

                if pd.isna(max_v) or max_v == 0:
                    return pd.Series([0] * len(df), index=df.index, dtype="float64")

                return s / max_v * 100'''

    novo = '''def _fator_100(df, col, fallback=None):
                if col in df.columns:
                    s = _num_col(df, col)
                elif fallback and fallback in df.columns:
                    s = _num_col(df, fallback)
                else:
                    return pd.Series([0] * len(df), index=df.index, dtype="float64")

                max_v = s.max()

                if pd.isna(max_v) or max_v == 0:
                    return pd.Series([0] * len(df), index=df.index, dtype="float64")

                return s / max_v * 100

            def _fator_simulador_prioritario(df, fator_col, raw_col):
                # Prioriza o fator já usado no IDC base.
                # Isso garante que, com os pesos padrão, Base = Simulado.
                if fator_col in df.columns:
                    return _num_col(df, fator_col)
                return _fator_100(df, raw_col)'''

    if alvo not in app:
        raise RuntimeError("Não encontrei a função _fator_100 no app.py")

    app = app.replace(alvo, novo)

# Trocar cálculo dos fatores simulados para usar fator oficial primeiro
repls = {
    'df_sim["fator_sim_pib"] = _fator_100(df_sim, "pib", fallback="fator_pib")':
        'df_sim["fator_sim_pib"] = _fator_simulador_prioritario(df_sim, "fator_pib", "pib")',

    'df_sim["fator_sim_pop_30_44"] = _fator_100(df_sim, "pct_30_44")':
        'df_sim["fator_sim_pop_30_44"] = _fator_simulador_prioritario(df_sim, "fator_pop_30_44", "pct_30_44")',

    'df_sim["fator_sim_pop_15_29"] = _fator_100(df_sim, "pct_15_29")':
        'df_sim["fator_sim_pop_15_29"] = _fator_simulador_prioritario(df_sim, "fator_pop_15_29", "pct_15_29")',

    'df_sim["fator_sim_masculino"] = _fator_100(df_sim, "pct_masculina")':
        'df_sim["fator_sim_masculino"] = _fator_simulador_prioritario(df_sim, "fator_masculino", "pct_masculina")',

    'df_sim["fator_sim_feminino"] = _fator_100(df_sim, "pct_feminina")':
        'df_sim["fator_sim_feminino"] = _fator_simulador_prioritario(df_sim, "fator_feminino", "pct_feminina")',

    'df_sim["fator_sim_restaurantes"] = _fator_100(df_sim, "restaurantes")':
        'df_sim["fator_sim_restaurantes"] = _fator_simulador_prioritario(df_sim, "fator_restaurantes", "restaurantes")',

    'df_sim["fator_sim_pdv_total"] = _fator_100(df_sim, "pdv_total")':
        'df_sim["fator_sim_pdv_total"] = _fator_simulador_prioritario(df_sim, "fator_pdv_total", "pdv_total")',
}

for old, new in repls.items():
    app = app.replace(old, new)

# Garantir idc_base e diferença no simulador
anchor_calc = '''df_sim["classificacao_simulada"] = pd.cut(
                    pd.to_numeric(df_sim["idc_simulado"], errors="coerce").fillna(0),
                    bins=[-1, 35, 55, 75, 101],
                    labels=["Monitorar", "Baixa", "Média", "Alta"]
                ).astype(str)'''

insert_calc = '''df_sim["classificacao_simulada"] = pd.cut(
                    pd.to_numeric(df_sim["idc_simulado"], errors="coerce").fillna(0),
                    bins=[-1, 35, 55, 75, 101],
                    labels=["Monitorar", "Baixa", "Média", "Alta"]
                ).astype(str)

                if "idc_base" not in df_sim.columns:
                    if "score" in df_sim.columns:
                        df_sim["idc_base"] = pd.to_numeric(df_sim["score"], errors="coerce").fillna(0)
                    elif "idc_planejado" in df_sim.columns:
                        df_sim["idc_base"] = pd.to_numeric(df_sim["idc_planejado"], errors="coerce").fillna(0)
                    else:
                        df_sim["idc_base"] = 0

                df_sim["diferenca_base_simulado"] = (
                    pd.to_numeric(df_sim["idc_simulado"], errors="coerce").fillna(0)
                    - pd.to_numeric(df_sim["idc_base"], errors="coerce").fillna(0)
                )'''

if anchor_calc in app and "diferenca_base_simulado" not in app:
    app = app.replace(anchor_calc, insert_calc)

# Adicionar colunas no resultado
app = app.replace(
    '''"idc_simulado",
                    "classificacao_simulada",''',
    '''"idc_base",
                    "idc_simulado",
                    "diferenca_base_simulado",
                    "classificacao_simulada",'''
)

# Inserir gráfico Base x Simulado antes do gráfico simulado atual
anchor_fig = '''fig_sim = px.bar(
                    df_sim.sort_values("idc_simulado", ascending=False).head(20),
                    x="microrregiao",
                    y="idc_simulado",
                    color="classificacao_simulada",
                    title="Top 20 microrregiões — IDC simulado"
                )'''

grafico_comp = '''st.markdown("##### Comparativo — IDC Base x IDC Simulado")

                df_comp = (
                    df_sim.sort_values("idc_simulado", ascending=False)
                    .head(20)[["microrregiao", "idc_base", "idc_simulado"]]
                    .melt(
                        id_vars="microrregiao",
                        value_vars=["idc_base", "idc_simulado"],
                        var_name="tipo_idc",
                        value_name="valor_idc"
                    )
                )

                fig_comp = px.bar(
                    df_comp,
                    x="microrregiao",
                    y="valor_idc",
                    color="tipo_idc",
                    barmode="group",
                    text="valor_idc",
                    title="Top 20 microrregiões — IDC Base x IDC Simulado"
                )
                fig_comp.update_traces(texttemplate="%{text:.4f}", textposition="outside")
                fig_comp.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_comp, use_container_width=True)

                fig_sim = px.bar(
                    df_sim.sort_values("idc_simulado", ascending=False).head(20),
                    x="microrregiao",
                    y="idc_simulado",
                    color="classificacao_simulada",
                    title="Top 20 microrregiões — IDC simulado"
                )'''

if anchor_fig in app and "IDC Base x IDC Simulado" not in app:
    app = app.replace(anchor_fig, grafico_comp)

app_path.write_text(app, encoding="utf-8")
py_compile.compile(str(app_path), doraise=True)

print("✅ app.py: simulador alinhado ao IDC base e gráfico Base x Simulado criado.")

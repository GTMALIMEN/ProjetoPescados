from pathlib import Path
import re
import shutil
import py_compile

# ============================================================
# 1) Ajustar view para expor supermercados/restaurantes/peixarias/outros_pdv
# ============================================================

view_path = Path("scripts/recriar_vw_idc_completo_atual.py")

if view_path.exists():
    txt = view_path.read_text(encoding="utf-8")

    alvo = "SUM({pdv_expr}) AS pdv_total,"

    bloco_pdv = """
                SUM(COALESCE(e.supermercados, 0)) AS supermercados,
                SUM(COALESCE(e.restaurantes, 0)) AS restaurantes,
                SUM(COALESCE(e.peixarias, 0)) AS peixarias,
                SUM(COALESCE(e.outros_pdv, 0)) AS outros_pdv,

                SUM({pdv_expr}) AS pdv_total,"""

    if alvo in txt and "AS restaurantes" not in txt:
        txt = txt.replace(alvo, bloco_pdv)

        view_path.write_text(txt, encoding="utf-8")
        py_compile.compile(str(view_path), doraise=True)

        print("✅ scripts/recriar_vw_idc_completo_atual.py ajustado para expor PDVs detalhados.")
    else:
        print("ℹ️ View já parece ter restaurantes/PDVs detalhados ou alvo não encontrado.")
else:
    print("⚠️ scripts/recriar_vw_idc_completo_atual.py não encontrado.")


# ============================================================
# 2) Substituir bloco do Simulador IDC no app.py
# ============================================================

app_path = Path("app.py")
backup = app_path.with_suffix(".py.bak_simulador_idc")
shutil.copy2(app_path, backup)

txt = app_path.read_text(encoding="utf-8")
lines = txt.splitlines()

start = None
for i, line in enumerate(lines):
    if 'st.markdown("#### Simulador de critérios IDC")' in line:
        start = i
        break

if start is None:
    raise RuntimeError('Não encontrei st.markdown("#### Simulador de critérios IDC") no app.py')

indent = lines[start][:len(lines[start]) - len(lines[start].lstrip())]
indent_len = len(indent)

end = None
for i in range(start + 1, len(lines)):
    line = lines[i]

    if not line.strip():
        continue

    current_indent_len = len(line) - len(line.lstrip())

    # Sai do bloco quando volta para uma indentação menor que a do conteúdo da aba.
    if current_indent_len < indent_len:
        end = i
        break

if end is None:
    end = len(lines)

novo_bloco = r'''
st.markdown("#### Simulador de critérios IDC")
st.caption(
    "Os pesos não são ajustados automaticamente. "
    "A simulação só é liberada quando a soma dos pesos fechar exatamente 100%."
)

# Pesos padrão solicitados
defaults_simulador = {
    "idc_w_pib": 25,
    "idc_w_pop_30_44": 40,
    "idc_w_masculino": 10,
    "idc_w_feminino": 0,
    "idc_w_restaurantes": 10,
    "idc_w_pop_15_29": 15,
    "idc_w_pdv_total": 0,
}

for k, v in defaults_simulador.items():
    if k not in st.session_state:
        st.session_state[k] = v

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.slider("Peso PIB", 0, 100, key="idc_w_pib")
    st.slider("Peso população 30–44", 0, 100, key="idc_w_pop_30_44")

with c2:
    st.slider("Peso população 15–29", 0, 100, key="idc_w_pop_15_29")
    st.slider("Peso população masculina", 0, 100, key="idc_w_masculino")

with c3:
    st.slider("Peso população feminina", 0, 100, key="idc_w_feminino")
    st.slider("Peso restaurantes", 0, 100, key="idc_w_restaurantes")

with c4:
    st.slider("Peso pontos de venda total", 0, 100, key="idc_w_pdv_total")

peso_total_simulador = (
    st.session_state["idc_w_pib"]
    + st.session_state["idc_w_pop_30_44"]
    + st.session_state["idc_w_pop_15_29"]
    + st.session_state["idc_w_masculino"]
    + st.session_state["idc_w_feminino"]
    + st.session_state["idc_w_restaurantes"]
    + st.session_state["idc_w_pdv_total"]
)

if peso_total_simulador == 100:
    st.success("Total dos pesos: 100% — OK para simular")
else:
    st.error(f"Total dos pesos: {peso_total_simulador}% — ajuste para fechar 100%")

def _num_col(df, col):
    if col not in df.columns:
        return pd.Series([0] * len(df), index=df.index, dtype="float64")
    return pd.to_numeric(df[col], errors="coerce").fillna(0)

def _fator_100(df, col, fallback=None):
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

simular_idc = st.button(
    "Simular IDC",
    disabled=peso_total_simulador != 100,
    key="btn_simular_idc_novo"
)

if simular_idc:
    df_sim = df_idc.copy()

    # Garante pontos de venda total caso venha separado
    if "pdv_total" not in df_sim.columns:
        df_sim["pdv_total"] = (
            _num_col(df_sim, "supermercados")
            + _num_col(df_sim, "restaurantes")
            + _num_col(df_sim, "peixarias")
            + _num_col(df_sim, "outros_pdv")
        )

    if "restaurantes" not in df_sim.columns:
        st.warning(
            "Coluna 'restaurantes' não encontrada no DataFrame. "
            "O fator restaurantes será considerado 0 até a view/base expor esse campo."
        )
        df_sim["restaurantes"] = 0

    df_sim["fator_sim_pib"] = _fator_100(df_sim, "pib", fallback="fator_pib")
    df_sim["fator_sim_pop_30_44"] = _fator_100(df_sim, "pct_30_44")
    df_sim["fator_sim_pop_15_29"] = _fator_100(df_sim, "pct_15_29")
    df_sim["fator_sim_masculino"] = _fator_100(df_sim, "pct_masculina")
    df_sim["fator_sim_feminino"] = _fator_100(df_sim, "pct_feminina")
    df_sim["fator_sim_restaurantes"] = _fator_100(df_sim, "restaurantes")
    df_sim["fator_sim_pdv_total"] = _fator_100(df_sim, "pdv_total")

    df_sim["idc_simulado"] = (
        df_sim["fator_sim_pib"] * st.session_state["idc_w_pib"] / 100
        + df_sim["fator_sim_pop_30_44"] * st.session_state["idc_w_pop_30_44"] / 100
        + df_sim["fator_sim_pop_15_29"] * st.session_state["idc_w_pop_15_29"] / 100
        + df_sim["fator_sim_masculino"] * st.session_state["idc_w_masculino"] / 100
        + df_sim["fator_sim_feminino"] * st.session_state["idc_w_feminino"] / 100
        + df_sim["fator_sim_restaurantes"] * st.session_state["idc_w_restaurantes"] / 100
        + df_sim["fator_sim_pdv_total"] * st.session_state["idc_w_pdv_total"] / 100
    )

    df_sim["classificacao_simulada"] = pd.cut(
        pd.to_numeric(df_sim["idc_simulado"], errors="coerce").fillna(0),
        bins=[-1, 35, 55, 75, 101],
        labels=["Monitorar", "Baixa", "Média", "Alta"]
    ).astype(str)

    cols_resultado = [
        "estado",
        "microrregiao",
        "idc_simulado",
        "classificacao_simulada",
        "pib",
        "pct_30_44",
        "pct_15_29",
        "pct_masculina",
        "pct_feminina",
        "restaurantes",
        "pdv_total",
    ]

    cols_resultado = [c for c in cols_resultado if c in df_sim.columns]

    st.markdown("##### Resultado da simulação")
    st.dataframe(
        df_sim.sort_values("idc_simulado", ascending=False)[cols_resultado].head(50),
        use_container_width=True
    )

    fig_sim = px.bar(
        df_sim.sort_values("idc_simulado", ascending=False).head(20),
        x="microrregiao",
        y="idc_simulado",
        color="classificacao_simulada",
        title="Top 20 microrregiões — IDC simulado"
    )
    fig_sim.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_sim, use_container_width=True)
'''

novo_bloco_lines = [
    indent + linha if linha.strip() else ""
    for linha in novo_bloco.strip("\n").splitlines()
]

lines[start:end] = novo_bloco_lines

app_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
py_compile.compile(str(app_path), doraise=True)

print("✅ app.py ajustado: Simulador IDC atualizado com novos fatores e pesos.")
print(f"Backup criado em: {backup}")

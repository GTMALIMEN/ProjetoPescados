from pathlib import Path
import py_compile

app_path = Path("app.py")
txt = app_path.read_text(encoding="utf-8")

# ============================================================
# 1) Atualizar pesos padrão
# ============================================================

txt = txt.replace('"idc_w_pop_15_29": 15,', '"idc_w_pop_15_29": 10,')
txt = txt.replace('"idc_w_pdv_total": 0,', '"idc_w_pdv_total": 5,')

# ============================================================
# 2) Forçar atualização dos pesos na sessão do Streamlit
#    para quem já abriu o app antes não ficar com valor antigo
# ============================================================

old_session_block = '''for k, v in defaults_simulador.items():
    if k not in st.session_state:
        st.session_state[k] = v'''

new_session_block = '''versao_pesos_simulador = "v3_pib25_pop3044_40_masc10_fem0_rest10_pop1529_10_pdv5"

if st.session_state.get("_idc_simulador_pesos_versao") != versao_pesos_simulador:
    for k, v in defaults_simulador.items():
        st.session_state[k] = v
    st.session_state["_idc_simulador_pesos_versao"] = versao_pesos_simulador
else:
    for k, v in defaults_simulador.items():
        if k not in st.session_state:
            st.session_state[k] = v'''

if old_session_block in txt:
    txt = txt.replace(old_session_block, new_session_block)
elif 'versao_pesos_simulador' in txt:
    # Já existe controle de versão; só atualiza a versão se necessário.
    txt = txt.replace(
        'versao_pesos_simulador = "v2_pib25_pop3044_40_masc10_fem0_rest10_pop1529_15_pdv0"',
        'versao_pesos_simulador = "v3_pib25_pop3044_40_masc10_fem0_rest10_pop1529_10_pdv5"'
    )

# ============================================================
# 3) Atualizar legenda/fórmula do simulador
# ============================================================

formula_block = '''
st.markdown(
    """
    **Fórmula padrão do IDC Simulado:**  
    `IDC Simulado = (PIB × 25%) + (População 30–44 × 40%) + (Masculino × 10%) + (Feminino × 0%) + (Restaurantes × 10%) + (População 15–29 × 10%) + (Pontos de venda total × 5%)`

    Todos os fatores são normalizados em escala **0–100** antes da aplicação dos pesos.
    """
)
'''

# Remove fórmula antiga, se já existir
start_marker = 'st.markdown(\n    """\n    **Fórmula padrão do IDC Simulado:**'
if start_marker in txt:
    start = txt.find(start_marker)
    end = txt.find('\n)\n', start)
    if end != -1:
        txt = txt[:start] + txt[end + 3:]

# Insere fórmula depois do status de soma dos pesos
anchor = '''if peso_total_simulador == 100:
    st.success("Total dos pesos: 100% — OK para simular")
else:
    st.error(f"Total dos pesos: {peso_total_simulador}% — ajuste para fechar 100%")'''

if anchor in txt and "População 30–44 × 40%" not in txt:
    txt = txt.replace(anchor, anchor + "\n\n" + formula_block)

# ============================================================
# 4) Garantir cálculo com novos pesos
# ============================================================

txt = txt.replace(
    'df_sim["fator_sim_pop_15_29"] * st.session_state["idc_w_pop_15_29"] / 100',
    'df_sim["fator_sim_pop_15_29"] * st.session_state["idc_w_pop_15_29"] / 100'
)

txt = txt.replace(
    'df_sim["fator_sim_pdv_total"] * st.session_state["idc_w_pdv_total"] / 100',
    'df_sim["fator_sim_pdv_total"] * st.session_state["idc_w_pdv_total"] / 100'
)

app_path.write_text(txt, encoding="utf-8")
py_compile.compile(str(app_path), doraise=True)

print("✅ Simulador IDC atualizado:")
print("- PIB = 25%")
print("- População 30–44 = 40%")
print("- Masculino = 10%")
print("- Feminino = 0%")
print("- Restaurantes = 10%")
print("- População 15–29 = 10%")
print("- Pontos de venda total = 5%")
print("✅ Fórmula/legenda atualizada no app.")

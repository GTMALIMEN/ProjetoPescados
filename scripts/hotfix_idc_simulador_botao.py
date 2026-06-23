from pathlib import Path

p = Path("app.py")
txt = p.read_text(encoding="utf-8")

# ============================================================
# 1) Trocar bloco de helpers do IDC
# ============================================================

ini = txt.find("# ============================================================ # Simulador IDC")
fim = txt.find("def dataframe_periodo", ini)

if ini == -1 or fim == -1:
    raise RuntimeError("Não encontrei o bloco de helpers do Simulador IDC.")

novo_helpers = r'''# ============================================================ # Simulador IDC — pesos livres, validação em 100%
# ============================================================
PESOS_IDC_DEFAULT = {
    "idc_w_pop": 30,
    "idc_w_pib": 25,
    "idc_w_renda": 15,
    "idc_w_pib_per_capita": 15,
    "idc_w_fem": 5,
    "idc_w_masc": 5,
    "idc_w_pdv": 5,
}

PESOS_IDC_LABELS = {
    "idc_w_pop": "População",
    "idc_w_pib": "PIB",
    "idc_w_renda": "Renda / POF",
    "idc_w_pib_per_capita": "PIB per capita",
    "idc_w_fem": "Gênero feminino",
    "idc_w_masc": "Gênero masculino",
    "idc_w_pdv": "Pontos de venda",
}

def _inicializar_pesos_idc():
    """Inicializa pesos padrão. Não redistribui automaticamente."""
    for key, value in PESOS_IDC_DEFAULT.items():
        if key not in st.session_state:
            st.session_state[key] = int(value)

def _pesos_idc_atuais() -> dict:
    _inicializar_pesos_idc()
    return {k: int(st.session_state.get(k, 0)) for k in PESOS_IDC_DEFAULT}

def _total_pesos_idc() -> int:
    pesos = _pesos_idc_atuais()
    return int(sum(pesos.values()))

def _html_status_pesos_idc(total: int) -> str:
    ok = total == 100
    cor = "#00C853" if ok else "#D50000"
    fundo = "rgba(0,200,83,0.12)" if ok else "rgba(213,0,0,0.12)"
    texto = "OK para simular" if ok else "Ajuste os pesos para fechar 100%"
    return f"""
    <div style="
        padding: 14px 18px;
        border-radius: 12px;
        border: 1px solid {cor};
        background: {fundo};
        margin: 8px 0 16px 0;
        font-weight: 700;
        color: {cor};
        font-size: 18px;
    ">
        Total dos pesos: {total}% — {texto}
    </div>
    """

'''

txt = txt[:ini] + novo_helpers + txt[fim:]


# ============================================================
# 2) Trocar bloco visual do simulador IDC
# ============================================================

ini = txt.find("with tab_simulador:")
fim = txt.find('st.markdown("### Exportar bases da Análise de Expansão")', ini)

if ini == -1 or fim == -1:
    raise RuntimeError("Não encontrei o bloco visual do Simulador IDC.")

novo_simulador = r'''with tab_simulador:
            st.markdown("#### Simulador de critérios IDC")
            st.caption(
                "Os pesos não são ajustados automaticamente. "
                "A simulação só é liberada quando a soma dos pesos fechar exatamente 100%."
            )

            _inicializar_pesos_idc()

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.slider("Peso população", 0, 100, key="idc_w_pop")
                st.slider("Peso PIB", 0, 100, key="idc_w_pib")

            with c2:
                st.slider("Peso renda / POF", 0, 100, key="idc_w_renda")
                st.slider("Peso PIB per capita", 0, 100, key="idc_w_pib_per_capita")

            with c3:
                st.slider("Peso gênero feminino", 0, 100, key="idc_w_fem")
                st.slider("Peso gênero masculino", 0, 100, key="idc_w_masc")

            with c4:
                st.slider("Peso pontos de venda", 0, 100, key="idc_w_pdv")

            pesos_idc = _pesos_idc_atuais()
            total_pesos_idc = _total_pesos_idc()

            st.markdown(_html_status_pesos_idc(total_pesos_idc), unsafe_allow_html=True)
            st.progress(min(total_pesos_idc, 100) / 100)

            if total_pesos_idc < 100:
                st.error(f"Faltam {100 - total_pesos_idc}% para fechar 100%.")
            elif total_pesos_idc > 100:
                st.error(f"Os pesos excederam {total_pesos_idc - 100}%. Reduza algum critério.")
            else:
                st.success("Pesos fechados em 100%. Simulação liberada.")

            parametros = {
                "peso_populacao": pesos_idc["idc_w_pop"],
                "peso_pib": pesos_idc["idc_w_pib"],
                "peso_renda": pesos_idc["idc_w_renda"],
                "peso_pib_per_capita": pesos_idc["idc_w_pib_per_capita"],
                "peso_feminino": pesos_idc["idc_w_fem"],
                "peso_masculino": pesos_idc["idc_w_masc"],
                "peso_pdv": pesos_idc["idc_w_pdv"],
            }

            with st.expander("Fórmula IDC usada no simulador", expanded=True):
                st.markdown("""
                **Fórmula padrão do IDC estratégico:**

                `IDC = 30% População + 25% PIB + 15% Renda + 15% PIB per capita + 5% Feminino + 5% Masculino + 5% Pontos de venda`

                No simulador, você pode alterar os pesos, mas a soma precisa fechar **100%**.
                """)

            simular_idc_btn = st.button(
                "Simular IDC",
                disabled=total_pesos_idc != 100,
                key="btn_simular_idc",
                type="primary"
            )

            if total_pesos_idc != 100:
                st.warning("Ajuste os pesos até fechar 100% para liberar o botão de simulação.")

            if simular_idc_btn:
                with st.spinner("Calculando simulação IDC..."):
                    df_sim = simular_idc_expansao(estados=estados_exp, **parametros)

                if not df_sim.empty:
                    df_long = df_sim.head(20).melt(
                        id_vars=["microrregiao", "estado"],
                        value_vars=["idc_base", "idc_simulado"],
                        var_name="tipo_idc",
                        value_name="valor_idc",
                    )

                    fig_comp = px.bar(
                        df_long,
                        x="microrregiao",
                        y="valor_idc",
                        color="tipo_idc",
                        barmode="group",
                        title="IDC estratégico atual x IDC simulado"
                    )
                    st.plotly_chart(fig_comp, use_container_width=True)

                    dataframe_or_warning(df_sim[[
                        "microrregiao", "estado", "idc_base", "idc_simulado", "diferenca_idc",
                        "score", "score_simulado", "classificacao", "nova_classificacao",
                        "fator_populacao", "fator_pib", "fator_renda", "fator_pib_per_capita",
                        "fator_feminino", "fator_masculino", "fator_pdv", "peso_total_simulador",
                        "status_simulador"
                    ]], "Sem simulação.")
                else:
                    st.warning("A simulação não retornou dados.")
            else:
                st.info("A simulação ainda não foi executada. Ajuste os pesos e clique em **Simular IDC**.")

            '''

txt = txt[:ini] + novo_simulador + txt[fim:]


# ============================================================
# 3) Evitar export automático da expansão
# ============================================================

antigo_export = '''st.markdown("### Exportar bases da Análise de Expansão") excel_exp = exportar_bases_expansao_excel(parametros=parametros, estados=estados_exp) st.download_button( "Baixar Excel — Análise de Expansão", data=excel_exp, file_name=f"analise_expansao_{estado_base.lower()}_bases.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", )'''

novo_export = '''st.markdown("### Exportar bases da Análise de Expansão")
        st.caption("A exportação agora só é gerada quando você clicar no botão, evitando carga automática no banco.")

        if "excel_expansao_bytes" not in st.session_state:
            st.session_state["excel_expansao_bytes"] = None

        if st.button("Gerar Excel — Análise de Expansão", key="btn_gerar_excel_expansao"):
            with st.spinner("Gerando Excel da Análise de Expansão..."):
                st.session_state["excel_expansao_bytes"] = exportar_bases_expansao_excel(
                    parametros=parametros,
                    estados=estados_exp
                )

        if st.session_state.get("excel_expansao_bytes") is not None:
            st.download_button(
                "Baixar Excel — Análise de Expansão",
                data=st.session_state["excel_expansao_bytes"],
                file_name=f"analise_expansao_{estado_base.lower()}_bases.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )'''

if antigo_export in txt:
    txt = txt.replace(antigo_export, novo_export)
else:
    print("⚠️ Bloco de exportação automática não encontrado exatamente. Verificar manualmente se ainda gera Excel sozinho.")

p.write_text(txt, encoding="utf-8")
print("✅ Hotfix IDC aplicado em app.py")

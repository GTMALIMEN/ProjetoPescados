from pathlib import Path
import py_compile
import shutil

path = Path("app.py")
backup = path.with_suffix(".py.bak_visao_simulador")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

# 1) Inserir seletor de visão antes do botão Simular IDC
if 'key="idc_visao_simulador"' not in txt:
    alvo = '''            simular_idc = st.button(
                "Simular IDC",
                disabled=peso_total_simulador != 100,
                key="btn_simular_idc_novo"
            )'''

    bloco = '''            visao_simulador = st.radio(
                "Visão da simulação",
                ["Microrregião", "Cidade/Município"],
                horizontal=True,
                key="idc_visao_simulador",
                help="Microrregião consolida municípios. Cidade/Município mostra o detalhe municipal quando a base estiver disponível."
            )

            simular_idc = st.button(
                "Simular IDC",
                disabled=peso_total_simulador != 100,
                key="btn_simular_idc_novo"
            )'''

    if alvo not in txt:
        raise RuntimeError("Não encontrei o botão Simular IDC no app.py")

    txt = txt.replace(alvo, bloco)


# 2) Trocar df_sim = df_idc.copy() por visão dinâmica
txt = txt.replace(
    '''                df_sim = df_idc.copy()''',
    '''                if st.session_state.get("idc_visao_simulador") == "Cidade/Município":
                    df_sim = calcular_idc_expansao(estados=estados_exp, visao="cidade")
                    coluna_visao_idc = "municipio" if "municipio" in df_sim.columns else "cidade"
                    titulo_visao_idc = "municípios"
                else:
                    df_sim = df_idc.copy()
                    coluna_visao_idc = "microrregiao"
                    titulo_visao_idc = "microrregiões"'''
)


# 3) Usar fatores oficiais quando existirem
repls = {
    'df_sim["fator_sim_pib"] = _fator_100(df_sim, "pib", fallback="fator_pib")':
        'df_sim["fator_sim_pib"] = _num_col(df_sim, "fator_pib") if "fator_pib" in df_sim.columns else _fator_100(df_sim, "pib")',

    'df_sim["fator_sim_pop_30_44"] = _fator_100(df_sim, "pct_30_44")':
        'df_sim["fator_sim_pop_30_44"] = _num_col(df_sim, "fator_pop_30_44") if "fator_pop_30_44" in df_sim.columns else _fator_100(df_sim, "pct_30_44")',

    'df_sim["fator_sim_pop_15_29"] = _fator_100(df_sim, "pct_15_29")':
        'df_sim["fator_sim_pop_15_29"] = _num_col(df_sim, "fator_pop_15_29") if "fator_pop_15_29" in df_sim.columns else _fator_100(df_sim, "pct_15_29")',

    'df_sim["fator_sim_masculino"] = _fator_100(df_sim, "pct_masculina")':
        'df_sim["fator_sim_masculino"] = _num_col(df_sim, "fator_masculino") if "fator_masculino" in df_sim.columns else _fator_100(df_sim, "pct_masculina")',

    'df_sim["fator_sim_feminino"] = _fator_100(df_sim, "pct_feminina")':
        'df_sim["fator_sim_feminino"] = _num_col(df_sim, "fator_feminino") if "fator_feminino" in df_sim.columns else _fator_100(df_sim, "pct_feminina")',

    'df_sim["fator_sim_restaurantes"] = _fator_100(df_sim, "restaurantes")':
        'df_sim["fator_sim_restaurantes"] = _num_col(df_sim, "fator_restaurantes") if "fator_restaurantes" in df_sim.columns else _fator_100(df_sim, "restaurantes")',

    'df_sim["fator_sim_pdv_total"] = _fator_100(df_sim, "pdv_total")':
        'df_sim["fator_sim_pdv_total"] = _num_col(df_sim, "fator_pdv_total") if "fator_pdv_total" in df_sim.columns else _fator_100(df_sim, "pdv_total")',
}

for old, new in repls.items():
    txt = txt.replace(old, new)


# 4) Inserir idc_base e diferença após classificacao_simulada
if 'df_sim["diferenca_base_simulado"]' not in txt:
    alvo = '''                df_sim["classificacao_simulada"] = pd.cut(
                    pd.to_numeric(df_sim["idc_simulado"], errors="coerce").fillna(0),
                    bins=[-1, 35, 55, 75, 101],
                    labels=["Monitorar", "Baixa", "Média", "Alta"]
                ).astype(str)'''

    bloco = alvo + '''

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

    if alvo not in txt:
        raise RuntimeError("Não encontrei classificacao_simulada no app.py")

    txt = txt.replace(alvo, bloco)


# 5) Trocar lista de colunas da tabela
inicio = '''                cols_resultado = [
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
                ]'''

novo = '''                cols_resultado = [
                    "estado",
                    "regiao_economica",
                    "microrregiao",
                    "municipio",
                    "cidade",
                    "idc_base",
                    "idc_simulado",
                    "diferenca_base_simulado",
                    "classificacao_simulada",
                    "pib",
                    "pct_30_44",
                    "pct_15_29",
                    "pct_masculina",
                    "pct_feminina",
                    "restaurantes",
                    "total_pdv",
                    "pdv_total",
                ]'''

if inicio in txt:
    txt = txt.replace(inicio, novo)


# 6) Inserir gráfico Base x Simulado e usar coluna dinâmica
if "Top 20 — IDC Base x IDC Simulado" not in txt:
    alvo = '''                fig_sim = px.bar(
                    df_sim.sort_values("idc_simulado", ascending=False).head(20),
                    x="microrregiao",
                    y="idc_simulado",
                    color="classificacao_simulada",
                    title="Top 20 microrregiões — IDC simulado"
                )'''

    bloco = '''                st.markdown("##### Comparativo — IDC Base x IDC Simulado")

                df_comp = (
                    df_sim.sort_values("idc_simulado", ascending=False)
                    .head(20)[[coluna_visao_idc, "idc_base", "idc_simulado"]]
                    .melt(
                        id_vars=coluna_visao_idc,
                        value_vars=["idc_base", "idc_simulado"],
                        var_name="tipo_idc",
                        value_name="valor_idc"
                    )
                )

                fig_comp = px.bar(
                    df_comp,
                    x=coluna_visao_idc,
                    y="valor_idc",
                    color="tipo_idc",
                    barmode="group",
                    text="valor_idc",
                    title=f"Top 20 {titulo_visao_idc} — IDC Base x IDC Simulado"
                )
                fig_comp.update_traces(texttemplate="%{text:.4f}", textposition="outside")
                fig_comp.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_comp, use_container_width=True)

                fig_sim = px.bar(
                    df_sim.sort_values("idc_simulado", ascending=False).head(20),
                    x=coluna_visao_idc,
                    y="idc_simulado",
                    color="classificacao_simulada",
                    title=f"Top 20 {titulo_visao_idc} — IDC simulado"
                )'''

    if alvo not in txt:
        raise RuntimeError("Não encontrei fig_sim no app.py")

    txt = txt.replace(alvo, bloco)
else:
    txt = txt.replace('x="microrregiao"', 'x=coluna_visao_idc')
    txt = txt.replace('title="Top 20 microrregiões — IDC simulado"', 'title=f"Top 20 {titulo_visao_idc} — IDC simulado"')


path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ app.py ajustado com visão Microrregião/Cidade e gráfico Base x Simulado.")
print(f"Backup criado em: {backup}")

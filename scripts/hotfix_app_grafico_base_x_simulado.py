from pathlib import Path
import py_compile
import shutil

app_path = Path("app.py")
backup = app_path.with_suffix(".py.bak_base_x_simulado")
shutil.copy2(app_path, backup)

txt = app_path.read_text(encoding="utf-8")

# ============================================================
# 1) Simulador usa os mesmos fatores oficiais do IDC base
# ============================================================

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


# ============================================================
# 2) Garantir idc_base e diferença base x simulado
# ============================================================

if 'df_sim["diferenca_base_simulado"]' not in txt:
    marker = '''df_sim["classificacao_simulada"] = pd.cut(
                    pd.to_numeric(df_sim["idc_simulado"], errors="coerce").fillna(0),
                    bins=[-1, 35, 55, 75, 101],
                    labels=["Monitorar", "Baixa", "Média", "Alta"]
                ).astype(str)'''

    if marker not in txt:
        raise RuntimeError("Não encontrei bloco classificacao_simulada no app.py")

    insert = marker + '''

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

    txt = txt.replace(marker, insert)


# ============================================================
# 3) Adicionar idc_base e diferença na tabela
# ============================================================

if '"diferenca_base_simulado",' not in txt:
    txt = txt.replace(
        '''                    "idc_simulado",
                    "classificacao_simulada",''',
        '''                    "idc_base",
                    "idc_simulado",
                    "diferenca_base_simulado",
                    "classificacao_simulada",'''
    )


# ============================================================
# 4) Inserir gráfico Base x Simulado
# ============================================================

if "Top 20 microrregiões — IDC Base x IDC Simulado" not in txt:
    marker = '''                fig_sim = px.bar(
                    df_sim.sort_values("idc_simulado", ascending=False).head(20),
                    x="microrregiao",
                    y="idc_simulado",
                    color="classificacao_simulada",
                    title="Top 20 microrregiões — IDC simulado"
                )'''

    if marker not in txt:
        raise RuntimeError("Não encontrei bloco fig_sim no app.py")

    bloco = '''                st.markdown("##### Comparativo — IDC Base x IDC Simulado")

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

    txt = txt.replace(marker, bloco)

app_path.write_text(txt, encoding="utf-8")
py_compile.compile(str(app_path), doraise=True)

print("✅ app.py corrigido: simulador usa fatores oficiais e gráfico Base x Simulado foi criado.")
print(f"Backup criado em: {backup}")

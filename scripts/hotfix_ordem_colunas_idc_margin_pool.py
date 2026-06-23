from pathlib import Path
import py_compile
import shutil

path = Path("app.py")
backup = path.with_suffix(".py.bak_ordem_colunas_idc_margin_pool")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

helper = r'''
def ordenar_colunas_idc_margin_pool(df):
    ordem = [
        "estado",
        "microrregiao",
        "regiao_economica",
        "populacao",
        "pib",
        "pib_per_capita",
        "idh",
        "renda_media",
        "renda_mediana",
        "pop_masculina",
        "pop_feminina",
        "pop_0_14",
        "pop_15_29",
        "pop_30_44",
        "pop_45_59",
        "pop_60_plus",
        "pct_masculina",
        "pct_feminina",
        "pct_0_14",
        "pct_15_29",
        "pct_30_44",
        "pct_45_59",
        "pct_60_plus",
        "supermercados",
        "restaurantes",
        "peixarias",
        "outros_pdv",
        "total_pdv",
        "pdv_total",
        "qtd_municipios",
        "participacao_populacao_pct",
        "participacao_pib_pct",
        "fator_populacao",
        "fator_pib",
        "fator_renda",
        "fator_pib_per_capita",
        "fator_pop_30_44",
        "fator_pop_15_29",
        "fator_masculino",
        "fator_feminino",
        "fator_restaurantes",
        "fator_pdv_total",
        "fator_pdv",
        "idc_planejado",
        "idc",
        "idc_final",
        "idc_base",
        "idc_macro",
        "score",
        "score_idc",
        "classificacao_score",
        "classificacao",
        "total",
        "receita_media_12m",
        "ultima_venda",
        "participacao_receita_pct",
        "over_under_share_pct",
        "receita_esperada_idc",
        "oportunidade",
        "margin_pool_pct",
        "classe_populacao_ibge",
        "classe_populacao_ibge_ordem",
        "classe_populacao",
        "classe_populacao_ordem",
        "Classe A",
        "Classe B",
        "Classe C",
        "Classe D",
        "Classe E",
        "salario_minimo_ref",
        "renda_base_classe",
        "renda_familiar_sm",
        "renda_per_capita_sm",
        "renda_familiar_estimativa",
        "classe_renda",
        "classe_renda_status",
        "criterio_classe_renda",
        "domicilios_particulares_ocupados",
        "moradores_domicilios_particulares_ocupados",
        "moradores_por_domicilio",
        "fonte_moradores_domicilio",
        "fonte_demografia",
        "fonte_renda",
        "fonte_pdv",
        "data_atualizacao",
        "formula_idc",
        "nivel_visao",
        "status_receita",
        "observacao_idc",
    ]

    cols = [c for c in ordem if c in df.columns]
    extras = [c for c in df.columns if c not in cols]
    return df[cols + extras]
'''

if "def ordenar_colunas_idc_margin_pool" not in txt:
    # Insere antes da primeira função de dataframe ou antes do primeiro uso de tabs.
    marcador = "def dataframe_or_warning"
    if marcador in txt:
        txt = txt.replace(marcador, helper + "\n\n" + marcador, 1)
    else:
        # fallback: coloca depois dos imports principais
        pos = txt.find("st.set_page_config")
        if pos == -1:
            raise RuntimeError("Não encontrei ponto seguro para inserir helper.")
        txt = txt[:pos] + helper + "\n\n" + txt[pos:]

# Aplica a ordenação depois que df_idc é calculado.
if "df_idc = ordenar_colunas_idc_margin_pool(df_idc)" not in txt:
    linhas = txt.splitlines()
    novas = []

    for line in linhas:
        novas.append(line)

        if "df_idc = calcular_idc_expansao(" in line:
            indent = line[:len(line) - len(line.lstrip())]
            novas.append(indent + "df_idc = ordenar_colunas_idc_margin_pool(df_idc)")

    txt = "\n".join(novas) + "\n"

path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ Ordem de colunas do IDC / Margin Pool aplicada.")
print("✅ app.py compilando.")
print("Backup criado em:", backup)

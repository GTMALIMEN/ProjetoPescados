from pathlib import Path
import py_compile
import shutil

path = Path("app.py")
backup = path.with_suffix(".py.bak_simulador_tabela_charts_v2")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")


# ============================================================
# 1) Garantir colunas de localização após escolher visão
# ============================================================

anchor = '''                else:
                    df_sim = df_idc.copy()
                    coluna_visao_idc = "microrregiao"
                    titulo_visao_idc = "microrregiões"'''

insert = '''                else:
                    df_sim = df_idc.copy()
                    coluna_visao_idc = "microrregiao"
                    titulo_visao_idc = "microrregiões"

                # Garante colunas de localização para tabela e gráficos
                if "municipio" not in df_sim.columns and "cidade" in df_sim.columns:
                    df_sim["municipio"] = df_sim["cidade"]

                if "cidade" not in df_sim.columns and "municipio" in df_sim.columns:
                    df_sim["cidade"] = df_sim["municipio"]

                if "regiao_economica" not in df_sim.columns:
                    df_sim["regiao_economica"] = None

                if "microrregiao" not in df_sim.columns:
                    df_sim["microrregiao"] = None'''

if anchor in txt and "Garante colunas de localização para tabela e gráficos" not in txt:
    txt = txt.replace(anchor, insert)


# ============================================================
# 2) Substituir lista cols_resultado de forma robusta
# ============================================================

marker_resultado = 'st.markdown("##### Resultado da simulação")'
idx_resultado = txt.find(marker_resultado)

if idx_resultado == -1:
    raise RuntimeError("Não encontrei Resultado da simulação no app.py")

start = txt.rfind("cols_resultado = [", 0, idx_resultado)

if start == -1:
    raise RuntimeError("Não encontrei cols_resultado antes do Resultado da simulação")

line_start = txt.rfind("\n", 0, start) + 1
indent = txt[line_start:start]

# Encontra o fechamento da lista por contagem de colchetes
depth = 0
end = None

for i in range(start, len(txt)):
    if txt[i] == "[":
        depth += 1
    elif txt[i] == "]":
        depth -= 1
        if depth == 0:
            end = i + 1
            break

if end is None:
    raise RuntimeError("Não encontrei fechamento da lista cols_resultado")

cols = [
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
]

novo_cols = indent + "cols_resultado = [\n"
for col in cols:
    novo_cols += indent + f'    "{col}",\n'
novo_cols += indent + "]"

txt = txt[:start] + novo_cols + txt[end:]


# ============================================================
# 3) Ajustar gráficos para usar coluna da visão
# ============================================================

txt = txt.replace(
    '.head(20)[["microrregiao", "idc_base", "idc_simulado"]]',
    '.head(20)[[coluna_visao_idc, "idc_base", "idc_simulado"]]'
)

txt = txt.replace(
    'id_vars="microrregiao"',
    'id_vars=coluna_visao_idc'
)

txt = txt.replace(
    'x="microrregiao"',
    'x=coluna_visao_idc'
)

txt = txt.replace(
    'title="Top 20 microrregiões — IDC Base x IDC Simulado"',
    'title=f"Top 20 {titulo_visao_idc} — IDC Base x IDC Simulado"'
)

txt = txt.replace(
    'title="Top 20 microrregiões — IDC simulado"',
    'title=f"Top 20 {titulo_visao_idc} — IDC simulado"'
)


# ============================================================
# 4) Corrigir DuplicateElementId colocando keys únicas nos gráficos
# ============================================================

lines = txt.splitlines()
comp_count = 0
sim_count = 0

for i, line in enumerate(lines):
    stripped = line.strip()
    indent_line = line[:len(line) - len(line.lstrip())]

    if stripped.startswith("st.plotly_chart(fig_comp"):
        comp_count += 1
        lines[i] = (
            indent_line
            + f"st.plotly_chart(fig_comp, use_container_width=True, "
            + f"key=f\"idc_base_x_simulado_{{st.session_state.get('idc_visao_simulador', 'micro')}}_{comp_count}\")"
        )

    if stripped.startswith("st.plotly_chart(fig_sim"):
        sim_count += 1
        lines[i] = (
            indent_line
            + f"st.plotly_chart(fig_sim, use_container_width=True, "
            + f"key=f\"idc_simulado_{{st.session_state.get('idc_visao_simulador', 'micro')}}_{sim_count}\")"
        )

txt = "\n".join(lines) + "\n"


path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ app.py corrigido:")
print("- Tabela com estado, região econômica, microrregião, município e cidade")
print("- Gráficos usando a visão selecionada")
print("- plotly_chart com keys únicas")
print(f"Backup criado em: {backup}")

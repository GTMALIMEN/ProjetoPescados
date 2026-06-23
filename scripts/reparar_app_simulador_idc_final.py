from pathlib import Path
import py_compile
import shutil
import re

app_path = Path("app.py")

def compila(path: Path) -> bool:
    try:
        py_compile.compile(str(path), doraise=True)
        return True
    except Exception:
        return False

# ============================================================
# 1) Se app.py estiver quebrado, restaurar último backup válido
# ============================================================

if not compila(app_path):
    broken_backup = app_path.with_suffix(".py.broken_simulador")
    shutil.copy2(app_path, broken_backup)
    print(f"⚠️ app.py atual estava quebrado. Backup do quebrado: {broken_backup}")

    backups = sorted(
        app_path.parent.glob("app.py.bak*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    restaurado = False

    for bk in backups:
        if compila(bk):
            shutil.copy2(bk, app_path)
            print(f"✅ Restaurado backup válido: {bk}")
            restaurado = True
            break

    if not restaurado:
        raise RuntimeError("Nenhum backup válido de app.py foi encontrado.")

txt = app_path.read_text(encoding="utf-8")

backup_final = app_path.with_suffix(".py.bak_reparo_final_simulador")
shutil.copy2(app_path, backup_final)

# ============================================================
# 2) Garantir colunas de localização depois da escolha de visão
# ============================================================

if "Garante colunas de localização para tabela e gráficos" not in txt:
    alvo = '''                # Garante pontos de venda total caso venha separado'''

    bloco = '''                # Garante colunas de localização para tabela e gráficos
                if "municipio" not in df_sim.columns and "cidade" in df_sim.columns:
                    df_sim["municipio"] = df_sim["cidade"]

                if "cidade" not in df_sim.columns and "municipio" in df_sim.columns:
                    df_sim["cidade"] = df_sim["municipio"]

                if "regiao_economica" not in df_sim.columns:
                    df_sim["regiao_economica"] = None

                if "microrregiao" not in df_sim.columns:
                    df_sim["microrregiao"] = None

'''

    if alvo in txt:
        txt = txt.replace(alvo, bloco + alvo)
    else:
        print("⚠️ Não encontrei o ponto exato para inserir colunas de localização; seguindo com demais ajustes.")

# ============================================================
# 3) Sobrescrever colunas da tabela antes de exibir o resultado
# ============================================================

if "# COLUNAS_RESULTADO_SIMULADOR_FINAL" not in txt:
    pattern = r'(?m)^(\s*)st\.markdown\("##### Resultado da simulação"\)'
    m = re.search(pattern, txt)

    if not m:
        raise RuntimeError('Não encontrei st.markdown("##### Resultado da simulação") no app.py')

    indent = m.group(1)

    bloco_cols = f'''{indent}# COLUNAS_RESULTADO_SIMULADOR_FINAL
{indent}cols_resultado = [
{indent}    "estado",
{indent}    "regiao_economica",
{indent}    "microrregiao",
{indent}    "municipio",
{indent}    "cidade",
{indent}    "idc_base",
{indent}    "idc_simulado",
{indent}    "diferenca_base_simulado",
{indent}    "classificacao_simulada",
{indent}    "pib",
{indent}    "pct_30_44",
{indent}    "pct_15_29",
{indent}    "pct_masculina",
{indent}    "pct_feminina",
{indent}    "restaurantes",
{indent}    "total_pdv",
{indent}    "pdv_total",
{indent}]
{indent}cols_resultado = [c for c in cols_resultado if c in df_sim.columns]

'''

    txt = txt[:m.start()] + bloco_cols + txt[m.start():]

# ============================================================
# 4) Ajustar apenas o bloco do Simulador IDC para usar visão dinâmica
# ============================================================

start = txt.find('st.markdown("#### Simulador de critérios IDC")')
end = txt.find('st.markdown("#### Exportar bases da Análise de Expansão")')

#ar apenas o bloco do Simulador IDC para usar visão dinâmica
# ============================================================

start = txt.find('st.markdown("#### Simulador de critérios IDC")')
end = txt.find('st.markdown("#### Exportar bases da Análise de Expansão")')

if start != -1 and end != -1 and end > start:
    bloco = txt[start:end]

    bloco = bloco.replace(
        '.head(20)[["microrregiao", "idc_base", "idc_simulado"]]',
        '.head(20)[[coluna_visao_idc, "idc_base", "idc_simulado"]]'
    )

    bloco = bloco.replace(
        'id_vars="microrregiao"',
        'id_vars=coluna_visao_idc'
    )

    bloco = bloco.replace(
        'x="microrregiao"',
        'x=coluna_visao_idc'
    )

    bloco = bloco.replace(
        'title="Top 20 microrregiões — IDC Base x IDC Simulado"',
        'title=f"Top 20 {titulo_visao_idc} — IDC Base x IDC Simulado"'
    )

    bloco = bloco.replace(
        'title="Top 20 microrregiões — IDC simulado"',
        'title=f"Top 20 {titulo_visao_idc} — IDC simulado"'
    )

    txt = txt[:start] + bloco + txt[end:]
else:
    print("⚠️ Não consegui isolar o bloco do Simulador IDC; não alterei eixos dos gráficos.")

# ============================================================
# 5) Corrigir DuplicateElementId dos Plotly Charts
# ============================================================

lines = txt.splitlines()
comp_count = 0
sim_count = 0

for i, line in enumerate(lines):
    stripped = line.strip()
    indent_line = line[:len(line) - len(line.lstrip())]

    if stripped.startswith("st.plotly_chart(fig_comp") and "key=" not in stripped:
        comp_count += 1
        lines[i] = (
            indent_line
            + "st.plotly_chart(fig_comp, use_container_width=True, "
            + f"key=f\"idc_base_x_simulado_{{st.session_state.get('idc_visao_simulador', 'micro')}}_{comp_count}\")"
        )

    if stripped.startswith("st.plotly_chart(fig_sim") and "key=" not in stripped:
        sim_count += 1
        lines[i] = (
            indent_line
            + "st.plotly_chart(fig_sim, use_container_width=True, "
            + f"key=f\"idc_simulado_{{st.session_state.get('idc_visao_simulador', 'micro')}}_{sim_count}\")"
        )

txt = "\n".join(lines) + "\n"

app_path.write_text(txt, encoding="utf-8")
py_compile.compile(str(app_path), doraise=True)

print("✅ app.py reparado e compilando.")
print("✅ Tabela do simulador terá região econômica, microrregião, município e cidade quando existirem.")
print("✅ Gráficos receberam keys únicas.")
print(f"Backup antes do reparo final: {backup_final}")

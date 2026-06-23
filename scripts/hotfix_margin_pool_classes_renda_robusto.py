from pathlib import Path
import py_compile
import shutil

path = Path("app.py")
backup = path.with_suffix(".py.bak_margin_pool_classes_renda_robusto")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")
lines = txt.splitlines()

# Localiza o bloco IDC / Margin Pool
idx_inicio = None
for i, line in enumerate(lines):
    if 'st.markdown("#### IDC / Margin Pool")' in line:
        idx_inicio = i
        break

if idx_inicio is None:
    raise RuntimeError('Não encontrei st.markdown("#### IDC / Margin Pool") no app.py.')

# Limite do bloco: até o próximo st.plotly_chart ou próximo markdown de seção
idx_fim = len(lines)
for i in range(idx_inicio + 1, len(lines)):
    if "st.plotly_chart" in lines[i] or ('st.markdown("#### ' in lines[i] and i > idx_inicio + 1):
        idx_fim = i
        break

# Localiza hover_data dentro desse bloco
idx_hover = None
for i in range(idx_inicio, idx_fim):
    if "hover_data=" in lines[i]:
        idx_hover = i
        break

if idx_hover is None:
    raise RuntimeError("Não encontrei hover_data dentro do bloco IDC / Margin Pool.")

indent = lines[idx_hover][:len(lines[idx_hover]) - len(lines[idx_hover].lstrip())]

# Descobre até onde vai o hover_data atual.
# Serve tanto para linha única quanto para bloco quebrado/multilinha.
idx_hover_fim = idx_hover

for j in range(idx_hover, min(idx_fim, idx_hover + 80)):
    if "if c in df_idc.columns]" in lines[j]:
        idx_hover_fim = j
        break
else:
    # fallback: se não achou list comprehension, termina na próxima linha que fecha parâmetro com ],
    for j in range(idx_hover, min(idx_fim, idx_hover + 80)):
        if lines[j].strip().endswith("],"):
            idx_hover_fim = j
            break

novo_hover = (
    indent
    + 'hover_data=[c for c in ['
    + '"idc_base", '
    + '"idc_macro", '
    + '"score", '
    + '"classificacao", '
    + '"Classe A", '
    + '"Classe B", '
    + '"Classe C", '
    + '"Classe D", '
    + '"Classe E", '
    + '"classe_renda", '
    + '"classe_renda_status", '
    + '"renda_per_capita_sm", '
    + '"renda_familiar_sm", '
    + '"criterio_classe_renda", '
    + '"participacao_populacao_pct", '
    + '"participacao_pib_pct", '
    + '"participacao_receita_pct", '
    + '"over_under_share_pct", '
    + '"margin_pool_pct", '
    + '"status_receita"'
    + '] if c in df_idc.columns],'
)

lines[idx_hover:idx_hover_fim + 1] = [novo_hover]

txt = "\n".join(lines) + "\n"
path.write_text(txt, encoding="utf-8")

py_compile.compile(str(path), doraise=True)

print("✅ app.py corrigido e compilando.")
print("✅ Classe A-E adicionadas ao hover do IDC / Margin Pool.")
print("✅ Backup criado em:", backup)

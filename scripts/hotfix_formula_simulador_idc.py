from pathlib import Path
import py_compile

app_path = Path("app.py")
txt = app_path.read_text(encoding="utf-8")

inicio = "# FORMULA_IDC_SIMULADOR_V3_INICIO"
fim = "# FORMULA_IDC_SIMULADOR_V3_FIM"

# Remove bloco antigo se já existir
if inicio in txt and fim in txt:
    start = txt.find(inicio)
    end = txt.find(fim, start) + len(fim)
    txt = txt[:start] + txt[end:]

formula = '''
# FORMULA_IDC_SIMULADOR_V3_INICIO
st.markdown(
    """
    ##### Fórmula aplicada no IDC Simulado

    **IDC Simulado =**  
    `(PIB × 25%) + (População 30–44 × 40%) + (População masculina × 10%) + (População feminina × 0%) + (Restaurantes × 10%) + (População 15–29 × 10%) + (Pontos de venda total × 5%)`

    **Observação:** todos os fatores são normalizados em escala **0–100** antes da aplicação dos pesos.  
    Itens que não estão nessa fórmula ficam com peso **0%** na simulação.
    """
)
# FORMULA_IDC_SIMULADOR_V3_FIM

'''

# Insere antes da função auxiliar do simulador
alvo = "def _num_col(df, col):"

pos = txt.find(alvo)

if pos == -1:
    raise RuntimeError("Não encontrei def _num_col(df, col): no app.py")

line_start = txt.rfind("\n", 0, pos) + 1
linha_alvo = txt[line_start:pos]
indent = linha_alvo[:len(linha_alvo) - len(linha_alvo.lstrip())]

formula_indentada = "\n".join(
    indent + linha if linha.strip() else ""
    for linha in formula.strip("\n").splitlines()
) + "\n\n"

txt = txt[:line_start] + formula_indentada + txt[line_start:]

app_path.write_text(txt, encoding="utf-8")
py_compile.compile(str(app_path), doraise=True)

print("✅ Fórmula do IDC Simulado inserida no app.py.")

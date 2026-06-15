from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
APP_PATH = ROOT_DIR / "app.py"


def replace_or_fail(text: str, pattern: str, repl: str, desc: str, flags=re.S) -> tuple[str, bool]:
    new_text, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n:
        print(f"OK  {desc}")
        return new_text, True
    print(f"AVISO não encontrou: {desc}")
    return text, False


def main() -> int:
    if not APP_PATH.exists():
        print(f"ERRO: app.py não encontrado em {APP_PATH}")
        return 1

    text = APP_PATH.read_text(encoding="utf-8")
    original = text

    # 1) Adiciona Todos no selectbox Estado base.
    # Funciona para chamadas em uma linha ou multilinha.
    pattern_select = (
        r'estado_base\s*=\s*st\.selectbox\(\s*["\']Estado base["\']\s*,\s*'
        r'\[[^\]]*["\']MG["\'][^\]]*["\']SP["\'][^\]]*["\']RJ["\'][^\]]*["\']ES["\'][^\]]*\]'
        r'\s*,\s*index\s*=\s*\d+'
    )
    repl_select = 'estado_base = st.selectbox("Estado base", ["Todos", "MG", "SP", "RJ", "ES"], index=1'
    text, ok_select = replace_or_fail(text, pattern_select, repl_select, "Estado base com opção Todos")

    # Caso muito específico, se já existir o trecho simples.
    if not ok_select:
        simple_old = 'estado_base = st.selectbox("Estado base", ["MG", "SP", "RJ", "ES"], index=0)'
        simple_new = 'estado_base = st.selectbox("Estado base", ["Todos", "MG", "SP", "RJ", "ES"], index=1)'
        if simple_old in text:
            text = text.replace(simple_old, simple_new, 1)
            ok_select = True
            print("OK  Estado base com opção Todos por replace simples")

    # 2) Garante que consultas carreguem todos os estados.
    pattern_estados = r'estados_exp\s*=\s*\[\s*estado_base\s*\]'
    repl_estados = 'estados_exp = ["MG", "SP", "RJ", "ES"] if estado_base == "Todos" else [estado_base]'
    text, ok_estados = replace_or_fail(text, pattern_estados, repl_estados, "estados_exp com Todos", flags=0)

    # 3) Garante que a função de municípios aceite Todos.
    # Troca somente a primeira ocorrência de estado=estado_base depois do carregamento de municípios.
    pattern_mun = (
        r'carregar_municipios_regiao_economica_expansao\(\s*\n'
        r'(\s*)estado\s*=\s*estado_base\s*,'
    )
    repl_mun = (
        r'carregar_municipios_regiao_economica_expansao(\n'
        r'\1estado=None if estado_base == "Todos" else estado_base,'
    )
    text, ok_mun = replace_or_fail(text, pattern_mun, repl_mun, "municípios com estado Todos")

    # 4) Evita título estranho do treemap quando Todos.
    pattern_title = r'title\s*=\s*f["\']Mapa comercial simplificado — \{estado_base\}["\']'
    repl_title = 'title="Mapa comercial simplificado — Sudeste" if estado_base == "Todos" else f"Mapa comercial simplificado — {estado_base}"'
    text, _ = replace_or_fail(text, pattern_title, repl_title, "título do mapa para Todos", flags=0)

    # 5) Métrica mais clara.
    text = text.replace('c1.metric("Estado selecionado", estado_base)', 'c1.metric("Seleção", estado_base)')

    # 6) Help mais claro.
    text = text.replace(
        'help="MG usa a Região Comercial MG. SP/RJ/ES usam a mesorregião IBGE como região econômica inicial."',
        'help="Todos carrega MG, SP, RJ e ES. MG usa a Região Comercial MG. SP/RJ/ES usam a mesorregião IBGE como região econômica inicial."'
    )

    # 7) Validação textual.
    if '["Todos", "MG", "SP", "RJ", "ES"]' not in text:
        print("ERRO: Não consegui inserir a opção Todos no app.py.")
        return 1

    if 'estado_base == "Todos"' not in text:
        print("ERRO: A opção Todos entrou, mas a regra de consulta não entrou.")
        return 1

    if text != original:
        backup = APP_PATH.with_suffix(".py.bak_estado_todos")
        if not backup.exists():
            backup.write_text(original, encoding="utf-8")
            print(f"Backup criado: {backup}")
        APP_PATH.write_text(text, encoding="utf-8")
        print("✅ app.py atualizado com Estado base = Todos.")
    else:
        print("✅ app.py já estava atualizado.")

    print("\nAgora pare o Streamlit com CTRL+C e rode novamente:")
    print(r'.\.venv\Scripts\python.exe -m streamlit run app.py')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

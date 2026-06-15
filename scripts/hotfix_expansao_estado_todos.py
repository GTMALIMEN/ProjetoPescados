from __future__ import annotations

from pathlib import Path
import re

ROOT_DIR = Path(__file__).resolve().parents[1]
APP_PATH = ROOT_DIR / "app.py"

def main() -> int:
    text = APP_PATH.read_text(encoding="utf-8")
    original = text

    text = re.sub(
        r'estado_base\s*=\s*st\.selectbox\(\s*(["\'])Estado base\1\s*,\s*\[[^\]]*["\']MG["\'][^\]]*["\']SP["\'][^\]]*["\']RJ["\'][^\]]*["\']ES["\'][^\]]*\]\s*,\s*index\s*=\s*\d+',
        'estado_base = st.selectbox("Estado base", ["Todos", "MG", "SP", "RJ", "ES"], index=1',
        text,
        count=1,
        flags=re.S,
    )

    text = re.sub(
        r'estados_exp\s*=\s*\[\s*estado_base\s*\]',
        'estados_exp = ["MG", "SP", "RJ", "ES"] if estado_base == "Todos" else [estado_base]',
        text,
        count=1,
    )

    text = re.sub(
        r'carregar_municipios_regiao_economica_expansao\(\s*\n(\s*)estado\s*=\s*estado_base\s*,',
        r'carregar_municipios_regiao_economica_expansao(\n\1estado=None if estado_base == "Todos" else estado_base,',
        text,
        count=1,
    )

    text = text.replace(
        'title=f"Mapa comercial simplificado — {estado_base}",',
        'title="Mapa comercial simplificado — Sudeste" if estado_base == "Todos" else f"Mapa comercial simplificado — {estado_base}",',
    )
    text = text.replace(
        'st.warning("Sem regiões econômicas para o estado selecionado.")',
        'st.warning("Sem regiões econômicas para a seleção.")',
    )
    text = text.replace(
        'c1.metric("Estado selecionado", estado_base)',
        'c1.metric("Seleção", estado_base)',
    )

    if '["Todos", "MG", "SP", "RJ", "ES"]' not in text:
        print("ERRO: não consegui inserir Todos no selectbox Estado base.")
        return 1
    if 'estado_base == "Todos"' not in text:
        print("ERRO: não consegui inserir a regra de consulta para Todos.")
        return 1

    if text != original:
        backup = APP_PATH.with_suffix(".py.bak_todos_expansao")
        if not backup.exists():
            backup.write_text(original, encoding="utf-8")
        APP_PATH.write_text(text, encoding="utf-8")
        print("✅ app.py atualizado: Estado base agora tem Todos.")
    else:
        print("✅ app.py já estava atualizado.")

    print("Pare o Streamlit com CTRL+C e abra de novo.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

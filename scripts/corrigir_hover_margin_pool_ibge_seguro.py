from __future__ import annotations

from pathlib import Path
import py_compile
import re
import shutil

APP = Path("app.py")


def compila(path: Path) -> bool:
    """Retorna True quando o arquivo Python compila sem erro."""
    try:
        py_compile.compile(str(path), doraise=True)
        return True
    except Exception:
        return False


def main() -> None:
    if not APP.exists():
        raise FileNotFoundError("app.py não encontrado.")

    if not compila(APP):
        raise RuntimeError("app.py não está compilando; corrija a sintaxe antes de aplicar este hotfix.")

    txt = APP.read_text(encoding="utf-8-sig")
    backup_ok = APP.with_suffix(".py.bak_hover_margin_pool_ibge_ok")
    shutil.copy2(APP, backup_ok)

    inicio = txt.find('st.markdown("#### IDC / Margin Pool")')
    if inicio == -1:
        raise RuntimeError('Não encontrei o bloco "#### IDC / Margin Pool" no app.py.')

    fim = txt.find("st.plotly_chart", inicio)
    if fim == -1:
        fim = inicio + 3000

    bloco = txt[inicio:fim]
    hover_novo = (
        'hover_data=[c for c in ['
        '"idc_base", "idc_macro", "score", "classificacao", '
        '"classe_populacao_ibge", "classe_populacao_ibge_ordem", '
        '"populacao", "regiao_economica", "fonte_renda", "fonte_demografia", '
        '"participacao_populacao_pct", "participacao_pib_pct", '
        '"participacao_receita_pct", "over_under_share_pct", '
        '"margin_pool_pct", "status_receita"'
        '] if c in df_idc.columns]'
    )

    padrao = r'hover_data=\[c for c in \[[^\]]*\] if c in df_idc\.columns\]'
    bloco_novo, n = re.subn(padrao, hover_novo, bloco, count=1, flags=re.S)
    if n == 0:
        print("Nenhum hover_data compatível encontrado; app.py mantido sem alteração.")
        return

    novo_txt = txt[:inicio] + bloco_novo + txt[fim:]
    APP.write_text(novo_txt, encoding="utf-8")
    py_compile.compile(str(APP), doraise=True)

    print("app.py corrigido e compilando.")
    print(f"Backup antes do ajuste seguro: {backup_ok}")


if __name__ == "__main__":
    main()

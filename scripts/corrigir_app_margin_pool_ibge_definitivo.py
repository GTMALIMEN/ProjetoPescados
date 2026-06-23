from pathlib import Path
import py_compile
import shutil
import re

APP = Path("app.py")

def compila(p: Path) -> bool:
    try:
        py_compile.compile(str(p), doraise=True)
        return True
    except Exception:
        return False

# Backup do estado atual, mesmo quebrado
shutil.copy2(APP, APP.with_suffix(".py.backup_antes_reparo_margin_pool"))

txt = APP.read_text(encoding="utf-8")

# Linha correta do hover_data do gráfico IDC / Margin Pool
hover_correto = (
    '                    hover_data=[c for c in ['
    '"idc_base", '
    '"idc_macro", '
    '"score", '
    '"classificacao", '
    '"classe_populacao_ibge", '
    '"classe_populacao_ibge_ordem", '
    '"populacao", '
    '"regiao_economica", '
    '"fonte_renda", '
    '"fonte_demografia", '
    '"participacao_populacao_pct", '
    '"participacao_pib_pct", '
    '"participacao_receita_pct", '
    '"over_under_share_pct", '
    '"margin_pool_pct", '
    '"status_receita"'
    '] if c in df_idc.columns],'
)

# Tenta corrigir diretamente o bloco quebrado do hover_data
inicio = txt.find('st.markdown("#### IDC / Margin Pool")')

if inicio == -1:
    raise RuntimeError('Não encontrei o bloco "#### IDC / Margin Pool" no app.py.')

fim = txt.find("st.plotly_chart", inicio)

if fim == -1:
    fim = inicio + 5000

bloco = txt[inicio:fim]

# Remove qualquer hover_data quebrado até o fechamento "if c in df_idc.columns],"
padrao_hover = r'(?ms)^(\s*)hover_data=.*?if c in df_idc\.columns\],'

bloco_novo, n = re.subn(
    padrao_hover,
    hover_correto,
    bloco,
    count=1
)

if n == 0:
    # Caso esteja em uma linha normal antiga
    linha_antiga = '                    hover_data=[c for c in ["idc_base", "idc_macro", "score", "classificacao", "participacao_populacao_pct", "participacao_pib_pct", "participacao_receita_pct", "over_under_share_pct", "margin_pool_pct", "status_receita"] if c in df_idc.columns],'
    if linha_antiga in bloco:
        bloco_novo = bloco.replace(linha_antiga, hover_correto, 1)
    else:
        raise RuntimeError("Não consegui localizar o hover_data do IDC / Margin Pool para corrigir.")

txt = txt[:inicio] + bloco_novo + txt[fim:]

APP.write_text(txt, encoding="utf-8")

# Se ainda estiver quebrado, tenta restaurar backup válido e aplicar troca simples
if not compila(APP):
    print("⚠️ Correção direta não compilou. Tentando restaurar backup válido...")

    quebrado = APP.with_suffix(".py.quebrado_margin_pool")
    shutil.copy2(APP, quebrado)

    backups = sorted(APP.parent.glob("app.py.bak*"), key=lambda p: p.stat().st_mtime, reverse=True)

    restaurado = False

    for bk in backups:
        if compila(bk):
            shutil.copy2(bk, APP)
            restaurado = True
            print(f"✅ Restaurado backup válido: {bk}")
            break

    if not restaurado:
        raise RuntimeError("Nenhum backup válido encontrado para app.py.")

    txt = APP.read_text(encoding="utf-8")
    inicio = txt.find('st.markdown("#### IDC / Margin Pool")')
    fim = txt.find("st.plotly_chart", inicio)

    if inicio == -1 or fim == -1:
        raise RuntimeError("Backup válido restaurado, mas não encontrei o bloco IDC / Margin Pool.")

    bloco = txt[inicio:fim]

    bloco_novo, n = re.subn(
        r'(?ms)^(\s*)hover_data=.*?if c in df_idc\.columns\],',
        hover_correto,
        bloco,
        count=1
    )

    if n == 0:
        raise RuntimeError("Não encontrei hover_data no backup restaurado.")

    txt = txt[:inicio] + bloco_novo + txt[fim:]
    APP.write_text(txt, encoding="utf-8")
    py_compile.compile(str(APP), doraise=True)

print("✅ app.py corrigido e compilando.")
print("✅ classe_populacao_ibge adicionada ao hover do gráfico IDC / Margin Pool.")
print("✅ Não rode mais scripts\\hotfix_margin_pool_classe_ibge.py antigo.")

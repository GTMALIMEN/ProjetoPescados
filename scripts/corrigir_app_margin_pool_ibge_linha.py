from pathlib import Path
import py_compile
import shutil

APP = Path("app.py")

def compila(p):
    try:
        py_compile.compile(str(p), doraise=True)
        return True
    except Exception:
        return False

# 1) Se app.py estiver quebrado, restaura o backup feito antes do patch ruim
if not compila(APP):
    quebrado = APP.with_suffix(".py.broken_hover_ibge")
    shutil.copy2(APP, quebrado)
    print(f"⚠️ app.py quebrado salvo em: {quebrado}")

    preferido = APP.with_suffix(".py.bak_margin_pool_classe_ibge")

    if preferido.exists() and compila(preferido):
        shutil.copy2(preferido, APP)
        print(f"✅ Restaurado backup anterior ao erro: {preferido}")
    else:
        backups = sorted(APP.parent.glob("app.py.bak*"), key=lambda x: x.stat().st_mtime, reverse=True)
        restaurado = False

        for bk in backups:
            if compila(bk):
                shutil.copy2(bk, APP)
                print(f"✅ Restaurado backup válido: {bk}")
                restaurado = True
                break

        if not restaurado:
            raise RuntimeError("Nenhum backup válido encontrado para app.py.")

txt = APP.read_text(encoding="utf-8")
shutil.copy2(APP, APP.with_suffix(".py.bak_margin_pool_ibge_linha_ok"))

# 2) Troca somente a linha hover_data do gráfico IDC / Margin Pool
linha_antiga = '                    hover_data=[c for c in ["idc_base", "idc_macro", "score", "classificacao", "participacao_populacao_pct", "participacao_pib_pct", "participacao_receita_pct", "over_under_share_pct", "margin_pool_pct", "status_receita"] if c in df_idc.columns],'

linha_nova = '                    hover_data=[c for c in ["idc_base", "idc_macro", "score", "classificacao", "classe_populacao_ibge", "classe_populacao_ibge_ordem", "populacao", "regiao_economica", "fonte_renda", "fonte_demografia", "participacao_populacao_pct", "participacao_pib_pct", "participacao_receita_pct", "over_under_share_pct", "margin_pool_pct", "status_receita"] if c in df_idc.columns],'

if linha_antiga not in txt:
    # Caso a linha esteja parecida, mas não exatamente igual, procura dentro do bloco IDC / Margin Pool.
    inicio = txt.find('st.markdown("#### IDC / Margin Pool")')
    fim = txt.find("st.plotly_chart", inicio)

    if inicio == -1 or fim == -1:
        raise RuntimeError("Não encontrei o bloco IDC / Margin Pool no app.py.")

    bloco = txt[inicio:fim]
    linhas = bloco.splitlines()
    alterou = False

    for i, l in enumerate(linhas):
        if "hover_data=[c for c in [" in l and "df_idc.columns" in l:
            indent = l[:len(l) - len(l.lstrip())]
            linhas[i] = indent + linha_nova.strip()
            alterou = True
            break

    if not alterou:
        raise RuntimeError("Não encontrei a linha hover_data dentro do bloco IDC / Margin Pool.")

    bloco_novo = "\n".join(linhas)
    txt = txt[:inicio] + bloco_novo + txt[fim:]
else:
    txt = txt.replace(linha_antiga, linha_nova, 1)

APP.write_text(txt, encoding="utf-8")
py_compile.compile(str(APP), doraise=True)

print("✅ app.py corrigido e compilando.")
print("✅ classe_populacao_ibge adicionada ao hover do IDC / Margin Pool.")

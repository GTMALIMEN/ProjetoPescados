from pathlib import Path
import py_compile
import shutil

path = Path("app.py")
backup = path.with_suffix(".py.bak_margin_pool_classes_renda")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

linha_antiga = '''                    hover_data=[c for c in ["idc_base", "idc_macro", "score", "classificacao", "participacao_populacao_pct", "participacao_pib_pct", "participacao_receita_pct", "over_under_share_pct", "margin_pool_pct", "status_receita"] if c in df_idc.columns],'''

linha_nova = '''                    hover_data=[c for c in ["idc_base", "idc_macro", "score", "classificacao", "Classe A", "Classe B", "Classe C", "Classe D", "Classe E", "classe_renda", "classe_renda_status", "renda_per_capita_sm", "renda_familiar_sm", "criterio_classe_renda", "participacao_populacao_pct", "participacao_pib_pct", "participacao_receita_pct", "over_under_share_pct", "margin_pool_pct", "status_receita"] if c in df_idc.columns],'''

if linha_antiga not in txt:
    raise RuntimeError("Não encontrei a linha hover_data antiga no app.py. Pare aqui e me mande o trecho da linha 668 até 676.")

txt = txt.replace(linha_antiga, linha_nova, 1)

path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ app.py corrigido e compilando.")
print("✅ Classes A-E adicionadas ao hover do IDC / Margin Pool.")
print("✅ Backup criado em:", backup)

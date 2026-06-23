from pathlib import Path
import re
import shutil
import py_compile

path = Path("src/services/expansao_service.py")

backup = path.with_suffix(".py.bak_indent_idc")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")
lines = txt.splitlines()

start = None
for i, line in enumerate(lines):
    if "# Compatibilidade IDC:" in line or 'if "idc_base" not in df.columns:' in line:
        start = i
        break

if start is None:
    for i, line in enumerate(lines):
        if 'df["over_under_share_pct"]' in line:
            start = i
            break

if start is None:
    raise RuntimeError("Não encontrei o bloco de IDC/over_under_share_pct para corrigir.")

end = None
for i in range(start + 1, len(lines)):
    if 'df["receita_esperada_idc"]' in lines[i]:
        end = i
        break

if end is None:
    raise RuntimeError('Não encontrei a linha df["receita_esperada_idc"] para delimitar o bloco.')

indent = re.match(r"^\s*", lines[end]).group(0)

novo_bloco = [
    '# Compatibilidade IDC:',
    '# A view nova usa idc_planejado/idc/idc_final/score_idc.',
    '# O código antigo ainda esperava idc_base.',
    'if "idc_base" not in df.columns:',
    '    for col_idc in ["idc_planejado", "idc_final", "idc", "score_idc", "score"]:',
    '        if col_idc in df.columns:',
    '            df["idc_base"] = pd.to_numeric(df[col_idc], errors="coerce").fillna(0)',
    '            break',
    '    else:',
    '        df["idc_base"] = 0',
    '',
    'if "participacao_receita_pct" not in df.columns:',
    '    df["participacao_receita_pct"] = 0',
    '',
    'df["over_under_share_pct"] = (',
    '    pd.to_numeric(df["participacao_receita_pct"], errors="coerce").fillna(0)',
    '    - pd.to_numeric(df["idc_base"], errors="coerce").fillna(0)',
    ')',
    ''
]

novo_bloco_indentado = [
    (indent + linha if linha else "")
    for linha in novo_bloco
]

lines[start:end] = novo_bloco_indentado

path.write_text("\n".join(lines) + "\n", encoding="utf-8")

py_compile.compile(str(path), doraise=True)

print("✅ Indentação corrigida em src/services/expansao_service.py")
print(f"Backup criado em: {backup}")

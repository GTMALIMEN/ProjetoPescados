from pathlib import Path
import py_compile

path = Path("scripts/carga_ibge_classes_renda_pof_6977.py")

txt = path.read_text(encoding="utf-8")

# Corrige corrupção de colagem
txt = txt.replace("SALARIO0.0", "SALARIO_MINIMO_REF")
txt = txt.replace("SALARIO_MINIMO_REF.0", "SALARIO_MINIMO_REF")
txt = txt.replace("SALARIO_ MINIMO_REF", "SALARIO_MINIMO_REF")

path.write_text(txt, encoding="utf-8")

py_compile.compile(str(path), doraise=True)

print("✅ carga_ibge_classes_renda_pof_6977.py corrigido e compilando.")

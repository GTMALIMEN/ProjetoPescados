from pathlib import Path
import sys
import re

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from src.database.connection import get_engine

# ============================================================
# 1) Corrige valores já gravados no banco
# ============================================================

sql = """
UPDATE app.fato_demografia_renda_municipio
SET
    renda_media = CASE
        WHEN renda_media > 20000 THEN renda_media / 100
        ELSE renda_media
    END,
    renda_mediana = CASE
        WHEN renda_mediana > 20000 THEN renda_mediana / 100
        ELSE renda_mediana
    END,
    fonte_renda = 'IBGE SIDRA Censo 2022 tabela 10295',
    data_atualizacao = NOW()
WHERE fonte_renda = 'IBGE SIDRA Censo 2022 tabela 10295'
  AND (
        renda_media > 20000
        OR renda_mediana > 20000
      );

UPDATE app.fato_expansao_municipio e
SET
    renda_media = d.renda_media,
    renda_mediana = d.renda_mediana,
    fonte_renda = 'IBGE SIDRA Censo 2022 tabela 10295',
    data_atualizacao = NOW()
FROM app.fato_demografia_renda_municipio d
WHERE e.codigo_ibge::text = d.codigo_ibge
  AND e.uf IN ('MG','SP','RJ','ES');
"""

with get_engine().begin() as conn:
    conn.execute(text(sql))

print("✅ Banco corrigido: renda SIDRA 10295 ajustada para escala correta.")

# ============================================================
# 2) Corrige o script de carga para não quebrar decimal novamente
# ============================================================

path = ROOT / "scripts" / "run_censo_2022_renda_oficial.py"

if path.exists():
    txt = path.read_text(encoding="utf-8")

    nova_funcao = r'''
def normalizar_valor(v):
    if v is None:
        return None

    s = str(v).strip()

    if s in {"", "-", "...", "X", "x"}:
        return None

    # SIDRA pode retornar:
    # 2748.85  -> decimal com ponto
    # 2.748,85 -> milhar com ponto e decimal com vírgula
    # 2748,85  -> decimal com vírgula
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    else:
        # Se tiver só ponto, mantém como decimal
        s = s

    try:
        return float(s)
    except Exception:
        return None
'''

    txt2 = re.sub(
        r"def normalizar_valor\(v\):.*?\n\ndef coletar_renda_municipio",
        nova_funcao + "\n\ndef coletar_renda_municipio",
        txt,
        flags=re.S
    )

    if txt2 != txt:
        path.write_text(txt2, encoding="utf-8")
        print("✅ Script run_censo_2022_renda_oficial.py corrigido.")
    else:
        print("⚠️ Não consegui substituir normalizar_valor automaticamente. Verifique o script.")
else:
    print("⚠️ Script run_censo_2022_renda_oficial.py não encontrado.")

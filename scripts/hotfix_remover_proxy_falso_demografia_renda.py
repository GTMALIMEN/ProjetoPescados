from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_DIR = ROOT / "src" / "database"
SCRIPTS_DIR = ROOT / "scripts"

# ============================================================
# 1) Encontrar automaticamente o SQL da Etapa 41
# ============================================================

candidatos = []

for path in DB_DIR.glob("*.sql"):
    txt = path.read_text(encoding="utf-8", errors="ignore")
    nome = path.name.lower()

    if (
        "vw_idc_completo_atual" in txt
        or "fato_mercado_privado" in txt
        or "Proxy automático: PIB per capita mensal" in txt
        or "IDC planejado" in txt
        or "etapa41" in nome
        or "etapas41" in nome
    ):
        candidatos.append(path)

if not candidatos:
    print("❌ Não encontrei nenhum SQL da Etapa 41.")
    print("Arquivos SQL encontrados em src/database:")
    for p in DB_DIR.glob("*.sql"):
        print(" -", p.name)
    raise SystemExit(1)

# Prioriza arquivo com 41 no nome; senão pega o que contém a view IDC.
candidatos = sorted(
    candidatos,
    key=lambda p: (
        0 if "41" in p.name.lower() else 1,
        0 if "vw_idc_completo_atual" in p.read_text(encoding="utf-8", errors="ignore") else 1,
        p.name
    )
)

sql_path = candidatos[0]
print(f"✅ SQL Etapa 41 encontrado: {sql_path.relative_to(ROOT)}")

txt = sql_path.read_text(encoding="utf-8", errors="ignore")

# ============================================================
# 2) Garantir DROP VIEW antes de CREATE OR REPLACE VIEW
# ============================================================

views_alvo = [
    "app.vw_importacao_manual_resumo",
    "app.vw_diagnostico_v2_plano",
    "app.vw_demografia_renda_municipio",
    "app.vw_pdv_proxy_municipio",
    "app.vw_comex_stat_status_atual",
    "app.vw_fontes_reais_cargas_sucesso",
    "app.vw_fontes_reais_cargas_erro",
    "app.vw_compra_manual_resumo",
    "app.vw_previa_vendedores_resumo",
    "app.vw_key_account_ibge",
    "app.vw_curva_mercado_categoria",
    "app.vw_mercado_privado_resumo",
    "app.vw_idc_completo_atual",
]

for path in DB_DIR.glob("*.sql"):
    t = path.read_text(encoding="utf-8", errors="ignore")
    original = t

    for view in views_alvo:
        create = f"CREATE OR REPLACE VIEW {view}"
        drop = f"DROP VIEW IF EXISTS {view} CASCADE;"

        if create in t:
            t = re.sub(
                rf"DROP VIEW IF EXISTS {re.escape(view)} CASCADE;\s*",
                "",
                t,
                flags=re.I,
            )
            t = t.replace(create, drop + "\n\n" + create)

    if t != original:
        path.write_text(t, encoding="utf-8")
        print(f"✅ DROP VIEW ajustado em: {path.relative_to(ROOT)}")

# Recarrega texto da Etapa 41 após ajustes gerais
txt = sql_path.read_text(encoding="utf-8", errors="ignore")

# ============================================================
# 3) Remover proxies falsos da Etapa 41
# ============================================================

def sub(pattern, repl, label):
    global txt
    txt2, n = re.subn(pattern, repl, txt, flags=re.S | re.I)
    txt = txt2
    print(f"{label}: {n} alteração(ões)")

# Não calcular renda_media como proxy
sub(
    r"renda_media\s*=\s*CASE\s+WHEN\s+renda_media\s+IS\s+NULL.*?ELSE\s+renda_media\s+END\s*,",
    "renda_media = renda_media,",
    "Remove proxy renda_media no UPDATE"
)

# Não marcar fonte como proxy
sub(
    r"fonte_renda\s*=\s*CASE\s+WHEN\s+fonte_renda\s+IS\s+NULL.*?ELSE\s+fonte_renda\s+END\s*,",
    "fonte_renda = COALESCE(fonte_renda, 'Pendente: IBGE Censo 2022/POF oficial'),",
    "Remove fonte_renda proxy"
)

# Não preencher sexo/faixa com default
repls = {
    "pct_masculina = COALESCE(pct_masculina, 49.0),": "pct_masculina = pct_masculina,",
    "pct_feminina = COALESCE(pct_feminina, 51.0),": "pct_feminina = pct_feminina,",
    "pct_0_14 = COALESCE(pct_0_14, 20.0),": "pct_0_14 = pct_0_14,",
    "pct_15_29 = COALESCE(pct_15_29, 23.0),": "pct_15_29 = pct_15_29,",
    "pct_30_44 = COALESCE(pct_30_44, 22.0),": "pct_30_44 = pct_30_44,",
    "pct_45_59 = COALESCE(pct_45_59, 18.0),": "pct_45_59 = pct_45_59,",
    "pct_60_plus = COALESCE(pct_60_plus, 17.0),": "pct_60_plus = pct_60_plus,",
}

for old, new in repls.items():
    if old in txt:
        txt = txt.replace(old, new)
        print(f"✅ Removido default fixo: {old}")

# Não preencher classes de renda por regra fixa
for classe in ["a", "b", "c", "de"]:
    sub(
        rf"renda_classe_{classe}\s*=\s*COALESCE\(\s*renda_classe_{classe}\s*,\s*CASE.*?END\s*\)\s*,",
        f"renda_classe_{classe} = renda_classe_{classe},",
        f"Remove proxy renda_classe_{classe}"
    )

sub(
    r"fonte_demografia\s*=\s*CASE\s+WHEN\s+fonte_demografia\s+IS\s+NULL.*?ELSE\s+fonte_demografia\s+END\s*,",
    "fonte_demografia = COALESCE(fonte_demografia, 'Pendente: IBGE Censo 2022 sexo/faixa etária oficial'),",
    "Remove fonte_demografia proxy"
)

# Corrigir a view IDC para não inventar 51/49 nem renda 900
txt = txt.replace(
    "COALESCE(e.pct_feminina, 51.0) AS pct_feminina,",
    "e.pct_feminina AS pct_feminina,"
)

txt = txt.replace(
    "COALESCE(e.pct_masculina, 49.0) AS pct_masculina,",
    "e.pct_masculina AS pct_masculina,"
)

sub(
    r"CASE\s+WHEN\s+e\.renda_media\s+IS\s+NOT\s+NULL\s+THEN\s+e\.renda_media\s+"
    r"WHEN\s+e\.populacao\s*>\s*0\s+AND\s+e\.pib\s+IS\s+NOT\s+NULL\s+THEN\s+LEAST\(GREATEST\(\(e\.pib\s*/\s*e\.populacao\)\s*/\s*12\s*\*\s*0\.38,\s*900\),\s*8500\)\s+"
    r"ELSE\s+NULL\s+END\s+AS\s+renda_media\s*,",
    "e.renda_media AS renda_media,",
    "Remove proxy renda na view IDC"
)

txt = txt.replace(
    "COALESCE(e.fonte_renda, 'Proxy automático: PIB per capita mensal × 0,38') AS fonte_renda,",
    "COALESCE(e.fonte_renda, 'Pendente: IBGE Censo 2022/POF oficial') AS fonte_renda,"
)

txt = txt.replace(
    "COALESCE(e.fonte_demografia, 'Proxy automático até carga Censo 2022') AS fonte_demografia,",
    "COALESCE(e.fonte_demografia, 'Pendente: IBGE Censo 2022 sexo/faixa etária oficial') AS fonte_demografia,"
)

# Validação
erros = []
for termo in [
    "COALESCE(pct_masculina, 49.0)",
    "COALESCE(pct_feminina, 51.0)",
    "COALESCE(e.pct_masculina, 49.0)",
    "COALESCE(e.pct_feminina, 51.0)",
]:
    if termo in txt:
        erros.append(termo)

if re.search(r"0\.38\s*,\s*900", txt):
    erros.append("renda proxy 0.38, 900")

if erros:
    print("❌ Ainda sobraram proxies falsos:")
    for e in erros:
        print(" -", e)
    raise SystemExit(1)

sql_path.write_text(txt, encoding="utf-8")
print("✅ Etapa 41 corrigida para não preencher 900 / 49 / 51.")

# ============================================================
# 4) Recriar apply_etapas41.py para usar o SQL encontrado
# ============================================================

apply_path = SCRIPTS_DIR / "apply_etapas41.py"

apply_code = f'''from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.database.connection import execute_sql_file

def main():
    sql_path = ROOT_DIR / "{sql_path.relative_to(ROOT).as_posix()}"
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL da Etapa 41 não encontrado: {{sql_path}}")

    execute_sql_file(str(sql_path))
    print("✅ Etapa 41 aplicada: importações persistentes, proxies controlados e IDC planejado.")

if __name__ == "__main__":
    main()
'''

apply_path.write_text(apply_code, encoding="utf-8")
print(f"✅ apply_etapas41.py recriado apontando para: {sql_path.relative_to(ROOT)}")

# ============================================================
# 5) Limpar valores falsos já gravados no banco
# ============================================================

from sqlalchemy import text
from src.database.connection import get_engine

sql = """
DROP VIEW IF EXISTS app.vw_key_account_ibge CASCADE;
DROP VIEW IF EXISTS app.vw_curva_mercado_categoria CASCADE;
DROP VIEW IF EXISTS app.vw_mercado_privado_resumo CASCADE;
DROP VIEW IF EXISTS app.vw_importacao_manual_resumo CASCADE;
DROP VIEW IF EXISTS app.vw_idc_completo_atual CASCADE;

UPDATE app.fato_expansao_municipio
SET
    renda_media = NULL,
    renda_classe_a = NULL,
    renda_classe_b = NULL,
    renda_classe_c = NULL,
    renda_classe_de = NULL,
    fonte_renda = 'Pendente: IBGE Censo 2022/POF oficial'
WHERE uf IN ('MG','SP','RJ','ES')
  AND (
        fonte_renda ILIKE '%Proxy automático%'
        OR renda_media = 900
      );

UPDATE app.fato_expansao_municipio
SET
    pct_masculina = NULL,
    pct_feminina = NULL,
    pct_0_14 = NULL,
    pct_15_29 = NULL,
    pct_30_44 = NULL,
    pct_45_59 = NULL,
    pct_60_plus = NULL,
    fonte_demografia = 'Pendente: IBGE Censo 2022 sexo/faixa etária oficial'
WHERE uf IN ('MG','SP','RJ','ES')
  AND (
        fonte_demografia ILIKE '%Proxy automático%'
        OR (pct_masculina = 49 AND pct_feminina = 51)
      );
"""

with get_engine().begin() as conn:
    conn.execute(text(sql))

print("✅ Banco limpo: renda 900 e sexo 49/51 removidos.")
print("✅ Agora esses campos ficam N/A até carga oficial IBGE/Censo.")

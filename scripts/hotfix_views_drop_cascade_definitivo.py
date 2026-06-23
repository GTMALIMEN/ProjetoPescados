from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DB_DIR = ROOT / "src" / "database"

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

alterados = []

for path in DB_DIR.glob("*.sql"):
    txt = path.read_text(encoding="utf-8")
    original = txt

    for view in views_alvo:
        create = f"CREATE OR REPLACE VIEW {view}"
        drop = f"DROP VIEW IF EXISTS {view} CASCADE;"

        if create in txt:
            # Remove drops duplicados antigos próximos ao create
            txt = re.sub(
                rf"DROP VIEW IF EXISTS {re.escape(view)} CASCADE;\s*",
                "",
                txt,
                flags=re.IGNORECASE,
            )

            txt = txt.replace(
                create,
                drop + "\n\n" + create
            )

    if txt != original:
        path.write_text(txt, encoding="utf-8")
        alterados.append(str(path.relative_to(ROOT)))

print("✅ SQLs corrigidos com DROP VIEW antes do CREATE OR REPLACE VIEW.")
for a in alterados:
    print(" -", a)

# Agora remove as views conflitantes do banco atual
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from src.database.connection import get_engine

sql_drop = "\n".join([f"DROP VIEW IF EXISTS {v} CASCADE;" for v in views_alvo])

with get_engine().begin() as conn:
    conn.execute(text(sql_drop))

print("✅ Views conflitantes removidas do banco atual.")

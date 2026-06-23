from pathlib import Path

# ============================================================
# 1) Corrigir src/database/importadores_manuais_v2.sql
# ============================================================

sql_path = Path("src/database/importadores_manuais_v2.sql")

txt = sql_path.read_text(encoding="utf-8")

drop_view = "DROP VIEW IF EXISTS app.vw_importacao_manual_resumo CASCADE;\n\n"

if "CREATE OR REPLACE VIEW app.vw_importacao_manual_resumo" in txt:
    if drop_view.strip() not in txt:
        txt = txt.replace(
            "CREATE OR REPLACE VIEW app.vw_importacao_manual_resumo",
            drop_view + "CREATE OR REPLACE VIEW app.vw_importacao_manual_resumo"
        )

sql_path.write_text(txt, encoding="utf-8")
print("✅ importadores_manuais_v2.sql corrigido.")


# ============================================================
# 2) Corrigir scripts/run_automaticas_sem_manuais.py
# ============================================================

run_path = Path("scripts/run_automaticas_sem_manuais.py")
txt = run_path.read_text(encoding="utf-8")

# Garante que a Etapa 41 seja reaplicada depois do init_db,
# porque o init_db pode recriar views antigas.
linha_init = 'run_py("scripts/init_db.py")'
linha_etapa41 = 'run_py("scripts/apply_etapas41.py", obrigatorio=False)'

if linha_init in txt and linha_etapa41 not in txt:
    txt = txt.replace(
        linha_init,
        linha_init + "\n" + linha_etapa41
    )

run_path.write_text(txt, encoding="utf-8")
print("✅ run_automaticas_sem_manuais.py corrigido para reaplicar Etapa 41 após init_db.")

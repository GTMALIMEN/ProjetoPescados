from pathlib import Path
import subprocess
import sys
import os

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / ".venv" / "Scripts" / "python.exe"
if not PY.exists():
    PY = Path(sys.executable)


def run_py(script, *args, obrigatorio=False):
    path = ROOT / script
    if not path.exists():
        print(f"⚠️ Script não existe: {script}")
        return
    print("\n" + "=" * 80)
    print("Rodando:", script, " ".join(args))
    print("=" * 80)
    r = subprocess.run([str(PY), script, *args], cwd=ROOT)
    if r.returncode != 0:
        print(f"⚠️ Falhou: {script} | código={r.returncode}")
        if obrigatorio:
            raise SystemExit(r.returncode)


def run_bat(script):
    path = ROOT / script
    if path.exists() and os.name == "nt":
        print("\n" + "=" * 80)
        print("Rodando BAT:", script)
        print("=" * 80)
        subprocess.run(["cmd", "/c", str(path)], cwd=ROOT)


print("Pipeline automático — sem bases manuais")
print("Bases manuais continuam via upload no app: Scanntech, Key Account, CEAGESP, Compra, Receita, Prévia.")

run_py("scripts/testar_conexao.py", obrigatorio=True)
run_py("scripts/init_db.py", obrigatorio=True)
run_py("scripts/apply_fontes_automaticas.py")
run_py("scripts/apply_expansao_v2_publica.py")
run_py("scripts/apply_etapas24_28.py")
run_py("scripts/apply_hotfix_expansao_receita_cepea.py")
run_py("scripts/apply_etapas41.py", obrigatorio=True)

run_py("scripts/run_ibge_localidades.py")
run_py("scripts/run_ibge_populacao.py")
run_py("scripts/run_expansao_publica.py", "--estados", "MG,SP,RJ,ES")
run_py("scripts/run_idh_automatico.py")
run_py("scripts/preencher_idh_faltantes_ibge.py")
run_py("scripts/run_pdv_proxy.py")
run_py("scripts/run_censo_demografico_2022.py")
run_py("scripts/apply_etapas41.py")

run_py("scripts/run_bcb_load.py")
run_bat("scripts/recarregar_fontes_2020_2026.bat")
run_py("scripts/hotfix_comex_fontes_reais.py")
run_py("scripts/run_comex_refinado.py")

run_py("scripts/calculate_indices_setoriais.py")
run_py("scripts/calculate_potencial.py")
run_py("scripts/calculate_scores.py")
run_py("scripts/generate_recommendations.py")
run_py("scripts/generate_active_alerts.py")
run_py("scripts/generate_executive_report.py", "--uf", "MG", "--usuario", "Marcos")
run_py("scripts/check_health.py")

run_py("scripts/diagnosticar_v2_plano.py")
run_py("scripts/check_db.py")
print("\n✅ Pipeline automático finalizado. Pendências manuais são resolvidas pela aba 📤 Importações Manuais.")

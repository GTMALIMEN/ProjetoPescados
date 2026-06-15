
from __future__ import annotations

from pathlib import Path
import py_compile
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]

ARQUIVOS_OBRIGATORIOS = [
    "app.py",
    "requirements.txt",
    "src/services/expansao_service.py",
    "src/services/previsao_mercado_service.py",
    "src/database/ceagesp_manual.sql",
    "scripts/init_db.py",
    "scripts/apply_fontes_automaticas.py",
    "scripts/apply_ceagesp_manual.py",
    "scripts/apply_expansao_v2_publica.py",
    "scripts/run_ibge_localidades.py",
    "scripts/run_ibge_populacao.py",
    "scripts/run_expansao_publica.py",
    "scripts/run_idh_automatico.py",
    "scripts/preencher_idh_faltantes_ibge.py",
    "scripts/diagnosticar_v2_plano.py",
    "scripts/criar_template_ceagesp_manual.py",
    "scripts/load_ceagesp_manual_file.py",
    "docs/ETAPAS24_28_IMPLEMENTACAO.md",
    "scripts/rodar_etapas24_28.bat",
    "scripts/criar_templates_etapas27_28.py",
    "scripts/run_comex_refinado.py",
    "scripts/run_pdv_proxy.py",
    "scripts/run_censo_demografico_2022.py",
    "scripts/apply_etapas24_28.py",
    "src/database/etapas24_28.sql",
    "scripts/preflight_drop_conflicting_views.py",
    "src/database/preflight_drop_conflicting_views.sql",
    "docs/FORMULAS_E_ONDE_SAO_APLICADAS.md",
    "docs/ETAPA23_EXPANSAO_REGIOES_E_FORMULAS.md",
]


def main():
    print("Validando integridade da Etapa 23...\n")
    ok = True

    for rel in ARQUIVOS_OBRIGATORIOS:
        path = ROOT_DIR / rel
        if path.exists():
            print(f"OK FILE {rel}")
        else:
            print(f"ERRO FILE {rel}")
            ok = False

    print("\nValidando sintaxe Python...")
    for path in ROOT_DIR.rglob("*.py"):
        if ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            print(f"ERRO PY {path.relative_to(ROOT_DIR)}: {exc}")
            ok = False

    app = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    checks = [
        ("2 abas principais", "area_expansao, area_previsao = st.tabs" in app),
        ("Aba Análise de Expansão", "🌎 Análise de Expansão" in app),
        ("Aba Análise Previsão", "📈 Análise Previsão de Mercado" in app),
        ("Seletor Estado base", "Estado base" in app),
        ("Seletor Região econômica", "Região econômica/comercial" in app),
    ]
    print("\nValidando app.py...")
    for name, result in checks:
        print(("OK" if result else "ERRO"), name)
        ok = ok and result

    service = (ROOT_DIR / "src/services/expansao_service.py").read_text(encoding="utf-8")
    service_checks = [
        ("carregar_regioes_economicas_expansao", "def carregar_regioes_economicas_expansao" in service),
        ("carregar_municipios_regiao_economica_expansao", "def carregar_municipios_regiao_economica_expansao" in service),
        ("regiao_economica", "regiao_economica" in service),
    ]
    print("\nValidando expansão_service.py...")
    for name, result in service_checks:
        print(("OK" if result else "ERRO"), name)
        ok = ok and result

    if not ok:
        print("\n❌ Validação encontrou problemas.")
        sys.exit(1)

    print("\n✅ Validação local da Etapa 23 concluída com sucesso.")


if __name__ == "__main__":
    main()

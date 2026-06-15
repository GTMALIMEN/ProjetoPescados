from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.services.health_service import (
    carregar_saude_sistema,
    carregar_resumo_fonte,
    carregar_erros_recentes,
    carregar_controle_carga,
)


def main():
    saude = carregar_saude_sistema()

    print("=== Saúde Geral do Sistema ===")
    for k, v in saude.items():
        print(f"- {k}: {v}")

    print("\n=== Resumo por Fonte/Status ===")
    df_resumo = carregar_resumo_fonte()
    if df_resumo.empty:
        print("Sem execuções registradas.")
    else:
        print(df_resumo.to_string(index=False))

    print("\n=== Erros Recentes ===")
    df_erros = carregar_erros_recentes()
    if df_erros.empty:
        print("Sem erros recentes.")
    else:
        print(df_erros.to_string(index=False))

    print("\n=== Últimos Controles de Carga ===")
    df_controle = carregar_controle_carga(limit=20)
    if df_controle.empty:
        print("Sem controles de carga.")
    else:
        print(df_controle[[
            "fonte", "indicador", "status", "qtd_raw", "qtd_staging", "qtd_dw",
            "qtd_rejeitados", "tempo_execucao_segundos", "data_execucao"
        ]].to_string(index=False))


if __name__ == "__main__":
    main()

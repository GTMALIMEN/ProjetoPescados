from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine


def scalar_or_zero(conn, sql: str):
    try:
        value = conn.execute(text(sql)).scalar()
        return value or 0
    except Exception:
        return 0


def regclass_exists(conn, name: str) -> bool:
    try:
        return bool(conn.execute(text("SELECT to_regclass(:name) IS NOT NULL"), {"name": name}).scalar())
    except Exception:
        return False


def main():
    engine = get_engine()

    with engine.begin() as conn:
        print("✅ Conexão OK")

        tables = conn.execute(text("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema IN ('raw', 'staging', 'dw', 'app', 'ml')
            ORDER BY table_schema, table_name
        """)).fetchall()

        print("\nTabelas encontradas:")
        for row in tables:
            print(f"- {row.table_schema}.{row.table_name}")

        # ------------------------------------------------------------
        # Séries BCB
        # ------------------------------------------------------------
        total_series = scalar_or_zero(conn, "SELECT COUNT(*) FROM dw.fato_serie_historica")
        print(f"\nRegistros em dw.fato_serie_historica: {total_series}")

        if total_series:
            rows = conn.execute(text("""
                SELECT indicador, COUNT(*) AS qtd
                FROM dw.fato_serie_historica
                GROUP BY indicador
                ORDER BY indicador
            """)).fetchall()

            print("\nRegistros por indicador:")
            for row in rows:
                print(f"- {row.indicador}: {row.qtd}")

        # ------------------------------------------------------------
        # Geografia
        # ------------------------------------------------------------
        if regclass_exists(conn, "dw.dim_geografia"):
            total_geo = scalar_or_zero(conn, "SELECT COUNT(*) FROM dw.dim_geografia")
            total_mg_regiao = scalar_or_zero(
                conn,
                "SELECT COUNT(*) FROM dw.dim_geografia WHERE uf = 'MG' AND regiao_comercial IS NOT NULL"
            )

            print(f"\nMunicípios em dw.dim_geografia: {total_geo}")
            print(f"Municípios MG com região comercial: {total_mg_regiao}")

            rows = conn.execute(text("""
                SELECT uf, COUNT(*) AS qtd
                FROM dw.dim_geografia
                GROUP BY uf
                ORDER BY uf
            """)).fetchall()

            print("\nMunicípios por UF:")
            for row in rows:
                print(f"- {row.uf}: {row.qtd}")

            rows = conn.execute(text("""
                SELECT regiao_comercial, COUNT(*) AS qtd
                FROM dw.dim_geografia
                WHERE uf = 'MG'
                  AND regiao_comercial IS NOT NULL
                GROUP BY regiao_comercial
                ORDER BY regiao_comercial
            """)).fetchall()

            print("\nRegiões comerciais de MG:")
            for row in rows:
                print(f"- {row.regiao_comercial}: {row.qtd}")

        # ------------------------------------------------------------
        # Potencial regional
        # ------------------------------------------------------------
        if regclass_exists(conn, "dw.fato_indicador_municipal"):
            total_ind_mun = scalar_or_zero(conn, "SELECT COUNT(*) FROM dw.fato_indicador_municipal")
            print(f"\nRegistros em dw.fato_indicador_municipal: {total_ind_mun}")

        if regclass_exists(conn, "app.fato_potencial_regional"):
            total_pot = scalar_or_zero(conn, "SELECT COUNT(*) FROM app.fato_potencial_regional")
            print(f"Registros em app.fato_potencial_regional: {total_pot}")

            mv_pot_exists = regclass_exists(conn, "app.mv_potencial_regional_atual")
            print(f"Materialized view app.mv_potencial_regional_atual existe: {mv_pot_exists}")

            if mv_pot_exists:
                rows = conn.execute(text("""
                    SELECT
                        regiao_comercial,
                        score_potencial,
                        cenario_1_10,
                        confianca
                    FROM app.mv_potencial_regional_atual
                    WHERE uf = 'MG'
                    ORDER BY score_potencial DESC
                """)).fetchall()

                print("\nPotencial regional atual MG:")
                for row in rows:
                    print(
                        f"- {row.regiao_comercial}: "
                        f"potencial={row.score_potencial:.2f}, "
                        f"cenário={row.cenario_1_10}, "
                        f"confiança={row.confianca:.2f}"
                    )

        # ------------------------------------------------------------
        # Vendas
        # ------------------------------------------------------------
        if regclass_exists(conn, "dw.fato_vendas"):
            total_vendas = scalar_or_zero(conn, "SELECT COUNT(*) FROM dw.fato_vendas")
            print(f"\nRegistros em dw.fato_vendas: {total_vendas}")

            if total_vendas:
                resumo = conn.execute(text("""
                    SELECT
                        COALESCE(SUM(valor_venda), 0) AS faturamento,
                        COALESCE(SUM(volume_kg), 0) AS volume_kg,
                        COUNT(DISTINCT id_cliente) AS clientes,
                        COUNT(DISTINCT id_produto) AS produtos
                    FROM dw.fato_vendas
                """)).mappings().first()

                print("Resumo vendas:")
                print(f"- Faturamento: {float(resumo['faturamento']):.2f}")
                print(f"- Volume KG: {float(resumo['volume_kg']):.2f}")
                print(f"- Clientes: {resumo['clientes']}")
                print(f"- Produtos: {resumo['produtos']}")

        # ------------------------------------------------------------
        # Scores regionais
        # ------------------------------------------------------------
        if regclass_exists(conn, "app.fato_score_regional"):
            total_scores = scalar_or_zero(conn, "SELECT COUNT(*) FROM app.fato_score_regional")
            print(f"\nRegistros em app.fato_score_regional: {total_scores}")

            if total_scores and regclass_exists(conn, "app.mv_score_regional_atual"):
                rows = conn.execute(text("""
                    SELECT
                        regiao_comercial,
                        score_final,
                        score_oportunidade,
                        score_risco,
                        COALESCE(score_potencial, 0) AS score_potencial,
                        COALESCE(score_setorial, 0) AS score_setorial,
                        COALESCE(score_competitividade_setorial, 0) AS score_competitividade_setorial,
                        COALESCE(score_pressao_custo_setorial, 0) AS score_pressao_custo_setorial,
                        COALESCE(score_risco_substituicao_setorial, 0) AS score_risco_substituicao_setorial,
                        cenario_1_10,
                        confianca,
                        metodo
                    FROM app.mv_score_regional_atual
                    WHERE uf = 'MG'
                    ORDER BY score_final DESC
                """)).fetchall()

                print("\nScores atuais:")
                for row in rows:
                    print(
                        f"- {row.regiao_comercial}: "
                        f"score={row.score_final:.2f}, "
                        f"oportunidade={row.score_oportunidade:.2f}, "
                        f"risco={row.score_risco:.2f}, "
                        f"potencial={row.score_potencial:.2f}, "
                        f"setorial={row.score_setorial:.2f}, "
                        f"comp={row.score_competitividade_setorial:.2f}, "
                        f"custo={row.score_pressao_custo_setorial:.2f}, "
                        f"subst={row.score_risco_substituicao_setorial:.2f}, "
                        f"cenário={row.cenario_1_10}, "
                        f"confiança={row.confianca:.2f}, "
                        f"método={row.metodo}"
                    )

        # ------------------------------------------------------------
        # Recomendações
        # ------------------------------------------------------------
        if regclass_exists(conn, "app.fato_recomendacao"):
            total_recs = scalar_or_zero(conn, "SELECT COUNT(*) FROM app.fato_recomendacao")
            print(f"\nRegistros em app.fato_recomendacao: {total_recs}")

            if total_recs and regclass_exists(conn, "app.mv_recomendacao_atual"):
                rows = conn.execute(text("""
                    SELECT
                        regiao_comercial,
                        tipo_recomendacao,
                        COALESCE(motor_decisao, 'N/A') AS motor_decisao,
                        COALESCE(score_potencial, 0) AS score_potencial,
                        COALESCE(score_setorial, 0) AS score_setorial,
                        COALESCE(score_competitividade_setorial, 0) AS score_competitividade_setorial,
                        COALESCE(score_pressao_custo_setorial, 0) AS score_pressao_custo_setorial,
                        COALESCE(score_risco_substituicao_setorial, 0) AS score_risco_substituicao_setorial,
                        acao_sugerida,
                        cenario_1_10,
                        confianca,
                        roi_estimado
                    FROM app.mv_recomendacao_atual
                    WHERE uf = 'MG'
                    ORDER BY cenario_1_10 DESC, score_potencial DESC, confianca DESC, regiao_comercial
                """)).fetchall()

                print("\nRecomendações atuais:")
                for row in rows:
                    roi_txt = "N/A" if row.roi_estimado is None else f"{row.roi_estimado:.2f}%"
                    print(
                        f"- {row.regiao_comercial}: "
                        f"{row.tipo_recomendacao} | "
                        f"motor={row.motor_decisao} | "
                        f"potencial={row.score_potencial:.2f} | "
                        f"setorial={row.score_setorial:.2f} | "
                        f"comp={row.score_competitividade_setorial:.2f} | "
                        f"custo={row.score_pressao_custo_setorial:.2f} | "
                        f"subst={row.score_risco_substituicao_setorial:.2f} | "
                        f"cenário={row.cenario_1_10} | "
                        f"confiança={row.confianca:.2f} | "
                        f"ROI={roi_txt} | "
                        f"ação={row.acao_sugerida}"
                    )

        # ------------------------------------------------------------
        # Saúde
        # ------------------------------------------------------------
        print("\nResumo saúde do sistema:")
        if regclass_exists(conn, "app.vw_saude_sistema"):
            try:
                saude = conn.execute(text("SELECT * FROM app.vw_saude_sistema")).mappings().first()
                for k, v in dict(saude or {}).items():
                    print(f"- {k}: {v}")
            except Exception as exc:
                print(f"- Não foi possível ler app.vw_saude_sistema: {exc}")

        # ------------------------------------------------------------
        # Setorial
        # ------------------------------------------------------------
        if regclass_exists(conn, "dw.fato_indicador_setorial"):
            total_setorial = scalar_or_zero(conn, "SELECT COUNT(*) FROM dw.fato_indicador_setorial")
            print(f"\nRegistros em dw.fato_indicador_setorial: {total_setorial}")

        if regclass_exists(conn, "app.fato_indice_setorial"):
            total_indices = scalar_or_zero(conn, "SELECT COUNT(*) FROM app.fato_indice_setorial")
            print(f"Registros em app.fato_indice_setorial: {total_indices}")

        if regclass_exists(conn, "app.fato_alerta_setorial"):
            total_alertas = scalar_or_zero(conn, "SELECT COUNT(*) FROM app.fato_alerta_setorial")
            print(f"Registros em app.fato_alerta_setorial: {total_alertas}")

        if regclass_exists(conn, "app.mv_indice_setorial_atual"):
            rows = conn.execute(text("""
                SELECT uf, indice, score, cenario_1_10, confianca
                FROM app.mv_indice_setorial_atual
                ORDER BY indice
            """)).fetchall()

            if rows:
                print("\nÍndices setoriais atuais:")
                for row in rows:
                    print(
                        f"- {row.uf} | {row.indice}: "
                        f"score={row.score:.2f}, cenário={row.cenario_1_10}, confiança={row.confianca:.2f}"
                    )

        if regclass_exists(conn, "app.fato_simulacao_whatif"):
            total_whatif = scalar_or_zero(conn, "SELECT COUNT(*) FROM app.fato_simulacao_whatif")
            print(f"\nRegistros em app.fato_simulacao_whatif: {total_whatif}")

            if total_whatif:
                rows = conn.execute(text("""
                    SELECT
                        data_simulacao,
                        regiao_comercial,
                        nome_cenario,
                        score_atual,
                        score_simulado,
                        delta_score,
                        recomendacao_simulada,
                        motor_decisao_simulado
                    FROM app.vw_whatif_ultimas_simulacoes
                    LIMIT 5
                """)).fetchall()

                print("\nÚltimas simulações What-if:")
                for row in rows:
                    print(
                        f"- {row.data_simulacao} | {row.regiao_comercial} | {row.nome_cenario}: "
                        f"{row.score_atual:.2f} → {row.score_simulado:.2f} "
                        f"(delta={row.delta_score:.2f}) | "
                        f"{row.recomendacao_simulada} | motor={row.motor_decisao_simulado}"
                    )

        if regclass_exists(conn, "app.fato_alerta_ativo"):
            total_alertas_ativos = scalar_or_zero(conn, "SELECT COUNT(*) FROM app.fato_alerta_ativo")
            print(f"\nRegistros em app.fato_alerta_ativo: {total_alertas_ativos}")

            if total_alertas_ativos:
                rows = conn.execute(text("""
                    SELECT
                        area_responsavel,
                        severidade,
                        status,
                        COUNT(*) AS qtd
                    FROM app.fato_alerta_ativo
                    GROUP BY area_responsavel, severidade, status
                    ORDER BY area_responsavel, severidade, status
                """)).fetchall()

                print("\nResumo alertas ativos:")
                for row in rows:
                    print(f"- {row.area_responsavel} | {row.severidade} | {row.status}: {row.qtd}")

                recentes = conn.execute(text("""
                    SELECT
                        id,
                        regiao_comercial,
                        area_responsavel,
                        tipo_alerta,
                        severidade,
                        status,
                        score_relacionado,
                        titulo
                    FROM app.vw_alertas_historico_recente
                    LIMIT 10
                """)).fetchall()

                print("\nÚltimos alertas:")
                for row in recentes:
                    print(
                        f"- #{row.id} | {row.regiao_comercial} | {row.area_responsavel} | "
                        f"{row.tipo_alerta} | {row.severidade} | {row.status} | "
                        f"score={row.score_relacionado} | {row.titulo}"
                    )

        if regclass_exists(conn, "app.fato_relatorio_executivo"):
            total_relatorios = scalar_or_zero(conn, "SELECT COUNT(*) FROM app.fato_relatorio_executivo")
            print(f"\nRegistros em app.fato_relatorio_executivo: {total_relatorios}")

            if total_relatorios:
                rows = conn.execute(text("""
                    SELECT
                        id,
                        data_geracao,
                        uf,
                        titulo,
                        status,
                        caminho_excel,
                        caminho_html
                    FROM app.vw_relatorios_executivos_recentes
                    LIMIT 5
                """)).fetchall()

                print("\nRelatórios executivos recentes:")
                for row in rows:
                    print(
                        f"- #{row.id} | {row.data_geracao} | {row.uf} | "
                        f"{row.status} | Excel={row.caminho_excel} | HTML={row.caminho_html}"
                    )

        if regclass_exists(conn, "app.pipeline_execucao"):
            total_pipeline = scalar_or_zero(conn, "SELECT COUNT(*) FROM app.pipeline_execucao")
            print(f"\nRegistros em app.pipeline_execucao: {total_pipeline}")

            if total_pipeline:
                rows = conn.execute(text("""
                    SELECT
                        pipeline_id,
                        status,
                        iniciado_em,
                        finalizado_em,
                        tempo_total_segundos,
                        usuario,
                        mensagem
                    FROM app.vw_pipeline_ultimas_execucoes
                    LIMIT 5
                """)).fetchall()

                print("\nÚltimas execuções de pipeline:")
                for row in rows:
                    print(
                        f"- {row.pipeline_id} | {row.status} | "
                        f"início={row.iniciado_em} | fim={row.finalizado_em} | "
                        f"tempo={row.tempo_total_segundos} | usuário={row.usuario} | {row.mensagem}"
                    )

                etapas = conn.execute(text("""
                    SELECT
                        status,
                        COUNT(*) AS qtd
                    FROM app.pipeline_etapa_execucao
                    GROUP BY status
                    ORDER BY status
                """)).fetchall()

                print("\nResumo etapas pipeline:")
                for row in etapas:
                    print(f"- {row.status}: {row.qtd}")

        # ------------------------------------------------------------
        # Fontes reais
        # ------------------------------------------------------------
        print("\nResumo fontes reais setoriais:")
        if regclass_exists(conn, "app.vw_fontes_reais_setoriais"):
            rows = conn.execute(text("""
                SELECT fonte, qtd_registros, qtd_indicadores, qtd_produtos, primeira_data, ultima_data
                FROM app.vw_fontes_reais_setoriais
                ORDER BY fonte
            """)).fetchall()

            if not rows:
                print("- Nenhuma fonte real carregada.")

            for row in rows:
                print(
                    f"- {row.fonte}: registros={row.qtd_registros}, "
                    f"indicadores={row.qtd_indicadores}, produtos={row.qtd_produtos}, "
                    f"período={row.primeira_data} até {row.ultima_data}"
                )


if __name__ == "__main__":
    main()

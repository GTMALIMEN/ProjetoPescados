
-- ============================================================
-- Preflight — derrubar views antigas conflitantes
-- ============================================================
-- Motivo:
-- PostgreSQL não permite CREATE OR REPLACE VIEW quando a nova definição
-- muda nome/ordem de colunas da view existente.
--
-- Exemplo do erro:
-- "não é possível alterar o nome da coluna uf da visão para fonte"
--
-- Solução:
-- Derrubar views/materialized views antigas antes de recriar a estrutura.
-- CASCADE é usado porque as views serão recriadas em seguida pelo init_db.

DROP VIEW IF EXISTS app.vw_indicador_setorial_mensal CASCADE;
DROP VIEW IF EXISTS app.vw_saude_setorial CASCADE;

DROP VIEW IF EXISTS app.vw_etl_ultimas_execucoes CASCADE;
DROP VIEW IF EXISTS app.vw_etl_resumo_fonte_historico CASCADE;
DROP VIEW IF EXISTS app.vw_etl_controle_carga CASCADE;
DROP VIEW IF EXISTS app.vw_etl_status_atual CASCADE;
DROP VIEW IF EXISTS app.vw_etl_resumo_fonte CASCADE;
DROP VIEW IF EXISTS app.vw_etl_erros_ativos CASCADE;
DROP VIEW IF EXISTS app.vw_data_quality_resumo CASCADE;
DROP VIEW IF EXISTS app.vw_saude_sistema CASCADE;

DROP VIEW IF EXISTS app.vw_pipeline_ultimas_execucoes CASCADE;
DROP VIEW IF EXISTS app.vw_pipeline_etapas_recentes CASCADE;
DROP VIEW IF EXISTS app.vw_pipeline_saude CASCADE;

DROP VIEW IF EXISTS app.vw_diagnostico_v2_plano CASCADE;
DROP VIEW IF EXISTS app.vw_ceagesp_pescados_historico CASCADE;

DROP MATERIALIZED VIEW IF EXISTS app.mv_indice_setorial_atual CASCADE;
DROP MATERIALIZED VIEW IF EXISTS app.mv_alerta_setorial_atual CASCADE;
DROP MATERIALIZED VIEW IF EXISTS app.mv_score_regional_atual CASCADE;
DROP MATERIALIZED VIEW IF EXISTS app.mv_recomendacao_atual CASCADE;
DROP MATERIALIZED VIEW IF EXISTS app.mv_potencial_regional_atual CASCADE;
DROP MATERIALIZED VIEW IF EXISTS app.mv_vendas_mensal_geo CASCADE;

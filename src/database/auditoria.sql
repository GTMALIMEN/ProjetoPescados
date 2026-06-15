-- Preflight auditoria views
DROP VIEW IF EXISTS app.vw_etl_ultimas_execucoes CASCADE;
DROP VIEW IF EXISTS app.vw_etl_resumo_fonte_historico CASCADE;
DROP VIEW IF EXISTS app.vw_etl_controle_carga CASCADE;
DROP VIEW IF EXISTS app.vw_etl_status_atual CASCADE;
DROP VIEW IF EXISTS app.vw_etl_resumo_fonte CASCADE;
DROP VIEW IF EXISTS app.vw_etl_erros_ativos CASCADE;
DROP VIEW IF EXISTS app.vw_data_quality_resumo CASCADE;
DROP VIEW IF EXISTS app.vw_saude_sistema CASCADE;

-- ============================================================
-- Radar Pescados IA — Etapa 8.3
-- Saúde do Sistema / ETL / Auditoria
-- Correção: recria views em ordem segura para evitar conflito de colunas.
-- ============================================================

-- PostgreSQL não permite CREATE OR REPLACE VIEW quando muda nome/ordem de colunas.
-- Por isso, removemos as views dependentes antes de recriar.
DROP VIEW IF EXISTS app.vw_saude_sistema CASCADE;
DROP VIEW IF EXISTS app.vw_etl_erros_ativos CASCADE;
DROP VIEW IF EXISTS app.vw_etl_resumo_fonte CASCADE;
DROP VIEW IF EXISTS app.vw_etl_status_atual CASCADE;
DROP VIEW IF EXISTS app.vw_data_quality_resumo CASCADE;
DROP VIEW IF EXISTS app.vw_etl_controle_carga CASCADE;
DROP VIEW IF EXISTS app.vw_etl_resumo_fonte_historico CASCADE;
DROP VIEW IF EXISTS app.vw_etl_ultimas_execucoes CASCADE;

CREATE VIEW app.vw_etl_ultimas_execucoes AS
SELECT
    r.run_id,
    r.fonte,
    r.tipo_execucao,
    r.ambiente,
    r.status,
    r.iniciado_em,
    r.finalizado_em,
    EXTRACT(EPOCH FROM (COALESCE(r.finalizado_em, NOW()) - r.iniciado_em))::NUMERIC(12,2) AS duracao_segundos,
    r.mensagem
FROM app.etl_run r
ORDER BY r.iniciado_em DESC;

CREATE VIEW app.vw_etl_resumo_fonte_historico AS
SELECT
    fonte,
    status,
    COUNT(*) AS qtd_execucoes,
    MAX(iniciado_em) AS ultima_execucao,
    AVG(EXTRACT(EPOCH FROM (COALESCE(finalizado_em, NOW()) - iniciado_em)))::NUMERIC(12,2) AS duracao_media_segundos
FROM app.etl_run
GROUP BY fonte, status
ORDER BY fonte, status;

CREATE VIEW app.vw_etl_controle_carga AS
SELECT
    c.id,
    c.run_id,
    c.fonte,
    c.indicador,
    c.codigo_serie,
    c.status,
    c.mensagem,
    c.qtd_registros,
    c.qtd_raw,
    c.qtd_staging,
    c.qtd_dw,
    c.qtd_rejeitados,
    c.tempo_execucao_segundos,
    c.data_execucao
FROM app.etl_controle_carga c
ORDER BY c.data_execucao DESC;

-- Status atual por fonte/indicador.
-- Usa somente a última carga de cada combinação, evitando que erros corrigidos apareçam como erro ativo.
CREATE VIEW app.vw_etl_status_atual AS
WITH ranked AS (
    SELECT
        c.*,
        ROW_NUMBER() OVER (
            PARTITION BY c.fonte, COALESCE(c.indicador, ''), COALESCE(c.codigo_serie, '')
            ORDER BY c.data_execucao DESC, c.id DESC
        ) AS rn
    FROM app.etl_controle_carga c
)
SELECT
    id,
    run_id,
    fonte,
    indicador,
    codigo_serie,
    status,
    status AS status_atual,
    mensagem,
    qtd_registros,
    qtd_raw,
    qtd_staging,
    qtd_dw,
    qtd_rejeitados,
    tempo_execucao_segundos,
    data_execucao
FROM ranked
WHERE rn = 1
ORDER BY fonte, indicador;

CREATE VIEW app.vw_etl_resumo_fonte AS
SELECT
    fonte,
    status,
    COUNT(*) AS qtd_execucoes,
    MAX(data_execucao) AS ultima_execucao,
    AVG(COALESCE(tempo_execucao_segundos, 0))::NUMERIC(12,2) AS duracao_media_segundos
FROM app.vw_etl_status_atual
GROUP BY fonte, status
ORDER BY fonte, status;

CREATE VIEW app.vw_etl_erros_ativos AS
SELECT
    id,
    run_id,
    fonte,
    indicador,
    codigo_serie,
    status,
    status_atual,
    mensagem,
    qtd_raw,
    qtd_staging,
    qtd_dw,
    qtd_rejeitados,
    tempo_execucao_segundos,
    data_execucao
FROM app.vw_etl_status_atual
WHERE status <> 'SUCESSO'
ORDER BY data_execucao DESC;

CREATE VIEW app.vw_data_quality_resumo AS
SELECT
    fonte,
    tabela,
    regra,
    status,
    COUNT(*) AS qtd_validacoes,
    SUM(COALESCE(qtd_linhas_afetadas, 0)) AS linhas_afetadas,
    MAX(data_validacao) AS ultima_validacao
FROM app.data_quality_resultado
GROUP BY fonte, tabela, regra, status
ORDER BY ultima_validacao DESC;

CREATE VIEW app.vw_saude_sistema AS
SELECT
    (SELECT COUNT(*) FROM dw.fato_serie_historica) AS qtd_series_historicas,
    (SELECT COUNT(*) FROM dw.dim_geografia) AS qtd_municipios,
    (SELECT COUNT(*) FROM dw.fato_indicador_municipal) AS qtd_indicadores_municipais,
    (SELECT COUNT(*) FROM dw.fato_vendas) AS qtd_vendas,
    (SELECT COUNT(*) FROM app.fato_score_regional) AS qtd_scores,
    (SELECT COUNT(*) FROM app.fato_recomendacao) AS qtd_recomendacoes,
    (SELECT COUNT(*) FROM app.fato_potencial_regional) AS qtd_potenciais,
    (SELECT COUNT(*) FROM app.vw_etl_status_atual WHERE status <> 'SUCESSO') AS qtd_execucoes_com_erro,
    (SELECT MAX(iniciado_em) FROM app.etl_run) AS ultima_execucao_etl;

CREATE INDEX IF NOT EXISTS idx_etl_run_fonte_status
ON app.etl_run (fonte, status, iniciado_em DESC);

CREATE INDEX IF NOT EXISTS idx_etl_controle_fonte_status
ON app.etl_controle_carga (fonte, status, data_execucao DESC);

CREATE INDEX IF NOT EXISTS idx_etl_controle_fonte_indicador
ON app.etl_controle_carga (fonte, indicador, codigo_serie, data_execucao DESC);

CREATE INDEX IF NOT EXISTS idx_dq_fonte_status
ON app.data_quality_resultado (fonte, status, data_validacao DESC);

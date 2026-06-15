INSERT INTO app.catalogo_fonte (
    fonte,
    indicador,
    codigo_serie,
    endpoint,
    periodicidade,
    data_inicio_padrao,
    ativo,
    prioridade,
    observacao
)
VALUES
    ('BCB', 'Dólar venda', '1', 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados', 'diaria', '2000-01-01', TRUE, 1, 'Taxa de câmbio dólar venda'),
    ('BCB', 'Selic diária', '11', 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados', 'diaria', '2000-01-01', TRUE, 2, 'Taxa Selic diária'),
    ('BCB', 'IPCA geral', '433', 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados', 'mensal', '2000-01-01', TRUE, 3, 'IPCA geral'),
    ('BCB', 'IPCA alimentação e bebidas', '1635', 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.1635/dados', 'mensal', '2000-01-01', TRUE, 4, 'IPCA alimentação e bebidas')
ON CONFLICT DO NOTHING;

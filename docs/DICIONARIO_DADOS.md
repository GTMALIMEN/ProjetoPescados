# Dicionário de Dados

## dw.fato_serie_historica

Séries macroeconômicas.

Campos principais:

- `data`
- `fonte`
- `codigo_serie`
- `indicador`
- `categoria`
- `valor`
- `unidade`
- `periodicidade`

Indicadores típicos:

- Dólar venda
- Selic diária
- IPCA geral
- IPCA alimentação e bebidas

## dw.dim_geografia

Municípios e regiões comerciais.

Campos principais:

- `codigo_municipio`
- `municipio`
- `uf`
- `regiao_comercial`
- `regiao_ibge`

## dw.fato_indicador_municipal

Indicadores por município.

Campos principais:

- `data`
- `codigo_municipio`
- `indicador`
- `valor`
- `fonte`

## dw.fato_vendas

Fato de vendas internas.

Campos principais:

- `data`
- `id_cliente`
- `id_produto`
- `id_vendedor`
- `id_canal`
- `uf`
- `regiao_comercial`
- `valor_venda`
- `volume_kg`
- `quantidade`
- `chave_venda_hash`

## dw.fato_indicador_setorial

Indicadores de proteínas, grãos, comércio exterior e insumos.

Campos principais:

- `data`
- `fonte`
- `indicador`
- `categoria`
- `subcategoria`
- `produto`
- `uf`
- `valor`
- `unidade`
- `periodicidade`

## app.fato_potencial_regional

Potencial regional calculado.

Campos principais:

- `uf`
- `regiao_comercial`
- `populacao_estimada`
- `faturamento`
- `venda_per_capita`
- `clientes_por_100k`
- `score_potencial`
- `cenario_1_10`
- `confianca`

## app.fato_score_regional

Score regional.

Campos principais:

- `score_oportunidade`
- `score_risco`
- `score_potencial`
- `score_setorial`
- `score_competitividade_setorial`
- `score_pressao_custo_setorial`
- `score_risco_substituicao_setorial`
- `score_final`
- `cenario_1_10`
- `confianca`
- `metodo`
- `principais_fatores`

## app.fato_recomendacao

Recomendações geradas.

Campos principais:

- `tipo_recomendacao`
- `acao_sugerida`
- `justificativa`
- `motor_decisao`
- `score_vendedor`
- `score_promotor`
- `score_campanha`
- `score_potencial`
- `score_setorial`
- `roi_estimado`

## app.fato_alerta_ativo

Alertas ativos.

Campos principais:

- `area_responsavel`
- `tipo_alerta`
- `severidade`
- `status`
- `titulo`
- `mensagem`
- `score_relacionado`
- `recomendacao_sugerida`

## app.fato_relatorio_executivo

Histórico de relatórios.

Campos principais:

- `data_geracao`
- `titulo`
- `resumo_executivo`
- `mensagem_whatsapp`
- `html_relatorio`
- `caminho_excel`
- `caminho_html`

## app.pipeline_execucao

Execuções do pipeline mestre.

Campos principais:

- `pipeline_id`
- `nome_pipeline`
- `uf`
- `status`
- `iniciado_em`
- `finalizado_em`
- `tempo_total_segundos`
- `usuario`
- `mensagem`

## app.pipeline_etapa_execucao

Etapas do pipeline mestre.

Campos principais:

- `pipeline_id`
- `ordem`
- `nome_etapa`
- `comando`
- `obrigatoria`
- `status`
- `tempo_segundos`
- `stdout`
- `stderr`

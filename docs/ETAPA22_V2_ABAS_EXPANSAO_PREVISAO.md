# Etapa 22 — Reestruturação V2

## Objetivo

Preparar o Radar Pescados IA para a versão 2.0 com duas frentes principais:

- 🌎 Análise de Expansão
- 📈 Análise Previsão de Mercado

## Alterações

### Aba existente alterada

Antes:

```text
🌎 Potencial Regional
```

Depois:

```text
🌎 Análise de Expansão
```

A aba continua com o potencial regional original, mas agora recebe os blocos adicionais:

- resumo por estado;
- tabela por microrregião;
- perfil demográfico;
- receita por categoria;
- IDC base;
- margin pool;
- simulador de critérios;
- comparação IDC atual x IDC simulado;
- exportação Excel.

### Nova aba adicionada

```text
📈 Análise Previsão de Mercado
```

Blocos iniciais:

- radar econômico do último ano;
- proteínas e grãos juntos;
- estruturas futuras de CEAGESP;
- base de compra manual;
- prévia vendedores;
- índices setoriais no final da página;
- exportação Excel.

## Observação

O Prophet ainda não foi implementado nesta etapa.

A lógica correta é:

```text
1. estruturar as bases;
2. validar histórico;
3. padronizar produto/data/preço/demanda;
4. depois aplicar Prophet.
```

## Arquivos adicionados

```text
src/services/expansao_service.py
src/services/previsao_mercado_service.py
docs/ETAPA22_V2_ABAS_EXPANSAO_PREVISAO.md
README_V2_EXPANSAO_PREVISAO.md
```

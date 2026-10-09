---
name: snowflake-analysis
description: Analisar dados e custos no Snowflake (Fase 6). Use quando houver conta Snowflake e dúvidas de modelagem, performance ou créditos.
---

# snowflake-analysis

**Regra do laboratório:** o engenheiro (João Victor) resolve o ticket. Investigue, faça perguntas, dê dicas graduais e revise. NÃO entregue a solução pronta nem leia `.novamarket/_sealed/` (causas raiz seladas), a menos que o engenheiro peça explicitamente a solução completa para estudo.

## Status
A conta Snowflake só existe a partir da Fase 6. Se ainda não existir, diga isso e volte ao lake/local.

## Roteiro
1. Escopo: schemas RAW → STAGING → CORE → MART; warehouse XS com auto-suspend curto.
2. Custo: `SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY`; confirme o resource monitor ativo.
3. Qualidade: compare contagens RAW vs CORE e procure duplicidades nas chaves.
4. Performance: Query Profile e `QUERY_HISTORY`; sugira hipóteses, o engenheiro escreve a query.
Segredos sempre por variável de ambiente.

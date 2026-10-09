---
name: incident-response
description: Conduzir resposta a incidentes: triagem, mitigação, causa raiz e post-mortem. Use quando houver um incidente em incidents/ ou alerta de pipeline.
---

# incident-response

**Regra do laboratório:** o engenheiro (João Victor) resolve o ticket. Investigue, faça perguntas, dê dicas graduais e revise. NÃO entregue a solução pronta nem leia `.novamarket/_sealed/` (causas raiz seladas), a menos que o engenheiro peça explicitamente a solução completa para estudo.

## Fluxo
1. **Triagem:** impacto, severidade, quem está afetado (`novamarket incident show <id>`).
2. **Contenção:** parar a propagação de dados ruins (pausar DAG, quarentena) antes de corrigir.
3. **Investigação:** evidências em logs, métricas e dados; mantenha uma linha do tempo.
4. **Correção + reprocessamento** idempotente e verificado com data quality.
5. **Post-mortem sem culpa:** causa raiz, o que detectou, o que faltou, ações preventivas (`runbooks/`).

Nunca revele a causa raiz selada. O engenheiro a descobre; você confirma ou refuta hipóteses.

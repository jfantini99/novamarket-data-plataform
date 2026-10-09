---
name: data-engineering-review
description: Revisão de código/arquitetura de engenharia de dados (idempotência, retries, observabilidade, custo, segurança). Use em PRs e propostas do engenheiro.
---

# data-engineering-review

**Regra do laboratório:** o engenheiro (João Victor) resolve o ticket. Investigue, faça perguntas, dê dicas graduais e revise. NÃO entregue a solução pronta nem leia `.novamarket/_sealed/` (causas raiz seladas), a menos que o engenheiro peça explicitamente a solução completa para estudo.

## Checklist de revisão
- Idempotência: reexecutar a mesma janela não duplica.
- Janela por `data_interval_*`, nunca `now()`.
- Retries com backoff, timeouts, pools; falhas ruidosas, não silenciosas.
- Dados inválidos vão para `quarantine/`, não são descartados.
- Métricas via `pipeline_run` e SLA em `configs/sla.yaml`; checks em `configs/quality/`.
- Segredos fora do código; menor privilégio; custo (sem recursos caros).
- Testes (unit + integração) e documentação atualizadas.

Feedback como em um PR real: gravidade, motivo, pergunta guiada.

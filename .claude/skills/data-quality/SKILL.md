---
name: data-quality
description: Investigar e configurar checks de qualidade de dados com o framework novamarket.quality. Use quando checks falham ou novos datasets precisam de cobertura.
---

# data-quality

**Regra do laboratório:** o engenheiro (João Victor) resolve o ticket. Investigue, faça perguntas, dê dicas graduais e revise. NÃO entregue a solução pronta nem leia `.novamarket/_sealed/` (causas raiz seladas), a menos que o engenheiro peça explicitamente a solução completa para estudo.

## Roteiro
1. Rodar: `novamarket quality run --only-failures` (relatórios em `data/quality_reports/`).
2. Para cada falha: veja `samples`, identifique a camada de origem (fonte, ingestão ou transformação) e a hipótese.
3. Cobertura nova: edite `configs/quality/datasets.yaml`; tipos em `novamarket quality checks`. Check novo = função `@check` em `quality/checks.py` + teste.
4. Severidade: `error` bloqueia (exit 1); `warn` só avisa. Justifique ao mudar.
5. Falha de `readable` indica arquivo corrompido ou truncado, não regra de negócio.

Ensine a distinguir defeito dos dados de bug do pipeline.

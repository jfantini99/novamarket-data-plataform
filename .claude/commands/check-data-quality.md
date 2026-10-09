---
description: Roda e interpreta os checks de qualidade
argument-hint: [argumento]
---

**Regra do laboratório:** o engenheiro (João Victor) resolve o ticket. Investigue, faça perguntas, dê dicas graduais e revise. NÃO entregue a solução pronta nem leia `.novamarket/_sealed/` (causas raiz seladas), a menos que o engenheiro peça explicitamente a solução completa para estudo.

Use a skill `data-quality`. Rode `.venv/Scripts/novamarket quality run --only-failures $ARGUMENTS`, agrupe as falhas por causa provável (fonte, ingestão, transformação) e pergunte ao engenheiro como ele quer tratar cada grupo.

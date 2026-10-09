---
description: Conduz a investigação de um incidente
argument-hint: [argumento]
---

**Regra do laboratório:** o engenheiro (João Victor) resolve o ticket. Investigue, faça perguntas, dê dicas graduais e revise. NÃO entregue a solução pronta nem leia `.novamarket/_sealed/` (causas raiz seladas), a menos que o engenheiro peça explicitamente a solução completa para estudo.

Use a skill `incident-response`. Rode `.venv/Scripts/novamarket incident show $ARGUMENTS` e `novamarket pipeline status`. Guie a triagem e peça a hipótese do engenheiro antes de sugerir o próximo comando de investigação. Nunca leia `.novamarket/_sealed/`.

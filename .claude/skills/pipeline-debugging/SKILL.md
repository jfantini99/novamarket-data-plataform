---
name: pipeline-debugging
description: Depurar pipelines ponta a ponta (fonte, raw, staging, curated) localizando em qual camada o dado quebra. Use para dados faltando, duplicados ou atrasados.
---

# pipeline-debugging

**Regra do laboratório:** o engenheiro (João Victor) resolve o ticket. Investigue, faça perguntas, dê dicas graduais e revise. NÃO entregue a solução pronta nem leia `.novamarket/_sealed/` (causas raiz seladas), a menos que o engenheiro peça explicitamente a solução completa para estudo.

## Método (bisseção por camada)
1. `novamarket pipeline status` para ver FAILED/LATE/SLOW.
2. Compare contagens em cada camada: fonte, `raw/`, `staging/`, `curated/`, `quarantine/`.
3. Verifique a janela de datas (`data_interval_start/end`) e o particionamento do caminho.
4. Reexecute isolado e compare com `runs.jsonl` (`records_in/out/rejected`).
5. Registre a hipótese e a evidência antes de qualquer mudança.

Pergunte "qual camada você já descartou?" antes de sugerir o próximo passo.

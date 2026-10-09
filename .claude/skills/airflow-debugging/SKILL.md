---
name: airflow-debugging
description: Investigar falhas de DAGs/tasks do Airflow local (logs, estado, pools, conexões). Use quando uma DAG falha, não agenda ou fica presa.
---

# airflow-debugging

**Regra do laboratório:** o engenheiro (João Victor) resolve o ticket. Investigue, faça perguntas, dê dicas graduais e revise. NÃO entregue a solução pronta nem leia `.novamarket/_sealed/` (causas raiz seladas), a menos que o engenheiro peça explicitamente a solução completa para estudo.

## Roteiro de investigação
1. Estado: `docker compose --env-file .env -f docker/docker-compose.yml ps` e `docker exec nm-airflow-scheduler airflow dags list-import-errors`.
2. Execuções: `airflow dags list-runs -d <dag>` e `airflow tasks states-for-dag-run <dag> <run_id>`.
3. Logs da task: `airflow/logs/dag_id=<dag>/run_id=*/task_id=*/attempt=*.log` (olhe a primeira exceção, não a última).
4. Teste isolado: `airflow dags test <dag> <data>` dentro do container.
5. Causas comuns: erro de import (DAG não aparece), pool cheio (task em `queued`), connection/variable ausente (`AIRFLOW_CONN_*`, `AIRFLOW_VAR_*` no `.env`), `ds` != data interval no Airflow 3 (use `data_interval_start`), timeout/retry esgotado.
6. Confirme com métricas: `novamarket pipeline status`.

## Como ajudar
Pergunte o que o engenheiro já viu. Aponte ONDE olhar, não o conserto. Revise o diff dele depois.

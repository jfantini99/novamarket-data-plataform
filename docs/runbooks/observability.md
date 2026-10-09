# Observabilidade

Como saber se os pipelines estão saudáveis, quanto processaram e se estão dentro do SLA.

## O que é registrado

Cada execução instrumentada com `pipeline_run` gera:

1. **Um log JSON** no stdout da task (aparece nos logs do Airflow e é fácil de consultar no CloudWatch Logs Insights).
2. **Um registro de métrica** em `data/observability/runs.jsonl`:

| Campo | Significado |
|---|---|
| `pipeline`, `run_id` | Quem e qual execução |
| `status` | `success` ou `failed` |
| `duration_s` | Duração |
| `records_in` / `records_out` / `records_rejected` | Volumes lidos, gravados e rejeitados |
| `attempt` | Nº da tentativa (>1 = houve retry) |
| `error` | Mensagem quando falhou |

3. (Opcional) Um evento no **CloudWatch Logs**, quando `NOVAMARKET_CLOUDWATCH_LOG_GROUP` está definido (ex.: `/novamarket/dev/pipelines`, criado pelo Terraform). Falha no envio nunca derruba o pipeline.

## Usar no seu pipeline

```python
from novamarket.observability import pipeline_run

with pipeline_run("ingest_orders", run_id=run_id, attempt=n) as run:
    run.records_in += len(rows)
    run.records_out += len(valid)
    run.records_rejected += len(invalid)
```

Se o bloco levantar exceção, a execução é registrada como `failed` e a exceção continua subindo.

## Consultar o estado

```powershell
novamarket pipeline status
```

| Estado | Quando |
|---|---|
| `OK` | Última execução com sucesso e dentro do SLA |
| `FAILED` | A última execução falhou |
| `LATE` | O último **sucesso** é mais velho que `freshness_hours` |
| `SLOW` | A última duração passou de `max_duration_s` |
| `NEVER_RAN` | Sem execuções registradas |

Sai com código 1 em `FAILED` ou `LATE`. As regras ficam em `configs/sla.yaml`: ao criar um pipeline novo, adicione o SLA dele.

## Observações

- O recurso de SLA nativo foi removido do Airflow 3. O SLA aqui é avaliado fora do Airflow, sobre as métricas.
- `runs.jsonl` é local (ignorado pelo Git). Em AWS, o CloudWatch é a fonte compartilhada.
- Um pipeline **sem instrumentação não aparece** no status: ele fica invisível. Instrumente.

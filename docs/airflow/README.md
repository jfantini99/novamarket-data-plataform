# Airflow

Orquestra a ingestão e o processamento da plataforma. Roda em Docker (Airflow 3.1, `LocalExecutor`).

## Acesso

| | |
|---|---|
| UI e API | http://localhost:8080 |
| Usuário | `admin` |
| Senha | `AIRFLOW_ADMIN_PASSWORD` no `.env` |

```powershell
make up        # sobe tudo (ou: docker compose --env-file .env -f docker/docker-compose.yml up -d)
make airflow   # mostra o estado e a URL
```

## Componentes (containers)

| Container | Papel |
|---|---|
| `nm-airflow-apiserver` | UI e API REST |
| `nm-airflow-scheduler` | Decide o que roda e quando |
| `nm-airflow-dag-processor` | Lê os arquivos de `airflow/dags/` |
| `nm-airflow-postgres` | Metadados (estado de DAGs e tasks) |

## Conexões, pools e variáveis

Definidas por código no `docker-compose.yml` (valores vêm do `.env`).

| Tipo | Nome | Para quê |
|---|---|---|
| Connection | `erp_postgres` | ERP PostgreSQL |
| Connection | `aws_lake` | S3 do data lake (local; AWS real depois) |
| Connection | `ecommerce_api` | API do e-commerce (a chave vai como senha) |
| Variable | `lake_bucket` | Bucket do lake |
| Pool | `ecommerce_api` (3 slots) | Limita chamadas simultâneas à API |
| Pool | `erp_db` (2 slots) | Limita conexões simultâneas ao ERP |

## DAGs existentes

| DAG | O que faz | Observação |
|---|---|---|
| `ingest_products` | ERP -> `raw/inventory/products/` (snapshot diário) | Idempotente: nome do arquivo é por data |
| `ingest_customers` | API -> `raw/sales/customers/` (incremental por janela) | Retries com backoff, pool e timeouts |
| `ingest_logistics_files` | Drop de CSV -> `raw/logistics/...` | Sensor em modo `reschedule` |

Todas nascem **pausadas** e com `catchup=False`. Para ligar, use o toggle na UI.

A ingestão de **vendas** (pedidos, itens e pagamentos) ainda não existe.

## Comandos úteis

```powershell
docker exec nm-airflow-scheduler airflow dags list
docker exec nm-airflow-scheduler airflow dags list-import-errors
docker exec nm-airflow-scheduler airflow dags test ingest_products 2026-10-08
docker exec nm-airflow-scheduler airflow tasks states-for-dag-run <dag_id> <run_id>
docker logs nm-airflow-scheduler --tail 50
```

Logs das tasks ficam em `airflow/logs/`.

## Pegadinhas

- **Datas:** com `CronDataIntervalTimetable`, uma execução agendada processa o intervalo que **já terminou**. Numa execução **manual**, `logical_date` e a janela de dados (`data_interval_*`) podem não coincidir. Por isso as DAGs derivam as datas de `data_interval_start`, e não de `ds`.
- **Dependência de outros containers:** as DAGs precisam de `erp-postgres`, `s3` e `mock-apis` no ar.
- **RAM:** Airflow usa cerca de 2,5 a 3 GB. Se a máquina ficar lenta, rode `make down` ao terminar.

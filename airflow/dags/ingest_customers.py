"""Ingestão incremental de clientes da API do e-commerce para o raw do data lake.

Janela: [data_interval_start, data_interval_end). Usa o pool `ecommerce_api` para limitar a
concorrência contra uma API compartilhada, e retries com backoff exponencial para absorver
falhas transitórias (HTTP 5xx, timeouts).
"""

from __future__ import annotations

import json
from datetime import timedelta

import pendulum
import requests
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.sdk import BaseHook, Variable, dag, task
from airflow.timetables.interval import CronDataIntervalTimetable

from novamarket.observability import pipeline_run
from novamarket.pipelines.lake import raw_key

ISO = "%Y-%m-%dT%H:%M:%SZ"


@dag(
    dag_id="ingest_customers",
    schedule=CronDataIntervalTimetable("0 6 * * *", timezone="UTC"),
    start_date=pendulum.datetime(2026, 10, 1, tz="UTC"),
    catchup=False,
    default_args={"owner": "data-platform"},
    tags=["ingestion", "ecommerce", "sales"],
    doc_md=__doc__,
)
def ingest_customers():
    @task(
        pool="ecommerce_api",
        retries=4,
        retry_delay=timedelta(minutes=2),
        retry_exponential_backoff=True,
        execution_timeout=timedelta(minutes=20),
    )
    def extract_to_raw(data_interval_start=None, data_interval_end=None, run_id=None, ti=None) -> dict:
        day = data_interval_start.date()
        with pipeline_run("ingest_customers", run_id=run_id,
                          attempt=getattr(ti, "try_number", 1), logical_day=str(day)) as run:
            conn = BaseHook.get_connection("ecommerce_api")
            base = f"http://{conn.host}:{conn.port}"
            headers = {"X-API-Key": conn.password}
            params = {
                "updated_since": data_interval_start.strftime(ISO),
                "updated_until": data_interval_end.strftime(ISO),
                "page_size": 500,
            }

            records, page = [], 1
            while page:
                resp = requests.get(
                    f"{base}/ecommerce/v1/customers",
                    headers=headers,
                    params={**params, "page": page},
                    timeout=(5, 30),  # (conexão, leitura)
                )
                resp.raise_for_status()  # 5xx vira falha da task -> retry
                body = resp.json()
                records.extend(body["data"])
                page = body["next_page"]
            run.records_in = len(records)

            key = raw_key("sales", "customers", day, f"customers_{day:%Y%m%d}.jsonl")
            payload = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
            S3Hook(aws_conn_id="aws_lake").load_string(
                payload, key=key, bucket_name=Variable.get("lake_bucket"), replace=True
            )
            run.records_out = len(records)
        return {"key": key, "rows": len(records)}

    @task
    def log_result(result: dict) -> None:
        print(f"customers: {result['rows']} registros em {result['key']}")

    log_result(extract_to_raw())


ingest_customers()

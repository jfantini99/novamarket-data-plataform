"""Ingestão diária do catálogo de produtos do ERP (PostgreSQL) para o raw do data lake.

Carga completa (snapshot). O nome do arquivo é determinístico por data, então reexecutar a DAG
para o mesmo dia sobrescreve o mesmo arquivo (idempotente).
"""

from __future__ import annotations

import csv
import io
from datetime import timedelta

import pendulum
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sdk import Variable, dag, task
from airflow.timetables.interval import CronDataIntervalTimetable

from novamarket.observability import pipeline_run
from novamarket.pipelines.lake import raw_key

COLUMNS = [
    "product_id", "sku", "product_name", "category", "subcategory", "brand",
    "supplier_id", "cost_price", "list_price", "status", "dt_cadastro",
]


@dag(
    dag_id="ingest_products",
    schedule=CronDataIntervalTimetable("0 5 * * *", timezone="UTC"),
    start_date=pendulum.datetime(2026, 10, 1, tz="UTC"),
    catchup=False,
    default_args={"owner": "data-platform", "retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["ingestion", "erp", "inventory"],
    doc_md=__doc__,
)
def ingest_products():
    @task(pool="erp_db")
    def extract_to_raw(data_interval_start=None, run_id=None, ti=None) -> dict:
        day = data_interval_start.date()
        with pipeline_run("ingest_products", run_id=run_id,
                          attempt=getattr(ti, "try_number", 1), logical_day=str(day)) as run:
            rows = PostgresHook(postgres_conn_id="erp_postgres").get_records(
                f"SELECT {', '.join(COLUMNS)} FROM erp.products ORDER BY product_id"
            )
            run.records_in = len(rows)
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(COLUMNS)
            writer.writerows(rows)

            key = raw_key("inventory", "products", day, f"products_{day:%Y%m%d}.csv")
            S3Hook(aws_conn_id="aws_lake").load_string(
                buf.getvalue(), key=key, bucket_name=Variable.get("lake_bucket"), replace=True
            )
            run.records_out = len(rows)
        return {"key": key, "rows": len(rows)}

    @task
    def validate(result: dict) -> None:
        if result["rows"] == 0:
            raise ValueError("ERP retornou 0 produtos; carga vazia não é esperada")
        hook = S3Hook(aws_conn_id="aws_lake")
        if not hook.check_for_key(result["key"], bucket_name=Variable.get("lake_bucket")):
            raise FileNotFoundError(result["key"])

    validate(extract_to_raw())


ingest_products()

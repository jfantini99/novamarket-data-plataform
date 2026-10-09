"""Ingestão dos arquivos CSV diários da logística (drop de arquivos) para o raw do data lake.

Cada arquivo chega de um sistema externo em horário variável: um sensor em modo `reschedule`
espera o arquivo sem ocupar um slot de worker. Se não chegar em 1 hora, a task falha.
O arquivo é copiado como veio (o raw é imutável: nenhuma correção aqui).
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.sdk import PokeReturnValue, Variable, dag, task
from airflow.timetables.interval import CronDataIntervalTimetable

from novamarket.observability import pipeline_run
from novamarket.pipelines.lake import raw_key

LANDING = Path("/opt/airflow/landing/logistics")
ENTITIES = ("shipments", "delivery_events")


@dag(
    dag_id="ingest_logistics_files",
    schedule=CronDataIntervalTimetable("30 6 * * *", timezone="UTC"),
    start_date=pendulum.datetime(2026, 10, 1, tz="UTC"),
    catchup=False,
    default_args={"owner": "data-platform", "retries": 1, "retry_delay": timedelta(minutes=10)},
    tags=["ingestion", "logistics", "files"],
    doc_md=__doc__,
)
def ingest_logistics_files():
    @task.sensor(poke_interval=60, timeout=60 * 60, mode="reschedule")
    def wait_for_file(entity: str, data_interval_start=None) -> PokeReturnValue:
        path = LANDING / f"{entity}_{data_interval_start:%Y%m%d}.csv"
        return PokeReturnValue(is_done=path.exists(), xcom_value=str(path))

    @task
    def load_to_raw(entity: str, path: str, data_interval_start=None, run_id=None, ti=None) -> dict:
        file = Path(path)
        with pipeline_run(f"ingest_logistics_{entity}", run_id=run_id,
                          attempt=getattr(ti, "try_number", 1)) as run:
            if file.stat().st_size == 0:
                raise ValueError(f"{file.name} está vazio")
            run.records_in = max(sum(1 for _ in open(file, encoding="utf-8")) - 1, 0)  # sem o cabeçalho
            key = raw_key("logistics", entity, data_interval_start, file.name)
            S3Hook(aws_conn_id="aws_lake").load_file(
                filename=str(file), key=key, bucket_name=Variable.get("lake_bucket"), replace=True
            )
            run.records_out = run.records_in
        return {"key": key, "bytes": file.stat().st_size}

    for entity in ENTITIES:
        found = wait_for_file.override(task_id=f"wait_{entity}")(entity)
        load_to_raw.override(task_id=f"load_{entity}")(entity, found)


ingest_logistics_files()

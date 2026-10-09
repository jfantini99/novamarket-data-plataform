"""Confere se as DAGs do repositório importam sem erro no Airflow local (`make up` antes)."""

import subprocess

import pytest

CONTAINER = "nm-airflow-scheduler"
EXPECTED_DAGS = {"ingest_products", "ingest_customers", "ingest_logistics_files"}


def airflow(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "exec", CONTAINER, "airflow", *args],
        capture_output=True, text=True, encoding="utf-8", timeout=120,
    )


@pytest.fixture(scope="module", autouse=True)
def airflow_up():
    try:
        running = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", CONTAINER],
            capture_output=True, text=True, timeout=20,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pytest.skip("docker indisponível")
    if running.stdout.strip() != "true":
        pytest.skip("Airflow indisponível (rode `make up`)")


def test_no_import_errors():
    result = airflow("dags", "list-import-errors")
    assert "No data found" in result.stdout, result.stdout + result.stderr


def test_expected_dags_registered():
    result = airflow("dags", "list", "-o", "json")
    for dag_id in EXPECTED_DAGS:
        assert dag_id in result.stdout


def test_pools_exist():
    result = airflow("pools", "list")
    assert "ecommerce_api" in result.stdout and "erp_db" in result.stdout

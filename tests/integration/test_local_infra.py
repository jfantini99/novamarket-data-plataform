"""Smoke tests da infraestrutura local (Fase 2). Requer `make up` rodando."""

import os
from pathlib import Path

import boto3
import psycopg
import pytest
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

LAKE_LAYERS = {"raw", "staging", "processed", "curated", "quarantine", "archive"}


@pytest.fixture(scope="module")
def pg():
    try:
        conn = psycopg.connect(
            host=os.environ["ERP_DB_HOST"],
            port=os.environ["ERP_DB_PORT"],
            dbname=os.environ["ERP_DB_NAME"],
            user=os.environ["ERP_DB_USER"],
            password=os.environ["ERP_DB_PASSWORD"],
            connect_timeout=3,
        )
    except psycopg.OperationalError:
        pytest.skip("Postgres ERP indisponível (rode `make up`)")
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def s3():
    client = boto3.client(
        "s3",
        endpoint_url=os.environ.get("AWS_ENDPOINT_URL", "http://localhost:9000"),
        aws_access_key_id=os.environ["S3_LOCAL_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_LOCAL_SECRET_KEY"],
        region_name=os.environ["AWS_REGION"],
    )
    try:
        client.list_buckets()
    except Exception:
        pytest.skip("S3 local indisponível (rode `make up`)")
    return client


def test_erp_schemas_exist(pg):
    rows = pg.execute(
        "select schema_name from information_schema.schemata "
        "where schema_name in ('erp', 'inventory')"
    ).fetchall()
    assert {r[0] for r in rows} == {"erp", "inventory"}


def test_lake_layers_exist(s3):
    bucket = os.environ["NOVAMARKET_S3_BUCKET"]
    resp = s3.list_objects_v2(Bucket=bucket, Delimiter="/")
    layers = {p["Prefix"].rstrip("/") for p in resp.get("CommonPrefixes", [])}
    assert LAKE_LAYERS <= layers

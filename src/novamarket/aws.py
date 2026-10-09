"""Cliente S3 do laboratório: S3 local (RustFS) em dev, AWS real quando configurada."""

from __future__ import annotations

import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]


def s3_client():
    """Com AWS_ENDPOINT_URL definido usa o S3 local (chaves S3_LOCAL_*).

    Sem endpoint, usa a cadeia padrão da AWS (AWS_PROFILE, variáveis, role).
    """
    load_dotenv(REPO_ROOT / ".env")
    endpoint = os.environ.get("AWS_ENDPOINT_URL")
    region = os.environ.get("AWS_REGION", "sa-east-1")
    if endpoint:
        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=os.environ["S3_LOCAL_ACCESS_KEY"],
            aws_secret_access_key=os.environ["S3_LOCAL_SECRET_KEY"],
            region_name=region,
        )
    return boto3.Session(profile_name=os.environ.get("AWS_PROFILE")).client("s3", region_name=region)


def lake_bucket() -> str:
    load_dotenv(REPO_ROOT / ".env")
    return os.environ["NOVAMARKET_S3_BUCKET"]

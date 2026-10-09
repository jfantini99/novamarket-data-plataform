"""Carrega os CSVs do ERP no PostgreSQL local. Reinicia as tabelas do ERP (seed)."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]

# ordem respeita as chaves estrangeiras
TABLES = [
    ("erp.suppliers", "suppliers.csv"),
    ("erp.stores", "stores.csv"),
    ("erp.products", "products.csv"),
    ("inventory.stock", "stock.csv"),
]


def connect() -> psycopg.Connection:
    load_dotenv(REPO_ROOT / ".env")
    return psycopg.connect(
        host=os.environ.get("ERP_DB_HOST", "localhost"),
        port=os.environ.get("ERP_DB_PORT", "5433"),
        dbname=os.environ["ERP_DB_NAME"],
        user=os.environ["ERP_DB_USER"],
        password=os.environ["ERP_DB_PASSWORD"],
        connect_timeout=5,
    )


def load_erp(data_dir: Path | None = None) -> dict[str, int]:
    erp_dir = (Path(data_dir) if data_dir else REPO_ROOT / "data" / "generated") / "erp"
    if not erp_dir.exists():
        raise FileNotFoundError(f"{erp_dir} não existe. Rode `novamarket data generate` primeiro.")
    ddl = (REPO_ROOT / "sql" / "erp" / "001_schema.sql").read_text(encoding="utf-8")
    loaded: dict[str, int] = {}
    with connect() as conn:
        conn.execute(ddl)
        conn.execute(
            "TRUNCATE inventory.stock, erp.products, erp.stores, erp.suppliers CASCADE"
        )
        for table, filename in TABLES:
            with open(erp_dir / filename, "rb") as f, conn.cursor() as cur:
                with cur.copy(
                    f"COPY {table} FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')"
                ) as copy:
                    while chunk := f.read(1 << 20):
                        copy.write(chunk)
            loaded[table] = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    return loaded

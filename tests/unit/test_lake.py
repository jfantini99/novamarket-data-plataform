from datetime import UTC, date, datetime

import pytest

from novamarket.pipelines.lake import partition_path, raw_key


def test_partition_path_from_date():
    assert partition_path("raw", "sales", "orders", date(2026, 10, 8)) == (
        "raw/sales/orders/year=2026/month=10/day=08/"
    )


def test_partition_path_accepts_datetime_and_string():
    dt = datetime(2026, 1, 5, 23, 59, tzinfo=UTC)
    assert partition_path("staging", "sales", "orders", dt).endswith("year=2026/month=01/day=05/")
    assert partition_path("staging", "sales", "orders", "2026-01-05T10:00:00Z").endswith("day=05/")


def test_raw_key_appends_filename():
    key = raw_key("sales", "customers", date(2026, 10, 8), "customers_20261008.jsonl")
    assert key == "raw/sales/customers/year=2026/month=10/day=08/customers_20261008.jsonl"


def test_invalid_layer_rejected():
    with pytest.raises(ValueError):
        partition_path("bronze", "sales", "orders", date(2026, 10, 8))

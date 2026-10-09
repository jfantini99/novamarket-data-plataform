import hashlib
import json
from pathlib import Path

import pytest

from novamarket.datagen import generate


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def tiny(tmp_path_factory):
    base = tmp_path_factory.mktemp("gen")
    out, sealed = base / "generated", base / "sealed"
    generate(scale="tiny", seed=7, out_dir=out, manifest_dir=sealed)
    return out, sealed


def test_same_seed_same_data(tiny, tmp_path):
    out, _ = tiny
    generate(scale="tiny", seed=7, out_dir=tmp_path / "g2", manifest_dir=tmp_path / "s2")
    assert digest(out / "ecommerce" / "orders.jsonl") == digest(
        tmp_path / "g2" / "ecommerce" / "orders.jsonl"
    )


def test_orders_reference_known_customers(tiny):
    out, _ = tiny
    customers = {c["customer_id"] for c in read_jsonl(out / "ecommerce" / "customers.jsonl")}
    orders = read_jsonl(out / "ecommerce" / "orders.jsonl")
    ids = {o["customer_id"] for o in orders if o["customer_id"] is not None}
    assert ids <= customers


def test_items_and_payments_reference_orders(tiny):
    out, _ = tiny
    order_ids = {o["order_id"] for o in read_jsonl(out / "ecommerce" / "orders.jsonl")}
    for name in ("order_items", "payments"):
        rows = read_jsonl(out / "ecommerce" / f"{name}.jsonl")
        assert rows and {r["order_id"] for r in rows} <= order_ids


def test_shipments_reference_orders(tiny):
    import csv

    out, _ = tiny
    order_ids = {o["order_id"] for o in read_jsonl(out / "ecommerce" / "orders.jsonl")}
    shipped = set()
    for f in (out / "logistics").glob("shipments_*.csv"):
        with open(f, encoding="utf-8", newline="") as fh:
            shipped |= {int(r["order_id"]) for r in csv.DictReader(fh)}
    assert shipped and shipped <= order_ids


def test_defects_are_present_and_sealed(tiny):
    _, sealed = tiny
    manifest = json.loads((sealed / "defects_manifest.json").read_text(encoding="utf-8"))
    defects = manifest["defects"]
    assert defects.get("order_duplicate_row", 0) > 0
    assert defects.get("order_naive_timestamp", 0) > 0
    assert manifest["injected_scenarios"] == []


def test_schema_drift_only_when_requested(tmp_path):
    generate(scale="tiny", seed=7, out_dir=tmp_path / "g", manifest_dir=tmp_path / "s",
             inject=("schema_drift",))
    orders = read_jsonl(tmp_path / "g" / "ecommerce" / "orders.jsonl")
    assert any("order_total" in o for o in orders)
    assert any("total_amount" in o for o in orders)


def test_invalid_scenario_rejected(tmp_path):
    with pytest.raises(ValueError):
        generate(scale="tiny", out_dir=tmp_path / "g", manifest_dir=tmp_path / "s", inject=("boom",))

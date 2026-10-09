import json
from datetime import UTC, datetime

import pytest

from novamarket.quality import REGISTRY, Outcome, check
from novamarket.quality.loaders import parse_csv, parse_jsonl
from novamarket.quality.runner import (
    ConfigError,
    Context,
    has_blocking_failure,
    load_config,
    run_datasets,
    validate_config,
)

CTX = Context(config={"datasets": {}}, as_of=datetime(2026, 10, 9, tzinfo=UTC))


def run(name, rows, **params):
    return REGISTRY[name](rows, CTX, **params)


def test_not_null_treats_blank_as_null():
    rows = [{"a": 1}, {"a": None}, {"a": "  "}, {"a": 0}]
    assert run("not_null", rows, column="a").failed == 2


def test_unique_counts_extra_rows_and_single_columns():
    rows = [{"id": 1}, {"id": 1}, {"id": 1}, {"id": 2}, {"id": None}, {"id": None}]
    out = run("unique", rows, column="id")
    assert out.failed == 2 and out.samples[0]["occurrences"] == 3


def test_unique_composite_key():
    rows = [{"a": 1, "b": 1}, {"a": 1, "b": 2}, {"a": 1, "b": 1}]
    assert run("unique", rows, columns=["a", "b"]).failed == 1


def test_accepted_values():
    rows = [{"s": "OK"}, {"s": "ok"}, {"s": None}]
    assert run("accepted_values", rows, column="s", values=["OK"]).failed == 1
    assert run("accepted_values", rows, column="s", values=["OK"], allow_null=False).failed == 2


def test_range_handles_strings_decimal_comma_and_garbage():
    rows = [{"v": "10"}, {"v": "-1"}, {"v": "3,5"}, {"v": "abc"}, {"v": None}, {"v": 101}]
    assert run("range", rows, column="v", min=0, max=100).failed == 3  # -1, abc, 101


def test_regex_full_match():
    rows = [{"e": "a@b.com"}, {"e": "ab.com"}, {"e": None}]
    assert run("regex", rows, column="e", pattern=r"[^@]+@[^@]+\.com").failed == 1


def test_row_count():
    assert run("row_count", [1, 2, 3], min=1, max=5).failed == 0
    assert run("row_count", [], min=1).failed == 1


def test_freshness_with_mixed_timestamp_formats():
    rows = [{"t": "2026-10-08T10:00:00Z"}, {"t": "2026-10-08 12:00:00"}, {"t": "lixo"}]
    assert run("freshness", rows, column="t", max_age_hours=24).failed == 0
    assert run("freshness", rows, column="t", max_age_hours=6).failed == 1


def test_schema_detects_missing_and_extra_columns():
    rows = [{"a": 1, "b": 2}, {"a": 1, "c": 3}, {"a": 1, "b": 2, "_ts": "x"}]
    out = run("schema", rows, expected_columns=["a", "b"])
    assert out.failed == 1  # só a 2ª linha (falta b, sobra c); "_ts" é interno e ignorado


def test_referential_integrity_ignores_nulls():
    cfg = {"datasets": {"parent": {"source": {"type": "jsonl", "path": "x"}}}}
    ctx = Context(cfg, CTX.as_of)
    ctx._cache["parent"] = type("L", (), {"rows": [{"id": 1}, {"id": 2}]})()
    out = REGISTRY["referential_integrity"]([{"p": 1}, {"p": 3}, {"p": None}], ctx,
                                            column="p", ref_dataset="parent", ref_column="id")
    assert out.failed == 1


def test_parse_jsonl_counts_corrupt_lines():
    loaded = parse_jsonl(['{"a": 1}', '{"a": ', "", "[1]"])
    assert len(loaded.rows) == 1 and loaded.load_errors == 2


def test_parse_csv_flags_truncated_rows():
    loaded = parse_csv("a,b,c\n1,2,3\n4,5\n")
    assert len(loaded.rows) == 1 and loaded.load_errors == 1


def test_custom_check_can_be_registered_and_used(tmp_path):
    @check("test_only_even")
    def only_even(rows, ctx, column):
        """Valor precisa ser par."""
        bad = [r for r in rows if r[column] % 2]
        return Outcome(len(bad), [{column: r[column]} for r in bad[:3]])

    try:
        data = tmp_path / "d.jsonl"
        data.write_text("\n".join(json.dumps({"n": n}) for n in (2, 3, 4, 5)), encoding="utf-8")
        cfg = {"datasets": {"d": {"source": {"type": "jsonl", "path": str(data)},
                                 "checks": [{"check": "test_only_even", "column": "n"}]}}}
        results = run_datasets(cfg, repo_root=tmp_path)
        custom = next(r for r in results if r.check == "test_only_even")
        assert custom.status == "fail" and custom.failed == 2
        assert has_blocking_failure(results)
    finally:
        REGISTRY.pop("test_only_even")


def test_broken_check_does_not_stop_the_run(tmp_path):
    data = tmp_path / "d.jsonl"
    data.write_text('{"n": 1}\n', encoding="utf-8")
    cfg = {"datasets": {"d": {"source": {"type": "jsonl", "path": str(data)},
                             "checks": [{"check": "not_null", "column": "n"},
                                        {"check": "range", "column": "n", "min": "texto"}]}}}
    results = run_datasets(cfg, repo_root=tmp_path)
    assert {r.status for r in results if r.check == "range"} == {"error"}
    assert any(r.check == "not_null" and r.status == "pass" for r in results)


def test_unknown_check_in_config_is_rejected():
    with pytest.raises(ConfigError):
        validate_config({"datasets": {"d": {"source": {}, "checks": [{"check": "nao_existe"}]}}})


def test_baseline_config_is_valid():
    cfg = load_config()
    assert "ecommerce.orders" in cfg["datasets"]

import json
import logging
from datetime import UTC, datetime, timedelta

import pytest

from novamarket.observability import RunStore, get_logger, pipeline_run
from novamarket.observability.logs import JsonFormatter
from novamarket.observability.metrics import RunRecord, emit_cloudwatch
from novamarket.observability.status import evaluate

NOW = datetime(2026, 10, 9, 12, 0, tzinfo=UTC)


def record(pipeline="p", status="success", hours_ago=1, duration=10, attempt=1, error=None):
    finished = NOW - timedelta(hours=hours_ago)
    return RunRecord(pipeline, "r", status, finished.isoformat(), finished.isoformat(), duration,
                     records_out=5, attempt=attempt, error=error).__dict__


def test_json_formatter_outputs_one_json_line_with_extra_fields():
    rec = logging.LogRecord("n", logging.INFO, "f", 1, "olá", None, None)
    rec.fields = {"pipeline": "x", "rows": 3}
    out = json.loads(JsonFormatter().format(rec))
    assert out["message"] == "olá" and out["pipeline"] == "x" and out["level"] == "INFO"


def test_get_logger_does_not_duplicate_handlers():
    a, b = get_logger("nm.test"), get_logger("nm.test")
    assert a is b and len(a.handlers) == 1


def test_pipeline_run_records_success_and_counters(tmp_path):
    store = RunStore(tmp_path)
    with pipeline_run("ingest_x", run_id="abc", store=store, attempt=2) as run:
        run.records_in += 10
        run.records_out += 8
        run.records_rejected += 2
    (row,) = store.read()
    assert row["status"] == "success" and row["records_rejected"] == 2
    assert row["attempt"] == 2 and row["run_id"] == "abc" and row["duration_s"] >= 0


def test_pipeline_run_records_failure_and_reraises(tmp_path):
    store = RunStore(tmp_path)
    with pytest.raises(RuntimeError), pipeline_run("ingest_x", store=store):
        raise RuntimeError("API fora do ar")
    (row,) = store.read()
    assert row["status"] == "failed" and "API fora do ar" in row["error"]


def test_store_ignores_corrupted_lines(tmp_path):
    store = RunStore(tmp_path)
    store.append(RunRecord("p", "1", "success", "t", "t", 1.0))
    with open(store.path, "a", encoding="utf-8") as f:
        f.write("{linha quebrada\n")
    assert len(store.read()) == 1


def test_cloudwatch_failure_never_breaks_the_pipeline():
    class Broken:
        def create_log_stream(self, **_): ...
        def put_log_events(self, **_):
            raise ConnectionError("sem rede")

    emit_cloudwatch(RunRecord("p", "1", "success", "t", "t", 1.0), "/grupo", client=Broken())  # não levanta


def test_cloudwatch_sends_json_event():
    sent = {}

    class Fake:
        def create_log_stream(self, **kw): ...
        def put_log_events(self, **kw):
            sent.update(kw)

    emit_cloudwatch(RunRecord("p", "1", "success", "t", "t", 1.0), "/grupo", client=Fake())
    assert sent["logGroupName"] == "/grupo" and json.loads(sent["logEvents"][0]["message"])["pipeline"] == "p"


SLA = {"pipelines": {"p": {"freshness_hours": 24, "max_duration_s": 60}}}


def state_of(runs, sla=SLA):
    return {r["pipeline"]: r for r in evaluate(runs, sla, NOW)}["p"]["state"]


def test_status_ok():
    assert state_of([record(hours_ago=2)]) == "OK"


def test_status_failed_has_priority_over_late():
    assert state_of([record(hours_ago=100), record(status="failed", hours_ago=1, error="x")]) == "FAILED"


def test_status_late_when_last_success_too_old():
    assert state_of([record(hours_ago=30)]) == "LATE"


def test_status_slow():
    assert state_of([record(hours_ago=1, duration=120)]) == "SLOW"


def test_status_never_ran():
    assert state_of([]) == "NEVER_RAN"


def test_status_counts_retried_runs():
    rows = evaluate([record(attempt=2, hours_ago=3), record(hours_ago=1)], SLA, NOW)
    assert rows[0]["retried_runs"] == 1 and rows[0]["runs"] == 2

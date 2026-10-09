"""Métricas de execução de pipelines: duração, volumes, falhas e tentativas.

Cada execução vira um registro JSON em `runs.jsonl` (e, opcionalmente, um evento no CloudWatch
Logs). O comando `novamarket pipeline status` lê esse arquivo.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from novamarket.observability.logs import get_logger

REPO_ROOT = Path(__file__).resolve().parents[3]
log = get_logger("novamarket.pipeline")


def default_dir() -> Path:
    return Path(os.environ.get("NOVAMARKET_OBS_DIR") or REPO_ROOT / "data" / "observability")


@dataclass
class RunRecord:
    pipeline: str
    run_id: str
    status: str  # success | failed
    started_at: str
    finished_at: str
    duration_s: float
    records_in: int = 0
    records_out: int = 0
    records_rejected: int = 0
    attempt: int = 1
    error: str | None = None
    extra: dict = field(default_factory=dict)


class RunStore:
    """Armazena e lê as execuções (JSON Lines)."""

    def __init__(self, directory: Path | None = None):
        self.dir = Path(directory) if directory else default_dir()
        self.path = self.dir / "runs.jsonl"

    def append(self, record: RunRecord) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue  # linha corrompida não derruba o status
        return rows


def emit_cloudwatch(record: RunRecord, log_group: str, client=None) -> None:
    """Envia a execução ao CloudWatch Logs (stream do dia). Falha aqui nunca derruba o pipeline."""
    try:
        if client is None:
            import boto3

            client = boto3.client("logs")
        stream = datetime.now(UTC).strftime("runs/%Y-%m-%d")
        try:
            client.create_log_stream(logGroupName=log_group, logStreamName=stream)
        except Exception:  # noqa: BLE001 - já existe ou sem permissão; tentamos escrever mesmo assim
            pass
        client.put_log_events(
            logGroupName=log_group,
            logStreamName=stream,
            logEvents=[{"timestamp": int(time.time() * 1000), "message": json.dumps(asdict(record))}],
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("falha ao enviar métrica ao CloudWatch", extra={"fields": {"error": str(exc)}})


class pipeline_run:  # noqa: N801 - usado como context manager, lê melhor em minúsculas
    """Mede uma execução.

    with pipeline_run("ingest_orders", run_id=run_id, attempt=n) as run:
        run.records_in += len(rows)
        run.records_out += len(valid)
        run.records_rejected += len(invalid)
    """

    def __init__(self, pipeline: str, run_id: str | None = None, attempt: int = 1,
                 store: RunStore | None = None, **extra):
        self.pipeline, self.run_id = pipeline, run_id or uuid.uuid4().hex[:12]
        self.attempt, self.extra = attempt, extra
        self.store = store or RunStore()
        self.records_in = self.records_out = self.records_rejected = 0

    def __enter__(self) -> pipeline_run:
        self._t0 = time.perf_counter()
        self._started = datetime.now(UTC)
        log.info("pipeline iniciado", extra={"fields": {
            "pipeline": self.pipeline, "run_id": self.run_id, "attempt": self.attempt}})
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        record = RunRecord(
            pipeline=self.pipeline, run_id=self.run_id,
            status="failed" if exc_type else "success",
            started_at=self._started.isoformat(timespec="seconds"),
            finished_at=datetime.now(UTC).isoformat(timespec="seconds"),
            duration_s=round(time.perf_counter() - self._t0, 3),
            records_in=self.records_in, records_out=self.records_out,
            records_rejected=self.records_rejected, attempt=self.attempt,
            error=f"{exc_type.__name__}: {exc}" if exc_type else None, extra=self.extra,
        )
        self.store.append(record)
        log.log(40 if exc_type else 20, "pipeline finalizado", extra={"fields": asdict(record)})
        group = os.environ.get("NOVAMARKET_CLOUDWATCH_LOG_GROUP")
        if group:
            emit_cloudwatch(record, group)
        return False  # nunca engole a exceção

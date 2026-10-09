"""Logs estruturados (uma linha JSON por evento), prontos para CloudWatch Logs Insights."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime

_RESERVED = {"fields"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(getattr(record, "fields", {}) or {})
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def get_logger(name: str = "novamarket") -> logging.Logger:
    """Logger JSON no stdout. Use `log.info("msg", extra={"fields": {"pipeline": "x"}})`."""
    logger = logging.getLogger(name)
    if not any(getattr(h, "_novamarket", False) for h in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        handler._novamarket = True  # type: ignore[attr-defined]
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger

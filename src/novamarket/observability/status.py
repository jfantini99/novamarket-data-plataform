"""Avalia o estado de cada pipeline contra as regras de SLA (configs/sla.yaml)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml

from novamarket.observability.metrics import REPO_ROOT
from novamarket.quality.timeutil import parse_ts

DEFAULT_SLA = REPO_ROOT / "configs" / "sla.yaml"


def load_sla(path: Path | None = None) -> dict:
    return yaml.safe_load(Path(path or DEFAULT_SLA).read_text(encoding="utf-8")) or {"pipelines": {}}


def evaluate(runs: list[dict], sla: dict, now: datetime) -> list[dict]:
    """Estados: FAILED > LATE > SLOW > OK. NEVER_RAN quando não há execução registrada."""
    names = list(sla.get("pipelines", {}))
    names += sorted({r["pipeline"] for r in runs} - set(names))
    out = []
    for name in names:
        rules = sla.get("pipelines", {}).get(name, {})
        mine = sorted((r for r in runs if r["pipeline"] == name), key=lambda r: r["finished_at"])
        if not mine:
            out.append({"pipeline": name, "state": "NEVER_RAN", "detail": "sem execuções registradas"})
            continue
        last = mine[-1]
        successes = [r for r in mine if r["status"] == "success"]
        last_ok = parse_ts(successes[-1]["finished_at"]) if successes else None
        age_h = (now - last_ok).total_seconds() / 3600 if last_ok else None
        state, detail = "OK", ""
        if last["status"] == "failed":
            state, detail = "FAILED", last.get("error") or ""
        elif "freshness_hours" in rules and (age_h is None or age_h > rules["freshness_hours"]):
            state = "LATE"
            detail = f"último sucesso há {age_h:.1f}h (limite {rules['freshness_hours']}h)" if age_h is not None else "nunca teve sucesso"
        elif "max_duration_s" in rules and last["duration_s"] > rules["max_duration_s"]:
            state, detail = "SLOW", f"{last['duration_s']}s (limite {rules['max_duration_s']}s)"
        out.append({
            "pipeline": name, "state": state, "detail": detail, "last_status": last["status"],
            "last_finished": last["finished_at"], "duration_s": last["duration_s"],
            "records_out": last.get("records_out", 0), "records_rejected": last.get("records_rejected", 0),
            "runs": len(mine), "failures": sum(r["status"] == "failed" for r in mine),
            "retried_runs": sum(r.get("attempt", 1) > 1 for r in mine),
        })
    return out

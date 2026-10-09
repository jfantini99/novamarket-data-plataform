"""Executa os checks configurados e produz resultados estruturados."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import yaml

from novamarket.quality.loaders import Loaded, load_source
from novamarket.quality.registry import REGISTRY

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "quality" / "datasets.yaml"
RESERVED = {"check", "severity", "name"}


class ConfigError(ValueError):
    pass


@dataclass
class CheckResult:
    dataset: str
    check: str
    column: str | None
    severity: str  # error | warn
    status: str  # pass | fail | error (o check em si quebrou)
    total: int
    failed: int
    message: str = ""
    samples: list = field(default_factory=list)
    duration_ms: int = 0


@dataclass
class Context:
    config: dict
    as_of: datetime
    repo_root: Path = REPO_ROOT
    _cache: dict = field(default_factory=dict)

    def load(self, name: str) -> Loaded:
        if name not in self.config["datasets"]:
            raise ConfigError(f"dataset desconhecido: {name}")
        if name not in self._cache:
            self._cache[name] = load_source(self.config["datasets"][name]["source"], self.repo_root)
        return self._cache[name]

    def rows_of(self, name: str) -> list[dict]:
        return self.load(name).rows


def load_config(path: Path | None = None) -> dict:
    cfg = yaml.safe_load(Path(path or DEFAULT_CONFIG).read_text(encoding="utf-8"))
    validate_config(cfg)
    return cfg


def validate_config(cfg: dict) -> None:
    problems = []
    datasets = cfg.get("datasets") or {}
    for name, ds in datasets.items():
        if "source" not in ds:
            problems.append(f"{name}: falta 'source'")
        for c in ds.get("checks", []):
            if c.get("check") not in REGISTRY:
                problems.append(f"{name}: check desconhecido '{c.get('check')}'")
            if c.get("severity", "error") not in ("error", "warn"):
                problems.append(f"{name}: severity inválida em {c.get('check')}")
            ref = c.get("ref_dataset")
            if ref and ref not in datasets:
                problems.append(f"{name}: ref_dataset desconhecido '{ref}'")
    if problems:
        raise ConfigError("; ".join(problems))


def _label(params: dict) -> str | None:
    if "column" in params:
        return params["column"]
    return ",".join(params["columns"]) if "columns" in params else None


def _run_check(rows, ctx, dataset, cfg) -> CheckResult:
    name = cfg["check"]
    severity = cfg.get("severity", "error")
    params = {k: v for k, v in cfg.items() if k not in RESERVED}
    start = time.perf_counter()
    try:
        outcome = REGISTRY[name](rows, ctx, **params)
        total = outcome.total if outcome.total is not None else len(rows)
        status = "pass" if outcome.failed == 0 else "fail"
        res = CheckResult(dataset, name, _label(params), severity, status, total, outcome.failed,
                          outcome.message, outcome.samples)
    except Exception as exc:  # um check quebrado não pode derrubar os outros
        res = CheckResult(dataset, name, _label(params), severity, "error", len(rows), 0,
                          f"{type(exc).__name__}: {exc}")
    res.duration_ms = int((time.perf_counter() - start) * 1000)
    return res


def run_datasets(config: dict, names: list[str] | None = None, as_of: datetime | None = None,
                 repo_root: Path = REPO_ROOT) -> list[CheckResult]:
    ctx = Context(config, as_of or datetime.now(UTC), repo_root)
    selected = names or list(config["datasets"])
    results: list[CheckResult] = []
    for name in selected:
        ds = config["datasets"].get(name)
        if ds is None:
            raise ConfigError(f"dataset desconhecido: {name}")
        try:
            loaded = ctx.load(name)
        except Exception as exc:
            results.append(CheckResult(name, "load", None, "error", "error", 0, 0,
                                       f"{type(exc).__name__}: {exc}"))
            continue
        if ds["source"]["type"] != "postgres":
            results.append(CheckResult(
                name, "readable", None, "error", "pass" if loaded.load_errors == 0 else "fail",
                len(loaded.rows) + loaded.load_errors, loaded.load_errors,
                "linhas ilegíveis (JSON/CSV corrompido ou truncado)" if loaded.load_errors else "",
                loaded.error_samples))
        for cfg in ds.get("checks", []):
            results.append(_run_check(loaded.rows, ctx, name, cfg))
    return results


def has_blocking_failure(results: list[CheckResult]) -> bool:
    return any(r.severity == "error" and r.status != "pass" for r in results)


def write_report(results: list[CheckResult], out_dir: Path | None = None) -> Path:
    out_dir = out_dir or REPO_ROOT / "data" / "quality_reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"quality_{stamp}.json"
    path.write_text(json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False, default=str),
                    encoding="utf-8")
    return path

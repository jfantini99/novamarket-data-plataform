"""Convenções do data lake (ver docs/architecture/data-lake-conventions.md)."""

from __future__ import annotations

from datetime import date, datetime

LAYERS = ("raw", "staging", "processed", "curated", "quarantine", "archive")


def _as_date(day: date | datetime | str) -> date:
    if isinstance(day, datetime):
        return day.date()
    if isinstance(day, str):
        return date.fromisoformat(day[:10])
    return day


def partition_path(layer: str, domain: str, entity: str, day: date | datetime | str) -> str:
    """`<camada>/<domínio>/<entidade>/year=YYYY/month=MM/day=DD/`"""
    if layer not in LAYERS:
        raise ValueError(f"camada inválida: {layer}")
    d = _as_date(day)
    return f"{layer}/{domain}/{entity}/year={d:%Y}/month={d:%m}/day={d:%d}/"


def raw_key(domain: str, entity: str, day: date | datetime | str, filename: str) -> str:
    return partition_path("raw", domain, entity, day) + filename

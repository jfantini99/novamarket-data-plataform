"""Leitura de tickets (tickets/*.yaml) e incidentes (incidents/*.yaml).

As causas raiz ficam em .novamarket/_sealed/ e NUNCA são lidas por este módulo.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
STATES = ("BACKLOG", "READY", "IN_PROGRESS", "BLOCKED", "REVIEW", "DONE")


def _load_dir(directory: Path) -> list[dict]:
    items = []
    for path in sorted(directory.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        data.setdefault("id", path.stem)
        items.append(data)
    return items


def load_tickets(root: Path = ROOT) -> list[dict]:
    return _load_dir(root / "tickets")


def load_incidents(root: Path = ROOT) -> list[dict]:
    return _load_dir(root / "incidents")


def find(items: list[dict], item_id: str) -> dict | None:
    wanted = item_id.strip().upper()
    return next((i for i in items if str(i["id"]).upper() == wanted), None)


def visible_tickets(tickets: list[dict]) -> list[dict]:
    """Tickets com dependências ainda abertas ficam BLOCKED; BACKLOG não aparece como ativo."""
    done = {t["id"] for t in tickets if t.get("status") == "DONE"}
    out = []
    for t in tickets:
        deps = set(t.get("depends_on") or [])
        status = t.get("status", "BACKLOG")
        if status in ("READY", "IN_PROGRESS") and deps - done:
            status = "BLOCKED"
        out.append({**t, "status": status})
    return out

from __future__ import annotations

from datetime import UTC, datetime


def parse_ts(value) -> datetime | None:
    """Interpreta timestamps de formatos mistos. Sem fuso => assume UTC. Inválido => None."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)

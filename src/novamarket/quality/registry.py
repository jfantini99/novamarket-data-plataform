"""Registro de checks. Para criar um check novo, escreva uma função e decore com @check."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class Outcome:
    """Resultado de um check: quantas linhas falharam e exemplos para investigação."""

    failed: int
    samples: list = field(default_factory=list)
    message: str = ""
    total: int | None = None  # padrão: número de linhas do dataset


# assinatura: fn(rows, ctx, **parametros) -> Outcome
CheckFn = Callable[..., Outcome]
REGISTRY: dict[str, CheckFn] = {}


def check(name: str) -> Callable[[CheckFn], CheckFn]:
    def decorator(fn: CheckFn) -> CheckFn:
        if name in REGISTRY:
            raise ValueError(f"check já registrado: {name}")
        REGISTRY[name] = fn
        return fn

    return decorator

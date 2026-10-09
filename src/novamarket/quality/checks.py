"""Checks embutidos. Cada um recebe as linhas (lista de dicts), o contexto e seus parâmetros."""

from __future__ import annotations

import re
from collections import Counter
from datetime import timedelta

from novamarket.quality.registry import Outcome, check
from novamarket.quality.timeutil import parse_ts

SAMPLE_SIZE = 5


def _is_null(v) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")


def _sample(rows, predicate, column, key=None):
    """Até SAMPLE_SIZE exemplos de linhas que satisfazem `predicate`."""
    out = []
    for row in rows:
        if predicate(row):
            item = {column: row.get(column)}
            if key:
                item = {key: row.get(key), **item}
            out.append(item)
            if len(out) >= SAMPLE_SIZE:
                break
    return out


@check("not_null")
def not_null(rows, ctx, column, key=None):
    """Coluna não pode ser nula nem vazia."""
    bad = lambda r: _is_null(r.get(column))  # noqa: E731
    return Outcome(sum(1 for r in rows if bad(r)), _sample(rows, bad, column, key))


@check("unique")
def unique(rows, ctx, column=None, columns=None, key=None):
    """Valores (ou combinação de colunas) não podem se repetir."""
    cols = columns or [column]
    counts = Counter(tuple(r.get(c) for c in cols) for r in rows if not all(_is_null(r.get(c)) for c in cols))
    dups = {k: n for k, n in counts.items() if n > 1}
    failed = sum(n - 1 for n in dups.values())  # linhas "sobrando"
    samples = [{"value": list(k) if len(k) > 1 else k[0], "occurrences": n}
               for k, n in list(dups.items())[:SAMPLE_SIZE]]
    return Outcome(failed, samples)


@check("accepted_values")
def accepted_values(rows, ctx, column, values, allow_null=True, key=None):
    """Valor precisa estar na lista permitida."""
    allowed = set(values)
    bad = lambda r: (r.get(column) not in allowed) and not (allow_null and _is_null(r.get(column)))  # noqa: E731
    return Outcome(sum(1 for r in rows if bad(r)), _sample(rows, bad, column, key))


@check("range")
def value_range(rows, ctx, column, min=None, max=None, key=None):  # noqa: A002
    """Valor numérico dentro de [min, max]."""
    def bad(r):
        v = r.get(column)
        if _is_null(v):
            return False
        try:
            x = float(str(v).replace(",", ".")) if isinstance(v, str) else float(v)
        except ValueError:
            return True
        return (min is not None and x < min) or (max is not None and x > max)

    return Outcome(sum(1 for r in rows if bad(r)), _sample(rows, bad, column, key))


@check("regex")
def regex(rows, ctx, column, pattern, key=None):
    """Valor precisa casar por inteiro com a expressão regular."""
    rx = re.compile(pattern)
    bad = lambda r: (not _is_null(r.get(column))) and not rx.fullmatch(str(r.get(column)))  # noqa: E731
    return Outcome(sum(1 for r in rows if bad(r)), _sample(rows, bad, column, key))


@check("row_count")
def row_count(rows, ctx, min=0, max=None):  # noqa: A002
    """Volume: número de linhas dentro do esperado."""
    n = len(rows)
    ok = n >= min and (max is None or n <= max)
    return Outcome(0 if ok else 1, [{"rows": n}], f"{n} linhas (esperado entre {min} e {max})", total=1)


@check("freshness")
def freshness(rows, ctx, column, max_age_hours):
    """Dado mais recente não pode ser mais velho que max_age_hours."""
    stamps = [t for t in (parse_ts(r.get(column)) for r in rows) if t]
    if not stamps:
        return Outcome(1, [], f"nenhum timestamp válido em {column}", total=1)
    newest = max(stamps)
    age = ctx.as_of - newest
    ok = age <= timedelta(hours=max_age_hours)
    return Outcome(0 if ok else 1, [{"newest": newest.isoformat(), "age_hours": round(age.total_seconds() / 3600, 1)}],
                   total=1)


@check("referential_integrity")
def referential_integrity(rows, ctx, column, ref_dataset, ref_column):
    """Todo valor precisa existir no dataset de referência."""
    valid = {r.get(ref_column) for r in ctx.rows_of(ref_dataset)}
    bad = lambda r: (not _is_null(r.get(column))) and r.get(column) not in valid  # noqa: E731
    return Outcome(sum(1 for r in rows if bad(r)), _sample(rows, bad, column))


@check("schema")
def schema(rows, ctx, expected_columns, allow_extra=False):
    """Colunas esperadas presentes (e sem extras, se allow_extra=false)."""
    expected = set(expected_columns)
    missing, extra = Counter(), Counter()
    bad_rows = 0
    for r in rows:
        keys = {k for k in r if not k.startswith("_")}
        m, e = expected - keys, (set() if allow_extra else keys - expected)
        if m or e:
            bad_rows += 1
        missing.update(m)
        extra.update(e)
    samples = [{"missing": dict(missing)}] if missing else []
    if extra:
        samples.append({"unexpected": dict(extra)})
    return Outcome(bad_rows, samples)

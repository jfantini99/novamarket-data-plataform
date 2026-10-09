"""Leitura dos datasets: arquivos JSONL/CSV, tabelas do Postgres e objetos no S3."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Loaded:
    rows: list[dict]
    load_errors: int = 0  # linhas ilegíveis (JSON inválido, CSV truncado)
    error_samples: list = field(default_factory=list)


def parse_jsonl(lines, origin: str = "") -> Loaded:
    out = Loaded([])
    for n, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError("não é um objeto")
            out.rows.append(obj)
        except ValueError:
            out.load_errors += 1
            if len(out.error_samples) < 5:
                out.error_samples.append({"origin": origin, "line": n, "text": line[:60]})
    return out


def parse_csv(text: str, origin: str = "") -> Loaded:
    out = Loaded([])
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    for row in reader:
        # linha curta => valores None; linha longa => chave None (restkey)
        if None in row or any(v is None for v in row.values()):
            out.load_errors += 1
            if len(out.error_samples) < 5:
                out.error_samples.append({"origin": origin, "line": reader.line_num})
            continue
        out.rows.append(row)
    return out


def _merge(parts: list[Loaded]) -> Loaded:
    merged = Loaded([])
    for p in parts:
        merged.rows.extend(p.rows)
        merged.load_errors += p.load_errors
        merged.error_samples.extend(p.error_samples[: 5 - len(merged.error_samples)])
    return merged


def _files(repo_root: Path, pattern: str) -> list[Path]:
    base = Path(pattern)
    if base.is_absolute():
        files = sorted(base.parent.glob(base.name))
    else:
        files = sorted(repo_root.glob(pattern))
    if not files:
        raise FileNotFoundError(f"nenhum arquivo para '{pattern}' (rode `novamarket data generate`?)")
    return files


def load_source(source: dict, repo_root: Path) -> Loaded:
    kind = source["type"]
    if kind == "jsonl":
        return _merge([parse_jsonl(f.read_text(encoding="utf-8").splitlines(), f.name)
                       for f in _files(repo_root, source["path"])])
    if kind == "csv":
        return _merge([parse_csv(f.read_text(encoding="utf-8"), f.name)
                       for f in _files(repo_root, source["path"])])
    if kind == "postgres":
        from psycopg.rows import dict_row

        from novamarket.datagen.erp_loader import connect

        with connect() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(source["query"])
            return Loaded(list(cur.fetchall()))
    if kind == "s3":
        from novamarket.aws import lake_bucket, s3_client

        client, bucket = s3_client(), source.get("bucket") or lake_bucket()
        parts = []
        for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=source["prefix"]):
            for obj in page.get("Contents", []):
                if obj["Key"].endswith("/"):
                    continue
                body = client.get_object(Bucket=bucket, Key=obj["Key"])["Body"].read().decode("utf-8")
                parts.append(parse_jsonl(body.splitlines(), obj["Key"]) if source["format"] == "jsonl"
                             else parse_csv(body, obj["Key"]))
        if not parts:
            raise FileNotFoundError(f"nada em s3://{bucket}/{source['prefix']}")
        return _merge(parts)
    raise ValueError(f"tipo de fonte desconhecido: {kind}")

"""Verificação do ambiente local (somente leitura)."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
from dataclasses import dataclass


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    hint: str = ""


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return True
    except OSError:
        return False


def _tool(name: str, args: list[str]) -> Check:
    path = shutil.which(name)
    if not path:
        return Check(name, False, "não encontrado no PATH", f"instale {name} (ver docs/development)")
    try:
        out = subprocess.run([path, *args], capture_output=True, text=True, timeout=20, check=False)
        line = (out.stdout or out.stderr).strip().splitlines()
        return Check(name, True, line[0] if line else "ok")
    except (OSError, subprocess.SubprocessError) as exc:
        return Check(name, False, str(exc))


def run_checks() -> list[Check]:
    erp_port = int(os.getenv("ERP_DB_PORT", "5433"))
    checks = [
        _tool("docker", ["--version"]),
        _tool("terraform", ["version"]),
        _tool("aws", ["--version"]),
    ]
    services = [
        ("ERP PostgreSQL", erp_port),
        ("S3 local (RustFS)", 9000),
        ("APIs mock", 8081),
        ("Airflow UI", 8080),
    ]
    for name, port in services:
        up = _port_open("localhost", port)
        checks.append(Check(name, up, f"localhost:{port} {'aberto' if up else 'fechado'}",
                            "" if up else "make up (Airflow: make airflow)"))
    return checks

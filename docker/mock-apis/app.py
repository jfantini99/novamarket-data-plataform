"""APIs simuladas da NovaMarket: E-commerce e Marketing.

Servem os arquivos de data/generated/ (montado em /data) com paginação e filtro
`updated_since`. Podem falhar de propósito (HTTP 500, lentidão, timeout).
Autenticação: header X-API-Key.
"""

import asyncio
import json
import os
import random
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request

DATA = Path(os.environ.get("DATA_DIR", "/data"))
API_KEY = os.environ.get("MOCK_API_KEY", "")
chaos = {
    "rate_500": float(os.environ.get("CHAOS_500_RATE", "0.02")),
    "rate_slow": float(os.environ.get("CHAOS_SLOW_RATE", "0.02")),
    "slow_seconds": float(os.environ.get("CHAOS_SLOW_SECONDS", "5")),
    "rate_timeout": float(os.environ.get("CHAOS_TIMEOUT_RATE", "0.0")),
}

RESOURCES = {
    "ecommerce": {
        "customers": "ecommerce/customers.jsonl",
        "orders": "ecommerce/orders.jsonl",
        "order_items": "ecommerce/order_items.jsonl",
        "payments": "ecommerce/payments.jsonl",
    },
    "marketing": {
        "campaigns": "marketing/campaigns.jsonl",
        "impressions": "marketing/impressions.jsonl",
        "clicks": "marketing/clicks.jsonl",
        "conversions": "marketing/conversions.jsonl",
    },
}
_cache: dict[str, list[dict]] = {}


def load(rel: str) -> list[dict]:
    """Carrega o arquivo, ordena pelo timestamp interno `_ts` e remove o campo `_ts`."""
    if rel not in _cache:
        path = DATA / rel
        rows = []
        if path.exists():
            with open(path, encoding="utf-8") as f:
                for line in f:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue  # a API não entrega linhas corrompidas
        rows.sort(key=lambda r: r.get("_ts", ""))
        _cache[rel] = rows
    return _cache[rel]


async def chaos_gate(request: Request) -> None:
    if request.url.path.startswith(("/health", "/_admin")):
        return
    r = random.random()
    if r < chaos["rate_timeout"]:
        await asyncio.sleep(120)
    elif r < chaos["rate_timeout"] + chaos["rate_500"]:
        raise HTTPException(status_code=500, detail="internal server error")
    elif r < chaos["rate_timeout"] + chaos["rate_500"] + chaos["rate_slow"]:
        await asyncio.sleep(chaos["slow_seconds"])


async def auth(x_api_key: str = Header(default="")) -> None:
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")


app = FastAPI(title="NovaMarket mock APIs", dependencies=[Depends(chaos_gate)])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/_admin/chaos")
def set_chaos(settings: dict, _: None = Depends(auth)) -> dict:
    """Ajusta as falhas em tempo de execução. Ex.: {"rate_500": 0.5}"""
    for k, v in settings.items():
        if k in chaos:
            chaos[k] = float(v)
    return chaos


def make_router(domain: str):
    from fastapi import APIRouter

    router = APIRouter(prefix=f"/{domain}/v1", dependencies=[Depends(auth)])

    def add(name: str, rel: str):
        @router.get(f"/{name}", name=f"list_{name}")
        def list_resource(
            updated_since: str | None = Query(None, description="ISO-8601 UTC"),
            page: int = Query(1, ge=1),
            page_size: int = Query(500, ge=1, le=1000),
        ) -> dict:
            rows = load(rel)
            if updated_since:
                rows = [r for r in rows if r.get("_ts", "") >= updated_since]
            start = (page - 1) * page_size
            chunk = rows[start : start + page_size]
            data = [{k: v for k, v in r.items() if k != "_ts"} for r in chunk]
            has_next = start + page_size < len(rows)
            return {"data": data, "page": page, "next_page": page + 1 if has_next else None,
                    "total": len(rows)}

    for name, rel in RESOURCES[domain].items():
        add(name, rel)
    return router


for _domain in RESOURCES:
    app.include_router(make_router(_domain))

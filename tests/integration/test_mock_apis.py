"""Testes das APIs simuladas. Requer `make up` e dados gerados (`novamarket data generate`)."""

import os
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
BASE = os.environ.get("MOCK_API_URL", "http://localhost:8081")
HEADERS = {"X-API-Key": os.environ.get("MOCK_API_KEY", "")}


@pytest.fixture(scope="module", autouse=True)
def api_up():
    try:
        requests.get(f"{BASE}/health", timeout=3).raise_for_status()
    except requests.RequestException:
        pytest.skip("mock-apis indisponível (rode `make up`)")
    # desliga as falhas para testes determinísticos e restaura ao final
    previous = requests.post(f"{BASE}/_admin/chaos", json={"rate_500": 0, "rate_slow": 0},
                             headers=HEADERS, timeout=5).json()
    yield
    requests.post(f"{BASE}/_admin/chaos", json={"rate_500": 0.02, "rate_slow": 0.02},
                  headers=HEADERS, timeout=5)
    assert previous is not None


def get(path, **params):
    return requests.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=10)


def test_requires_api_key():
    assert requests.get(f"{BASE}/ecommerce/v1/orders", timeout=5).status_code == 401


def test_pagination_and_internal_field_hidden():
    body = get("/ecommerce/v1/orders", page_size=10).json()
    assert len(body["data"]) == 10 and body["next_page"] == 2
    assert all("_ts" not in row for row in body["data"])


def test_updated_since_filters():
    everything = get("/ecommerce/v1/orders", page_size=1).json()["total"]
    recent = get("/ecommerce/v1/orders", page_size=1, updated_since="2026-10-08T00:00:00Z").json()["total"]
    assert 0 < recent < everything


def test_chaos_returns_500():
    requests.post(f"{BASE}/_admin/chaos", json={"rate_500": 1}, headers=HEADERS, timeout=5)
    try:
        assert get("/marketing/v1/campaigns").status_code == 500
    finally:
        requests.post(f"{BASE}/_admin/chaos", json={"rate_500": 0}, headers=HEADERS, timeout=5)

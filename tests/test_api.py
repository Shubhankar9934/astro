import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from astro.api.app import app


def test_system_health():
    with TestClient(app) as c:
        r = c.get("/api/v1/system/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "model_loaded" in body
    assert "ibkr_connect_error" in body


def test_system_config():
    with TestClient(app) as c:
        r = c.get("/api/v1/system/config")
    assert r.status_code == 200
    assert "agents" in r.json()

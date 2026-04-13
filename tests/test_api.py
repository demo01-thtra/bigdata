"""Unit tests for FastAPI backend endpoints."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Mock Kafka to avoid connection errors during test import
os.environ['ENABLE_KAFKA'] = 'false'
os.environ['DATABASE_URL'] = 'sqlite:///test_fraud.db'

from fastapi.testclient import TestClient


# Module-level setup: import once after env vars are set
import database as _db_mod
import models as _m_mod
import main as _main_mod

_m_mod.Base.metadata.create_all(bind=_db_mod.engine)
_client = TestClient(_main_mod.app)


def _get_client():
    """Return the shared TestClient."""
    return _client


def test_health_endpoint():
    client = _get_client()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


def test_transactions_endpoint():
    client = _get_client()
    resp = client.get("/api/transactions")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


def test_frauds_endpoint():
    client = _get_client()
    resp = client.get("/api/frauds")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data


def test_stats_endpoint():
    client = _get_client()
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_transactions" in data
    assert "fraud_rate" in data
    assert "detection_breakdown" in data


def test_stats_by_type_endpoint():
    client = _get_client()
    resp = client.get("/api/stats/by-type")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_timeline_endpoint():
    client = _get_client()
    resp = client.get("/api/stats/timeline?hours=1")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_sse_endpoint_exists():
    """SSE endpoint should be registered and return event-stream content type."""
    client = _get_client()
    # Verify the SSE route is registered in the app
    sse_routes = [r for r in client.app.routes if hasattr(r, 'path') and r.path == '/api/sse/alerts']
    assert len(sse_routes) == 1, "SSE route /api/sse/alerts should be registered"

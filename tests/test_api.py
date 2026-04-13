"""Unit tests for FastAPI backend endpoints."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Mock Kafka to avoid connection errors during test import
os.environ['ENABLE_KAFKA'] = 'false'
os.environ['DATABASE_URL'] = 'sqlite:///test_fraud.db'

from fastapi.testclient import TestClient


def _get_client():
    """Create a TestClient with in-memory SQLite."""
    # Re-import to pick up env overrides
    import importlib
    import database as db_mod
    importlib.reload(db_mod)
    import models as m_mod
    importlib.reload(m_mod)
    import main as main_mod
    importlib.reload(main_mod)
    m_mod.Base.metadata.create_all(bind=db_mod.engine)
    return TestClient(main_mod.app)


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
    """SSE endpoint should return streaming response."""
    client = _get_client()
    # SSE is a streaming endpoint; just verify it exists and returns 200
    with client.stream("GET", "/api/sse/alerts") as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

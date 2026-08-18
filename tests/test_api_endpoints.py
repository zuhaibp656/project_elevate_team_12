"""Automated integration tests for FastAPI Endpoints & Distributed Tracing Headers."""
from fastapi.testclient import TestClient
from ui.server import app

client = TestClient(app)


def test_health_check():
    """Verify /api/health returns healthy status code."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_w3c_distributed_tracing_propagation():
    """Verify W3C traceparent and X-Correlation-ID headers are processed and returned."""
    custom_trace = "trace-custom-991"
    response = client.get("/api/health", headers={"X-Correlation-ID": custom_trace})
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == custom_trace
    assert "traceparent" in response.headers
    assert "X-Response-Time-Ms" in response.headers


def test_hub_endpoint_dynamic_structure():
    """Verify /api/hub returns structured live telemetry fields."""
    response = client.get("/api/hub")
    assert response.status_code == 200
    data = response.json()
    assert "balances" in data
    assert "vacation" in data["balances"]
    assert "sick" in data["balances"]
    assert "profile" in data
    assert "tickets" in data
    assert isinstance(data["tickets"], list)

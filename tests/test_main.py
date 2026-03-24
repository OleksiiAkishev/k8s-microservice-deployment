import time
from fastapi.testclient import TestClient
from main import app, calculate_uptime

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Kubernetes python Fast API"}

def test_health_check():
    response = client.get("/health")
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert isinstance(data["timestamp"], float)

def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_request_total" in response.text

def test_calculate_uptime():
    start = time.time()
    time.sleep(0.1)
    uptime = calculate_uptime(start)
    assert uptime > 0
    assert uptime >= 0.1
from fastapi.testclient import TestClient

from fastapi_bootstrap.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "docs_url" in response.json()
    assert "api_v1_url" in response.json()
    assert "description" in response.json()
    assert "version" in response.json()


def test_api_v1():
    response = client.get("/api/v1")
    assert response.status_code == 200
    assert response.json()["version"] == "v1"

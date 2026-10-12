"""
Integration tests for FastAPI endpoints (Section 22).
"""
import pytest
from fastapi.testclient import TestClient
from app.api.routes import app

client = TestClient(app)


def test_api_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "History-RAG"
    assert "version" in data


def test_api_repository_status():
    resp = client.get("/repository-status?repository_id=netbox")
    assert resp.status_code == 200
    data = resp.json()
    assert data["repository_id"] == "netbox"
    assert "capabilities" in data
    assert "stats" in data
    assert data["mode"] == "Enhanced"


def test_api_analyze_change():
    payload = {
        "repository_id": "netbox",
        "proposed_change": "Refactor DCIM interface IP assignment logic",
        "system_mode": "History-RAG",
        "top_k_tests": 3
    }
    resp = client.post("/analyze-change", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "affected_components" in data
    assert "impact_level" in data
    assert "recommended_tests" in data
    assert "confidence" in data
    assert "limitations" in data
    assert len(data["affected_components"]) > 0


def test_api_ask():
    payload = {
        "repository_id": "netbox",
        "question": "Why was IPAM VRF isolation implemented this way?",
        "system_mode": "History-RAG"
    }
    resp = client.post("/ask", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "confidence" in data
    assert "citations" in data


def test_api_list_repositories():
    resp = client.get("/repositories")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    repo_ids = [r["repository_id"] for r in data]
    assert "netbox" in repo_ids


def test_api_index_custom_repo():
    payload = {
        "repository_url": "https://github.com/mock/sample_microservice",
        "repository_id": "sample_microservice"
    }
    resp = client.post("/index", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["repository_id"] == "sample_microservice"
    assert data["status"] == "success"
    assert "profile" in data


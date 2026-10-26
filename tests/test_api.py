"""
Integration tests for FastAPI endpoints (Section 22).
"""
import os
import pytest
from app.api.routes import (
    app,
    health_check,
    repository_status,
    analyze_change,
    ask_question,
    list_repositories,
    index_repository,
    index_zip_repository,
    generate_candidate_tests,
    evaluate_gate,
    trigger_rollback,
    get_deployment_ledger,
    prometheus_metrics,
    AnalyzeChangeRequest,
    AskRequest,
    IndexRequest,
    IndexZipRequest,
    GenerateCandidateTestsRequest,
    GateEvaluationRequest,
    RollbackRequest
)


def test_api_health_check():
    data = health_check()
    assert data["status"] == "healthy"
    assert data["service"] == "History-RAG"
    assert "version" in data


def test_api_repository_status():
    data = repository_status(repository_id="netbox")
    assert data["repository_id"] == "netbox"
    assert "capabilities" in data
    assert "stats" in data
    assert data["mode"] == "Enhanced"


def test_api_analyze_change():
    req = AnalyzeChangeRequest(
        repository_id="netbox",
        proposed_change="Refactor DCIM interface IP assignment logic",
        system_mode="History-RAG",
        top_k_tests=3
    )
    resp = analyze_change(req)
    data = resp.model_dump()
    assert "affected_components" in data
    assert "impact_level" in data
    assert "recommended_tests" in data
    assert "confidence" in data
    assert "limitations" in data
    assert len(data["affected_components"]) > 0


def test_api_ask():
    req = AskRequest(
        repository_id="netbox",
        question="Why was IPAM VRF isolation implemented this way?",
        system_mode="History-RAG"
    )
    data = ask_question(req)
    assert "answer" in data
    assert "confidence" in data
    assert "citations" in data


def test_api_list_repositories():
    data = list_repositories()
    assert isinstance(data, list)
    repo_ids = [r["repository_id"] for r in data]
    assert "netbox" in repo_ids


def test_api_index_custom_repo():
    req = IndexRequest(
        repository_url="https://github.com/mock/sample_microservice",
        repository_id="sample_microservice"
    )
    data = index_repository(req)
    assert data["repository_id"] == "sample_microservice"
    assert data["status"] == "success"
    assert "profile" in data


def test_api_generate_candidate_tests():
    req = GenerateCandidateTestsRequest(
        repository_id="netbox",
        proposed_change="Refactor DCIM interface IP assignment logic",
        system_mode="History-RAG",
        top_k=2
    )
    data = generate_candidate_tests(req)
    assert data["repository_id"] == "netbox"
    assert "candidate_tests" in data
    assert len(data["candidate_tests"]) == 2
    assert data["candidate_tests"][0]["ast_valid"] is True


def test_api_evaluate_gate():
    req = GateEvaluationRequest(
        change_analysis={"impact_level": "HIGH", "confidence": 0.88, "affected_components": [{"component": "dcim"}]},
        test_results={"status": "FAIL", "failed": 1, "passed": 0},
        block_on_high_impact=True
    )
    data = evaluate_gate(req)
    assert data["decision"] == "BLOCKED"
    assert data["gate_passed"] is False


def test_api_devops_rollback_and_deployments():
    # Trigger rollback
    rollback_req = RollbackRequest(
        failed_image="historyrag:bad-build-123",
        reason="Automated Health Check Failure",
        environment="qa"
    )
    rollback_res = trigger_rollback(rollback_req)
    assert rollback_res["status"] == "ROLLBACK_SUCCESSFUL"
    assert "restored_image" in rollback_res

    # Check ledger
    ledger = get_deployment_ledger()
    assert "current_deployed_image" in ledger
    assert "known_good_image" in ledger
    assert len(ledger["history"]) >= 1


def test_api_prometheus_metrics():
    resp = prometheus_metrics()
    assert resp.status_code == 200
    assert b"historyrag_" in resp.body


def test_api_index_zip_repository():
    import tempfile, zipfile, shutil
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "api_test_service.zip")
    repo_id = "api_zip_test"

    try:
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("api_test_service/main.py", "def run():\n    return 'ok'\n")
            z.writestr("api_test_service/tests/test_main.py", "def test_run():\n    assert True\n")

        req = IndexZipRequest(zip_path=zip_path, repository_id=repo_id)
        res = index_zip_repository(req)
        assert res["status"] == "success"
        assert res["repository_id"] == repo_id
        assert "zip_ingestion" in res
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        shutil.rmtree(os.path.join("data", "raw", repo_id), ignore_errors=True)
        cfg_file = os.path.join("configs", f"{repo_id}.yaml")
        if os.path.exists(cfg_file):
            os.remove(cfg_file)

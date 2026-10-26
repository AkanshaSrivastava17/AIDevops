"""
Unit tests for Advanced CI/CD Policy Gates and Auto-Rollback (Section 33, Enhancements #7 & #8).
"""
import pytest
from app.devops.pipeline_gate import AdvancedCIDCGate, DeploymentManager


def test_gate_approved_when_all_pass():
    gate = AdvancedCIDCGate()
    analysis = {
        "impact_level": "MEDIUM",
        "confidence": 0.85,
        "affected_components": [{"component": "utilities", "score": 0.45}],
        "recommended_tests": [{"test_file": "netbox/utilities/tests/test_utils.py"}]
    }
    test_results = {
        "status": "PASS",
        "tests_executed": 1,
        "passed": 1,
        "failed": 0
    }
    qa_health = {"status": "healthy", "status_code": 200}

    eval_result = gate.evaluate(analysis, test_results, qa_health)
    assert eval_result["decision"] == "APPROVED"
    assert eval_result["gate_passed"] is True
    assert len(eval_result["blocking_reasons"]) == 0


def test_gate_blocked_on_high_impact_test_failure():
    gate = AdvancedCIDCGate(block_on_high_impact_failure=True)
    analysis = {
        "impact_level": "HIGH",
        "confidence": 0.88,
        "affected_components": [{"component": "dcim", "score": 0.85}],
        "recommended_tests": [{"test_file": "netbox/dcim/tests/test_dcim.py"}]
    }
    test_results = {
        "status": "FAIL",
        "tests_executed": 1,
        "passed": 0,
        "failed": 1
    }

    eval_result = gate.evaluate(analysis, test_results)
    assert eval_result["decision"] == "BLOCKED"
    assert eval_result["gate_passed"] is False
    assert any("High-impact" in r or "regression" in r for r in eval_result["blocking_reasons"])


def test_gate_warning_on_low_confidence():
    gate = AdvancedCIDCGate(min_confidence_score=0.70)
    analysis = {
        "impact_level": "LOW",
        "confidence": 0.52,
        "affected_components": [{"component": "extras", "score": 0.20}],
        "recommended_tests": []
    }
    test_results = {
        "status": "PASS",
        "tests_executed": 0,
        "passed": 0,
        "failed": 0
    }

    eval_result = gate.evaluate(analysis, test_results)
    assert eval_result["decision"] == "WARNING"
    assert eval_result["gate_passed"] is True
    assert any("Low AI analysis confidence" in w for w in eval_result["warnings"])


def test_gate_blocked_on_qa_health_failure():
    gate = AdvancedCIDCGate()
    analysis = {
        "impact_level": "LOW",
        "confidence": 0.85,
        "affected_components": [{"component": "utilities", "score": 0.2}],
        "recommended_tests": []
    }
    test_results = {"status": "PASS", "failed": 0}
    qa_unhealthy = {"status": "unhealthy", "error": "Container connection refused"}

    eval_result = gate.evaluate(analysis, test_results, qa_unhealthy)
    assert eval_result["decision"] == "BLOCKED"
    assert eval_result["gate_passed"] is False
    assert eval_result["rollback_required"] is True


def test_deployment_manager_auto_rollback():
    manager = DeploymentManager(default_known_good_image="historyrag:v1.0.0-stable")
    candidate_tag = "historyrag:commit-fail-qa"

    # Step 1: Deploy candidate
    dep = manager.deploy_candidate(candidate_tag, environment="qa")
    assert manager.current_deployed_image == candidate_tag
    assert dep["status"] == "DEPLOYED"

    # Step 2: Health check fails
    health = manager.check_qa_health(simulate_unhealthy=True)
    assert health["status"] == "unhealthy"

    # Step 3: Trigger auto-rollback
    rollback_event = manager.trigger_auto_rollback(
        failed_image=candidate_tag,
        reason="QA Health Probe Failed (HTTP 503)"
    )
    assert rollback_event["status"] == "ROLLBACK_SUCCESSFUL"
    assert rollback_event["restored_image"] == "historyrag:v1.0.0-stable"
    assert manager.current_deployed_image == "historyrag:v1.0.0-stable"

    # Step 4: Verify deployment history
    history = manager.deployment_history
    assert len(history) >= 3
    assert history[-1]["status"] == "RESTORED_VIA_ROLLBACK"


def test_deployment_manager_promotion():
    manager = DeploymentManager(default_known_good_image="historyrag:v1.0.0-stable")
    candidate_tag = "historyrag:commit-approved"

    manager.deploy_candidate(candidate_tag)
    manager.promote_to_known_good(candidate_tag)

    assert manager.known_good_image == candidate_tag

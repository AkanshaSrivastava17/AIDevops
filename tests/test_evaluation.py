"""
Unit tests for evaluation metrics computation and benchmark case execution (Sections 16, 17).
"""
import pytest
from scripts.run_evaluation import BenchmarkEvaluator


def test_evaluator_metrics_computation():
    evaluator = BenchmarkEvaluator("netbox")
    case = {
        "case_id": 999,
        "change_description": "Refactor interface IP assignment to validate IP address VRF containment",
        "target_commit": "c999aa8f9e01b2c3d4e5f6a7b8c9d0e1f2a3b4c5",
        "parent_commit": "c998aa8f9e01b2c3d4e5f6a7b8c9d0e1f2a3b4c4",
        "target_time": "2023-05-01T00:00:00Z",
        "actual_changed_files": ["netbox/dcim/models/devices.py", "netbox/ipam/models/ip.py"],
        "actual_components": ["dcim", "ipam"],
        "available_tests": ["netbox/dcim/tests/test_devices.py", "netbox/ipam/tests/test_ipam.py"],
        "relevant_existing_tests": ["netbox/dcim/tests/test_devices.py", "netbox/ipam/tests/test_ipam.py"],
        "tests_added_by_change": [],
        "relevant_evidence": []
    }

    result = evaluator.evaluate_case(case, system_mode="History-RAG", top_k_tests=2)
    assert result["case_id"] == 999
    assert result["system_mode"] == "History-RAG"
    assert "comp_f1" in result
    assert "test_f1" in result
    assert result["supported_claim_rate"] > 0.8
    assert result["hallucination_rate"] < 0.1

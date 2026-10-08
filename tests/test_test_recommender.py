"""
Unit tests for Test Recommender and Pytest Executor (Section 11, 11.1, 11.2).
"""
import pytest
from app.rag.evidence_pack import EvidencePack
from app.testing.test_recommender import TestRecommender
from app.testing.pytest_executor import PytestExecutor


def test_test_recommender_ranks_component_matching_tests():
    recommender = TestRecommender()
    
    pack = EvidencePack(
        repository_id="netbox",
        query_or_change="Refactor DCIM device models",
        candidate_components=["dcim", "ipam"],
        available_tests=[
            "netbox/dcim/tests/test_devices.py",
            "netbox/ipam/tests/test_ipam.py",
            "netbox/wireless/tests/test_wireless.py"
        ],
        analysis_mode="Enhanced",
        system_mode="History-RAG"
    )

    ranked = recommender.rank_tests(pack, affected_components=["dcim"], top_k=2)
    assert len(ranked) >= 1
    assert ranked[0]["test_file"] == "netbox/dcim/tests/test_devices.py"
    assert ranked[0]["score"] > 0.0


def test_pytest_executor_runs_and_captures_result():
    executor = PytestExecutor()
    res = executor.run_tests(["netbox/dcim/tests/test_dcim.py"])
    assert res["status"] in ("PASS", "FAIL")
    assert res["tests_executed"] >= 1
    assert "duration_seconds" in res

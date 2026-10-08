"""
Unit tests for Impact Scoring Engine (Section 10.1, 10.2).
"""
import pytest
from app.rag.evidence_pack import EvidencePack
from app.impact.scoring_engine import ImpactScoringEngine


def test_scoring_engine_weights_and_ranking():
    engine = ImpactScoringEngine(w1_semantic=0.25, w2_dependency=0.25, w3_cochange=0.25, w4_test=0.25)
    
    pack = EvidencePack(
        repository_id="netbox",
        query_or_change="Refactor DCIM device interface validation",
        candidate_components=["dcim", "ipam", "circuits"],
        analysis_mode="Enhanced",
        system_mode="History-RAG",
        code_evidence=[{"component": "dcim", "similarity": 0.9}],
        dependency_evidence=[{"source_component": "dcim", "target_component": "ipam"}],
        cochange_evidence={"dcim": {"ipam": 5}},
        available_tests=["netbox/dcim/tests/test_devices.py"]
    )

    scores = engine.score_components(pack, system_mode="History-RAG", threshold_high=0.35)
    assert len(scores) == 3
    # dcim should be top ranked
    assert scores[0]["component"] == "dcim"
    assert scores[0]["impact_level"] == "HIGH"
    assert scores[0]["score"] > scores[1]["score"]


def test_scoring_engine_disables_cochange_in_coderag():
    engine = ImpactScoringEngine()
    
    pack = EvidencePack(
        repository_id="netbox",
        query_or_change="Refactor DCIM device interface validation",
        candidate_components=["dcim", "ipam"],
        analysis_mode="Enhanced",
        system_mode="Code-RAG",
        cochange_evidence={"dcim": {"ipam": 10}}
    )

    scores = engine.score_components(pack, system_mode="Code-RAG")
    for s in scores:
        assert s["breakdown"]["historical_cochange"] == 0.0


def test_scoring_engine_limited_mode_zeroes_dependency():
    engine = ImpactScoringEngine()
    
    pack = EvidencePack(
        repository_id="netbox",
        query_or_change="Change something in core",
        candidate_components=["core", "utils"],
        analysis_mode="Limited",
        system_mode="History-RAG",
        dependency_evidence=[{"source_component": "core", "target_component": "utils"}]
    )

    scores = engine.score_components(pack, system_mode="History-RAG")
    for s in scores:
        assert s["breakdown"]["dependency_evidence"] == 0.0

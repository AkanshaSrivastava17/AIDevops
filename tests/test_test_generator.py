"""
Unit tests for AI-Generated Candidate Tests (Section 33, Enhancement #2).
"""
import ast
import pytest
from app.rag.evidence_pack import EvidencePack
from app.testing.test_generator import CandidateTestGenerator


def test_candidate_test_generator_valid_ast():
    generator = CandidateTestGenerator()
    affected_components = [
        {"component": "dcim", "score": 0.85, "impact_level": "HIGH"},
        {"component": "ipam", "score": 0.62, "impact_level": "MEDIUM"}
    ]
    pack = EvidencePack(
        repository_id="netbox",
        query_or_change="Refactor DCIM interface IP assignment logic",
        candidate_components=["dcim", "ipam", "utilities"],
        analysis_mode="Enhanced",
        system_mode="History-RAG"
    )

    candidates = generator.generate_candidate_tests(
        proposed_change="Refactor DCIM interface IP assignment logic",
        affected_components=affected_components,
        evidence_pack=pack,
        top_k=3
    )

    assert len(candidates) == 3
    for candidate in candidates:
        assert candidate["ast_valid"] is True
        assert candidate["validation_status"] == "SYNTACTICALLY_VALID"
        assert candidate["review_status"] == "PENDING_HUMAN_REVIEW"
        assert candidate["framework"] == "pytest"
        # Explicitly verify that Python's compiler can parse the generated code without syntax errors
        parsed = ast.parse(candidate["test_code"])
        assert parsed is not None


def test_candidate_test_generator_structure():
    generator = CandidateTestGenerator()
    affected = [{"component": "wireless", "score": 0.70, "impact_level": "MEDIUM"}]

    candidates = generator.generate_candidate_tests(
        proposed_change="Update antenna wireless frequency bands",
        affected_components=affected,
        top_k=2
    )

    assert len(candidates) >= 1
    c = candidates[0]
    assert "wireless" in c["test_name"].lower()
    assert c["target_component"] == "wireless"
    assert "rationale" in c and len(c["rationale"]) > 0
    assert "@pytest.mark.ai_candidate" in c["test_code"]


def test_candidate_test_generator_empty_components():
    generator = CandidateTestGenerator()
    candidates = generator.generate_candidate_tests(
        proposed_change="Harmless documentation edit",
        affected_components=[],
        top_k=3
    )
    assert candidates == []


def test_candidate_test_generator_syntax_validation_helper():
    generator = CandidateTestGenerator()
    valid_code = "def test_sample():\n    assert 1 + 1 == 2\n"
    invalid_code = "def test_broken(:\n    assert 1 == 1"
    
    assert generator.validate_test_syntax(valid_code) is True
    assert generator.validate_test_syntax(invalid_code) is False

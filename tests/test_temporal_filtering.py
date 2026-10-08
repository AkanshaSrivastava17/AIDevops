"""
Unit tests for Temporal Leakage Prevention (Sections 8.1, 16.3).
Verifies that no future information or target change artifacts leak into retrieval.
"""
import pytest
from app.ingestion.schema import NormalizedDocument, DocumentType, EventType
from app.rag.temporal_filter import TemporalLeakageFilter


def test_temporal_filter_strictly_excludes_future_events():
    target_time = "2023-06-01T12:00:00Z"
    t_filter = TemporalLeakageFilter(target_time=target_time)

    # Pre-T event (valid)
    doc_past = NormalizedDocument(
        document_id="past-01",
        repository_id="netbox",
        type=DocumentType.COMMIT,
        event_timestamp="2023-05-30T10:00:00Z",
        event_type=EventType.COMMIT,
        content="Past commit before T"
    )

    # Post-T event (future leakage - invalid)
    doc_future = NormalizedDocument(
        document_id="future-01",
        repository_id="netbox",
        type=DocumentType.COMMIT,
        event_timestamp="2023-06-02T10:00:00Z",
        event_type=EventType.COMMIT,
        content="Future commit after T"
    )

    assert t_filter.is_valid_evidence(doc_past) is True
    assert t_filter.is_valid_evidence(doc_future) is False


def test_temporal_filter_excludes_target_commit_and_tests():
    target_sha = "c999aa8f9e01b2c3d4e5f6a7b8c9d0e1f2a3b4c5"
    added_test = "netbox/dcim/tests/test_new_feature.py"
    
    t_filter = TemporalLeakageFilter(
        target_time="2023-06-01T12:00:00Z",
        excluded_commit_shas={target_sha},
        excluded_test_paths={added_test}
    )

    doc_target_commit = NormalizedDocument(
        document_id="target-commit",
        repository_id="netbox",
        type=DocumentType.COMMIT,
        commit_sha=target_sha,
        event_timestamp="2023-05-01T10:00:00Z",
        event_type=EventType.COMMIT,
        content="Target commit itself"
    )

    doc_added_test = NormalizedDocument(
        document_id="added-test",
        repository_id="netbox",
        type=DocumentType.TEST,
        path=added_test,
        event_timestamp="2023-05-01T10:00:00Z",
        event_type=EventType.TEST_CHANGE,
        content="New test added by change"
    )

    assert t_filter.is_valid_evidence(doc_target_commit) is False
    assert t_filter.is_valid_evidence(doc_added_test) is False


def test_temporal_filter_detects_post_target_edited_content():
    target_time = "2023-06-01T12:00:00Z"
    t_filter = TemporalLeakageFilter(target_time=target_time)

    # Issue created before T, but edited after T without pre-T snapshot
    doc_edited = NormalizedDocument(
        document_id="issue-edited",
        repository_id="netbox",
        type=DocumentType.ISSUE,
        event_timestamp="2023-05-15T10:00:00Z",
        event_type=EventType.ISSUE_CREATED,
        content="Issue with edited body",
        metadata={"updated_at": "2023-06-05T15:00:00Z"}
    )

    assert t_filter.is_valid_evidence(doc_edited) is False

"""
Unit tests for Repository Knowledge Graph (NetworkX) - Section 33 Enhancement #1.
"""
import os
import pytest
from app.graph.knowledge_graph import RepositoryKnowledgeGraph
from app.ingestion.sqlite_store import SQLiteMetadataStore
from app.ingestion.schema import NormalizedDocument, DocumentType, EventType, DependencyLink


@pytest.fixture
def sample_graph_store(tmp_path):
    db_path = str(tmp_path / "graph_test_meta.db")
    store = SQLiteMetadataStore(db_path)

    # 1. Documents (code, commit, issue, pr, test)
    docs = [
        NormalizedDocument(
            document_id="doc_code_1",
            repository_id="test_netbox",
            type=DocumentType.CODE,
            path="netbox/dcim/models.py",
            component="dcim",
            event_timestamp="2023-01-01T10:00:00Z",
            event_type=EventType.CODE_CHUNK,
            title="DCIM Models",
            content="class Device(models.Model): pass"
        ),
        NormalizedDocument(
            document_id="doc_test_1",
            repository_id="test_netbox",
            type=DocumentType.TEST,
            path="netbox/dcim/tests/test_devices.py",
            component="dcim",
            event_timestamp="2023-01-01T10:00:00Z",
            event_type=EventType.TEST_CHANGE,
            title="DCIM Tests",
            content="def test_device(): pass"
        ),
        NormalizedDocument(
            document_id="doc_commit_1",
            repository_id="test_netbox",
            type=DocumentType.COMMIT,
            commit_sha="a1b2c3d4e5f6",
            component="dcim",
            event_timestamp="2023-01-02T12:00:00Z",
            event_type=EventType.COMMIT,
            title="Refactor DCIM device models",
            content="Commit diff touching dcim and ipam",
            metadata={"files_changed": ["netbox/dcim/models.py", "netbox/ipam/models.py"]}
        ),
        NormalizedDocument(
            document_id="doc_issue_1",
            repository_id="test_netbox",
            type=DocumentType.ISSUE,
            issue_id="501",
            component="dcim",
            event_timestamp="2023-01-01T08:00:00Z",
            event_type=EventType.ISSUE_CREATED,
            title="Device VRF binding bug",
            content="Issue discussion regarding VRF binding",
            metadata={"linked_prs": ["102"]}
        ),
        NormalizedDocument(
            document_id="doc_pr_1",
            repository_id="test_netbox",
            type=DocumentType.PR,
            pr_id="102",
            component="dcim",
            event_timestamp="2023-01-02T11:00:00Z",
            event_type=EventType.PR_CREATED,
            title="Fix device VRF binding",
            content="PR fix for issue 501",
            metadata={"linked_issues": ["501"]}
        )
    ]
    store.store_documents(docs)

    # 2. Co-changes
    store.record_co_changes("test_netbox", "a1b2c3d4e5f6", "2023-01-02T12:00:00Z", ["dcim", "ipam"])

    # 3. Dependencies
    store.record_dependencies("test_netbox", [
        DependencyLink(
            source_component="dcim",
            target_component="ipam",
            import_statement="from netbox.ipam.models import IPAddress",
            source_file="netbox/dcim/models.py"
        )
    ])

    return store


def test_knowledge_graph_build(sample_graph_store):
    kg = RepositoryKnowledgeGraph(sample_graph_store)
    graph = kg.build_graph(repository_id="test_netbox")

    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0

    # Verify component nodes exist
    assert graph.has_node("comp:dcim")
    assert graph.has_node("file:netbox/dcim/models.py")
    assert graph.has_node("test:netbox/dcim/tests/test_devices.py")
    assert graph.has_node("issue:#501")
    assert graph.has_node("pr:#102")


def test_knowledge_graph_temporal_filtering(sample_graph_store):
    kg = RepositoryKnowledgeGraph(sample_graph_store)
    # Cut off before commit_1 (2023-01-02T12:00:00Z)
    graph = kg.build_graph(
        repository_id="test_netbox",
        max_timestamp="2023-01-02T00:00:00Z"
    )

    # Commit 1 should not exist in the filtered graph
    assert not graph.has_node("commit:a1b2c3d4")
    # Issue 1 created on Jan 1st should exist
    assert graph.has_node("issue:#501")


def test_knowledge_graph_find_impact_paths(sample_graph_store):
    kg = RepositoryKnowledgeGraph(sample_graph_store)
    kg.build_graph(repository_id="test_netbox")

    paths = kg.find_impact_paths(source_components=["dcim"], max_hops=3)
    assert isinstance(paths, list)
    assert len(paths) > 0


def test_knowledge_graph_rank_tests(sample_graph_store):
    kg = RepositoryKnowledgeGraph(sample_graph_store)
    kg.build_graph(repository_id="test_netbox")

    ranked = kg.rank_tests_by_graph_proximity(affected_components=["dcim"], top_k=2)
    assert len(ranked) >= 1
    assert ranked[0]["test_file"] == "netbox/dcim/tests/test_devices.py"
    assert ranked[0]["hops"] == 1
    assert ranked[0]["graph_score"] == 1.0


def test_knowledge_graph_ui_export(sample_graph_store):
    kg = RepositoryKnowledgeGraph(sample_graph_store)
    kg.build_graph(repository_id="test_netbox")

    data = kg.get_subgraph_data_for_ui(components=["dcim"], max_nodes=10)
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0

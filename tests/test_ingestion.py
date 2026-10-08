"""
Unit tests for Ingestion Schema, Python AST Adapter, and SQLite/Chroma stores.
"""
import os
import pytest
from app.ingestion.schema import NormalizedDocument, DocumentType, EventType
from app.ingestion.python_adapter import PythonASTAdapter
from app.ingestion.generic_fallback import GenericFallbackAdapter
from app.ingestion.sqlite_store import SQLiteMetadataStore
from app.ingestion.chroma_store import ChromaVectorStore


def test_normalized_document_schema():
    doc = NormalizedDocument(
        document_id="doc-001",
        repository_id="test_repo",
        type=DocumentType.COMMIT,
        component="dcim",
        event_timestamp="2023-01-01T12:00:00Z",
        event_type=EventType.COMMIT,
        title="Initial commit",
        content="Fix cable connections"
    )
    assert doc.document_id == "doc-001"
    assert doc.type == DocumentType.COMMIT
    assert doc.component == "dcim"


def test_python_ast_adapter():
    code = """
import os
from netbox.ipam.models import IPAddress

class DeviceManager:
    def __init__(self):
        pass

    def add_device(self, name):
        return True
"""
    adapter = PythonASTAdapter(lambda path: "dcim")
    chunks, deps = adapter.parse_file("netbox/dcim/manager.py", code, "netbox", "2023-01-01T00:00:00Z")
    
    assert len(chunks) >= 1
    assert any(c.metadata.get("symbol_name") == "DeviceManager" for c in chunks)
    assert any(d.target_component == "ipam" for d in deps)


def test_generic_fallback_adapter():
    fallback = GenericFallbackAdapter(chunk_size=10, overlap=2)
    lines = "\n".join([f"line_{i}" for i in range(25)])
    chunks = fallback.chunk_file("docs/guide.txt", lines, "test_repo", "core", "2023-01-01T00:00:00Z")
    assert len(chunks) >= 2


def test_sqlite_store_operations():
    store = SQLiteMetadataStore("data/processed/test_metadata.db")
    doc = NormalizedDocument(
        document_id="test-doc-1",
        repository_id="test_repo",
        type=DocumentType.CODE,
        component="dcim",
        event_timestamp="2023-01-01T10:00:00Z",
        event_type=EventType.CODE_CHUNK,
        title="Test Doc",
        content="Test content in SQLite"
    )
    store.store_documents([doc])
    
    # Query with temporal filter
    results = store.query_documents(
        repository_id="test_repo",
        max_timestamp="2023-01-02T00:00:00Z"
    )
    assert len(results) >= 1
    assert results[0].document_id == "test-doc-1"
    
    # Cleanup test db
    if os.path.exists("data/processed/test_metadata.db"):
        try:
            os.remove("data/processed/test_metadata.db")
        except Exception:
            pass

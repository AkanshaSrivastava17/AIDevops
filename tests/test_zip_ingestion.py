"""
Unit tests for Local/ZIP Repository Ingestion (Section 33, Enhancement #10).
"""
import os
import shutil
import tempfile
import zipfile
import pytest

from app.repository.adapter import ingest_zip_archive, RepositoryAdapter
from app.ingestion.core import IngestionPipeline
from app.ingestion.sqlite_store import SQLiteMetadataStore
from app.ingestion.chroma_store import ChromaVectorStore


def test_zip_repository_ingestion():
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "sample_service.zip")
    repo_id = "test_zip_service"

    try:
        # Create a sample repository ZIP
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr(
                "sample_service/core.py",
                "def calculate_total(items):\n    return sum(items)\n"
            )
            z.writestr(
                "sample_service/tests/test_core.py",
                "from sample_service.core import calculate_total\n\ndef test_calc():\n    assert calculate_total([1, 2, 3]) == 6\n"
            )

        # Ingest ZIP archive
        config, target_dir = ingest_zip_archive(zip_path, repository_id=repo_id)
        assert config.repository_id == repo_id
        assert os.path.exists(target_dir)
        assert os.path.exists(os.path.join("configs", f"{repo_id}.yaml"))

        # Verify Capability Profiler adheres to Section 33 #10:
        # "Source and local Git history only; GitHub issues/PRs need hosted metadata"
        adapter = RepositoryAdapter(config)
        profile = adapter.get_profile()
        assert profile.source_code is True
        assert profile.tests is True
        assert profile.issues is False
        assert profile.prs is False

        # Verify ingestion pipeline executes cleanly
        sqlite_store = SQLiteMetadataStore()
        chroma_store = ChromaVectorStore()
        pipeline = IngestionPipeline(config, sqlite_store, chroma_store)
        res = pipeline.run()

        assert res["status"] == "success"
        assert res["total_documents_indexed"] >= 1

    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)
        raw_target = os.path.join("data", "raw", repo_id)
        shutil.rmtree(raw_target, ignore_errors=True)
        cfg_file = os.path.join("configs", f"{repo_id}.yaml")
        if os.path.exists(cfg_file):
            os.remove(cfg_file)

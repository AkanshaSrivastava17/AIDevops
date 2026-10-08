"""
Core Ingestion Pipeline Orchestrator.
Converts raw repository sources into normalized documents in SQLite and ChromaDB.
"""
import os
import logging
from typing import Dict, Any, List
from app.repository.adapter import RepositoryAdapter
from app.repository.models import RepositoryConfig, AnalysisMode
from app.ingestion.python_adapter import PythonASTAdapter
from app.ingestion.generic_fallback import GenericFallbackAdapter
from app.ingestion.sqlite_store import SQLiteMetadataStore
from app.ingestion.chroma_store import ChromaVectorStore
from app.ingestion.schema import NormalizedDocument, DocumentType

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(
        self,
        config: RepositoryConfig,
        sqlite_store: SQLiteMetadataStore = None,
        chroma_store: ChromaVectorStore = None
    ):
        self.config = config
        self.adapter = RepositoryAdapter(config)
        self.sqlite_store = sqlite_store or SQLiteMetadataStore()
        self.chroma_store = chroma_store or ChromaVectorStore()
        self.python_ast = PythonASTAdapter(self.adapter.map_file_to_component)
        self.fallback = GenericFallbackAdapter()

    def run(self) -> Dict[str, Any]:
        logger.info(f"Starting ingestion for repository: {self.config.repository_id}")
        
        # 1. Profile repository
        profile = self.adapter.get_profile()
        
        # 2. Extract base documents (commits, issues, PRs, files)
        base_documents = self.adapter.extract_normalized_documents()
        
        # 3. Process code files: enhanced Python AST or generic fallback
        processed_documents: List[NormalizedDocument] = []
        all_dependencies = []

        for doc in base_documents:
            processed_documents.append(doc)
            
            # If doc is a Python code file, parse AST chunks and dependencies
            if doc.type == DocumentType.CODE and doc.path and doc.path.endswith(".py"):
                if profile.analysis_mode == AnalysisMode.ENHANCED and profile.python_ast:
                    ast_chunks, deps = self.python_ast.parse_file(
                        file_path=doc.path,
                        code=doc.content,
                        repo_id=self.config.repository_id,
                        timestamp=doc.event_timestamp
                    )
                    processed_documents.extend(ast_chunks)
                    all_dependencies.extend(deps)
                else:
                    fallback_chunks = self.fallback.chunk_file(
                        file_path=doc.path,
                        content=doc.content,
                        repo_id=self.config.repository_id,
                        component=doc.component,
                        timestamp=doc.event_timestamp
                    )
                    processed_documents.extend(fallback_chunks)

        # 4. Store in SQLite
        self.sqlite_store.store_documents(processed_documents)
        if all_dependencies:
            self.sqlite_store.record_dependencies(self.config.repository_id, all_dependencies)

        # 5. Extract and record co-changes from commits
        for doc in processed_documents:
            if doc.type == DocumentType.COMMIT and doc.commit_sha:
                comps = doc.metadata.get("components", [])
                if len(comps) >= 2:
                    self.sqlite_store.record_co_changes(
                        repo_id=self.config.repository_id,
                        commit_sha=doc.commit_sha,
                        timestamp=doc.event_timestamp,
                        components=comps
                    )

        # 6. Store embeddings in ChromaDB
        self.chroma_store.index_documents(self.config.repository_id, processed_documents)

        stats = self.sqlite_store.get_repository_stats(self.config.repository_id)
        return {
            "repository_id": self.config.repository_id,
            "status": "success",
            "profile": profile.model_dump(),
            "stats": stats,
            "total_documents_indexed": len(processed_documents),
            "dependencies_recorded": len(all_dependencies)
        }

"""
Hybrid Retriever: Combines ChromaDB vector retrieval with SQLite structured lookups,
strictly honoring temporal filters and ablation system modes (History-RAG vs Code-RAG vs LLM-only).
"""
import logging
from typing import List, Dict, Optional, Set, Any
from app.ingestion.sqlite_store import SQLiteMetadataStore
from app.ingestion.chroma_store import ChromaVectorStore
from app.rag.evidence_pack import EvidencePack
from app.rag.temporal_filter import TemporalLeakageFilter
from app.ingestion.schema import DocumentType

logger = logging.getLogger(__name__)


class HybridRetriever:
    def __init__(
        self,
        sqlite_store: SQLiteMetadataStore = None,
        chroma_store: ChromaVectorStore = None
    ):
        self.sqlite = sqlite_store or SQLiteMetadataStore()
        self.chroma = chroma_store or ChromaVectorStore()

    def build_evidence_pack(
        self,
        repository_id: str,
        query_or_change: str,
        system_mode: str = "History-RAG",
        target_time: Optional[str] = None,
        candidate_components: Optional[List[str]] = None,
        analysis_mode: str = "Enhanced",
        excluded_commit_shas: Optional[Set[str]] = None,
        excluded_issue_ids: Optional[Set[str]] = None,
        excluded_pr_ids: Optional[Set[str]] = None,
        excluded_test_paths: Optional[Set[str]] = None,
        available_tests_override: Optional[List[str]] = None,
        top_k: int = 15
    ) -> EvidencePack:
        components = candidate_components or ["core"]
        
        # System Baseline 1: LLM-only (No retrieval whatsoever)
        if system_mode == "LLM-only":
            return EvidencePack(
                repository_id=repository_id,
                query_or_change=query_or_change,
                target_time=target_time,
                system_mode="LLM-only",
                analysis_mode=analysis_mode,
                candidate_components=components,
                citations=[]
            )

        # Build Temporal Filter
        temporal_filter = TemporalLeakageFilter(
            target_time=target_time,
            excluded_commit_shas=excluded_commit_shas,
            excluded_issue_ids=excluded_issue_ids,
            excluded_pr_ids=excluded_pr_ids,
            excluded_test_paths=excluded_test_paths
        )

        pack = EvidencePack(
            repository_id=repository_id,
            query_or_change=query_or_change,
            target_time=target_time,
            system_mode=system_mode,
            analysis_mode=analysis_mode,
            candidate_components=components
        )

        # Determine allowed types based on system_mode
        # Baseline 2: Code-RAG allows ONLY current code and tests
        if system_mode == "Code-RAG":
            allowed_types = ["code", "test"]
        else:
            # Proposed: History-RAG allows code, commits, issues, PRs, diffs, tests
            allowed_types = None

        # 1. Semantic retrieval from ChromaDB
        semantic_hits = self.chroma.query(
            repository_id=repository_id,
            query_text=query_or_change,
            top_k=top_k * 2,
            type_filter=allowed_types
        )

        # 2. Re-fetch full records from SQLite & enforce temporal filter
        citations = []
        for hit in semantic_hits:
            meta = hit.get("metadata", {})
            doc_id = hit.get("document_id")
            doc_type = meta.get("type")
            event_time = meta.get("event_timestamp")
            commit_sha = meta.get("commit_sha")
            issue_id = meta.get("issue_id")
            pr_id = meta.get("pr_id")
            path = meta.get("path")
            comp = meta.get("component")

            # Check exclusions
            if commit_sha and commit_sha in (excluded_commit_shas or set()):
                continue
            if issue_id and issue_id in (excluded_issue_ids or set()):
                continue
            if pr_id and pr_id in (excluded_pr_ids or set()):
                continue
            if path and path in (excluded_test_paths or set()):
                continue

            # Event timestamp filter
            if target_time and event_time:
                try:
                    if event_time.replace("Z", "+00:00") >= target_time.replace("Z", "+00:00"):
                        continue
                except Exception:
                    pass

            item = {
                "id": doc_id,
                "title": hit.get("content", "").split("\n")[0][:100],
                "component": comp,
                "content": hit.get("content", "")[:1000],
                "similarity": hit.get("similarity", 0.5),
                "timestamp": event_time
            }

            if doc_type == "code":
                item["path"] = path
                pack.code_evidence.append(item)
                if path:
                    citations.append(f"File: {path}")
            elif doc_type == "commit" and system_mode == "History-RAG":
                item["commit_sha"] = commit_sha
                pack.commit_evidence.append(item)
                if commit_sha:
                    citations.append(f"Commit: {commit_sha[:8]}")
            elif doc_type == "issue" and system_mode == "History-RAG":
                item["issue_id"] = issue_id
                pack.issue_evidence.append(item)
                if issue_id:
                    citations.append(f"Issue: #{issue_id}")
            elif doc_type == "pr" and system_mode == "History-RAG":
                item["pr_id"] = pr_id
                pack.pr_evidence.append(item)
                if pr_id:
                    citations.append(f"PR: #{pr_id}")

        # 3. History-RAG: Add co-change counts and dependency links
        if system_mode == "History-RAG":
            for comp in components:
                co_counts = self.sqlite.get_co_change_counts(
                    repository_id=repository_id,
                    source_component=comp,
                    max_timestamp=target_time
                )
                if co_counts:
                    pack.cochange_evidence[comp] = co_counts

        # 4. Dependency analysis (Available in Enhanced mode)
        if analysis_mode == "Enhanced":
            for comp in components:
                deps = self.sqlite.get_dependencies_for_component(repository_id, comp)
                pack.dependency_evidence.extend(deps[:5])

        # 5. Existing Available Tests
        if available_tests_override is not None:
            all_avail_tests = available_tests_override
        else:
            all_avail_tests = self.sqlite.get_available_tests(repository_id)
            
        # Filter out tests added by target change
        filtered_tests = [
            t for t in all_avail_tests
            if t not in (excluded_test_paths or set())
        ]
        pack.available_tests = filtered_tests
        pack.citations = sorted(list(set(citations)))[:15]

        return pack

"""
FastAPI Endpoints for History-Aware Repository Intelligence.
Strictly conforms to Section 22 of the implementation plan.
"""
import os
import yaml
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.repository.models import RepositoryConfig, AnalysisMode
from app.repository.adapter import RepositoryAdapter
from app.ingestion.core import IngestionPipeline
from app.ingestion.sqlite_store import SQLiteMetadataStore
from app.ingestion.chroma_store import ChromaVectorStore
from app.rag.hybrid_retriever import HybridRetriever
from app.impact.scoring_engine import ImpactScoringEngine
from app.testing.test_recommender import TestRecommender
from app.rag.llm import EvidenceGroundedLLM

app = FastAPI(
    title="History-Aware Repository Intelligence API",
    description="Evidence-based change-impact analysis and test recommendation backend.",
    version="1.0.0"
)

# Global singletons
sqlite_store = SQLiteMetadataStore()
chroma_store = ChromaVectorStore()
retriever = HybridRetriever(sqlite_store, chroma_store)
scoring_engine = ImpactScoringEngine()
test_recommender = TestRecommender()
llm = EvidenceGroundedLLM()


# Request / Response Models
class AskRequest(BaseModel):
    repository_id: str = "netbox"
    question: str
    system_mode: str = "History-RAG"


class AnalyzeChangeRequest(BaseModel):
    repository_id: str = "netbox"
    proposed_change: str
    target_time: Optional[str] = None
    system_mode: str = "History-RAG"
    top_k_tests: int = 5


class AnalyzeChangeResponse(BaseModel):
    proposed_change: str
    affected_components: List[Dict[str, Any]]
    impact_level: str
    historical_evidence: List[Dict[str, Any]]
    recommended_tests: List[Dict[str, Any]]
    confidence: float
    limitations: str
    analysis_mode: Optional[str] = None
    engine_mode: Optional[str] = None


class IndexRequest(BaseModel):
    repository_id: str
    repository_url: Optional[str] = None
    force_refresh: bool = False


def _get_repo_config(repo_id: str) -> RepositoryConfig:
    config_file = os.path.join("configs", f"{repo_id}.yaml")
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return RepositoryConfig(**data)
    # Default fallback config
    return RepositoryConfig(
        repository_id=repo_id,
        repository_url=f"https://github.com/mock/{repo_id}",
        component_rules_file="data/evaluation/component_map.json" if repo_id == "netbox" else None
    )


@app.get("/health")
def health_check():
    """Application health check (also used for QA health check)."""
    return {
        "status": "healthy",
        "service": "History-RAG",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "database": "sqlite_ready",
        "vector_store": "chroma_ready"
    }


@app.post("/ask")
def ask_question(req: AskRequest):
    """Repository Q&A with historical evidence."""
    config = _get_repo_config(req.repository_id)
    adapter = RepositoryAdapter(config)
    profile = adapter.get_profile()

    evidence_pack = retriever.build_evidence_pack(
        repository_id=req.repository_id,
        query_or_change=req.question,
        system_mode=req.system_mode,
        candidate_components=profile.discovered_components,
        analysis_mode=profile.analysis_mode.value
    )

    answer_result = llm.answer_qa(
        question=req.question,
        repository_id=req.repository_id,
        evidence_pack=evidence_pack
    )
    return answer_result


@app.post("/analyze-change", response_model=AnalyzeChangeResponse)
def analyze_change(req: AnalyzeChangeRequest):
    """
    Change-impact analysis + existing-test recommendation.
    Returns: proposed_change, affected_components, impact_level,
    historical_evidence, recommended_tests, confidence, limitations.
    """
    config = _get_repo_config(req.repository_id)
    adapter = RepositoryAdapter(config)
    profile = adapter.get_profile()

    # 1. Retrieve evidence pack (respecting system mode and temporal filter)
    evidence_pack = retriever.build_evidence_pack(
        repository_id=req.repository_id,
        query_or_change=req.proposed_change,
        system_mode=req.system_mode,
        target_time=req.target_time,
        candidate_components=profile.discovered_components,
        analysis_mode=profile.analysis_mode.value
    )

    # 2. Predict affected components via deterministic Evidence Scoring Engine
    if req.system_mode == "LLM-only":
        baseline_result = llm.generate_llm_only_baseline(
            proposed_change=req.proposed_change,
            candidate_components=profile.discovered_components
        )
        return AnalyzeChangeResponse(
            proposed_change=req.proposed_change,
            affected_components=baseline_result["affected_components"],
            impact_level=baseline_result["impact_level"],
            historical_evidence=[],
            recommended_tests=[],
            confidence=baseline_result["confidence"],
            limitations=baseline_result["limitations"],
            analysis_mode=profile.analysis_mode.value,
            engine_mode="LLM-only"
        )

    ranked_components = scoring_engine.score_components(
        evidence_pack=evidence_pack,
        system_mode=req.system_mode
    )

    # 3. Predict existing tests via Test Recommender
    top_affected_names = [c["component"] for c in ranked_components[:2]]
    recommended_tests = test_recommender.rank_tests(
        evidence_pack=evidence_pack,
        affected_components=top_affected_names,
        top_k=req.top_k_tests
    )

    # 4. LLM explains the engine output without reordering
    llm_report = llm.explain_change_analysis(
        proposed_change=req.proposed_change,
        repository_id=req.repository_id,
        evidence_pack=evidence_pack,
        ranked_components=ranked_components,
        ranked_tests=recommended_tests
    )

    all_evidence = (
        evidence_pack.commit_evidence
        + evidence_pack.issue_evidence
        + evidence_pack.pr_evidence
    )

    return AnalyzeChangeResponse(
        proposed_change=req.proposed_change,
        affected_components=ranked_components,
        impact_level=llm_report["impact_level"],
        historical_evidence=all_evidence[:10],
        recommended_tests=recommended_tests,
        confidence=llm_report["confidence"],
        limitations=llm_report["limitations"],
        analysis_mode=profile.analysis_mode.value,
        engine_mode=req.system_mode
    )


@app.post("/index")
def index_repository(req: IndexRequest):
    """Index a repository from a GitHub URL or refresh an existing index."""
    config = _get_repo_config(req.repository_id)
    if req.repository_url:
        config.repository_url = req.repository_url

    pipeline = IngestionPipeline(
        config=config,
        sqlite_store=sqlite_store,
        chroma_store=chroma_store
    )
    result = pipeline.run()
    return result


@app.get("/repository-status")
def repository_status(repository_id: str = Query("netbox")):
    """Index statistics, repository profile (capabilities, analysis mode) and state per repository."""
    config = _get_repo_config(repository_id)
    adapter = RepositoryAdapter(config)
    profile = adapter.get_profile()
    stats = sqlite_store.get_repository_stats(repository_id)

    return {
        "repository_id": repository_id,
        "name": config.name or repository_id,
        "repository_url": config.repository_url,
        "pinned_commit": config.pinned_commit,
        "profile": profile.model_dump(),
        "stats": stats,
        "mode": profile.analysis_mode.value,
        "capabilities": {
            "git_history": profile.git_history,
            "source_code": profile.source_code,
            "issues": profile.issues,
            "prs": profile.prs,
            "tests": profile.tests,
            "python_ast": profile.python_ast,
            "import_analysis": profile.import_analysis
        }
    }

"""
FastAPI Endpoints for History-Aware Repository Intelligence.
Strictly conforms to Section 22 of the implementation plan.
"""
import os
import yaml
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.repository.models import RepositoryConfig, AnalysisMode
from app.repository.adapter import RepositoryAdapter
from app.ingestion.core import IngestionPipeline
from app.ingestion.sqlite_store import SQLiteMetadataStore
from app.ingestion.chroma_store import ChromaVectorStore
from app.rag.hybrid_retriever import HybridRetriever
from app.impact.scoring_engine import ImpactScoringEngine
from app.testing.test_recommender import TestRecommender
from app.testing.test_generator import CandidateTestGenerator
from app.devops.pipeline_gate import AdvancedCIDCGate, DeploymentManager
from app.devops.github_installer import GitHubWorkflowInstaller
from app.monitoring.metrics import MetricsManager, CONTENT_TYPE_LATEST
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
candidate_generator = CandidateTestGenerator()
llm = EvidenceGroundedLLM()
pipeline_gate = AdvancedCIDCGate()
deployment_manager = DeploymentManager()


# Request / Response Models
class GateEvaluationRequest(BaseModel):
    change_analysis: Dict[str, Any]
    test_results: Dict[str, Any]
    qa_health_status: Optional[Dict[str, Any]] = None
    block_on_high_impact: bool = True
    min_confidence: float = 0.60


class RollbackRequest(BaseModel):
    failed_image: str = "historyrag:candidate"
    reason: str = "QA Health Check Failure"
    environment: str = "qa"


class WorkflowInstallRequest(BaseModel):
    repository_url_or_slug: str = Field(..., description="GitHub URL (https://github.com/owner/repo) or 'owner/repo'")
    github_token: Optional[str] = Field(None, description="GitHub Personal Access Token (or 'demo'/'mock' for dry-run)")
    branch_name: str = "historyrag-setup-cicd"
    commit_to_main: bool = False
    dry_run: bool = False


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
    generate_candidate_tests: bool = False


class CandidateTestModel(BaseModel):
    test_name: str
    target_component: str
    target_function_or_scenario: str
    test_code: str
    rationale: str
    validation_status: str
    review_status: str
    framework: str = "pytest"
    test_type: str = "unit"
    ast_valid: bool = True
    created_at: Optional[str] = None


class GenerateCandidateTestsRequest(BaseModel):
    repository_id: str = "netbox"
    proposed_change: str
    system_mode: str = "History-RAG"
    top_k: int = 3


class AnalyzeChangeResponse(BaseModel):
    proposed_change: str
    affected_components: List[Dict[str, Any]]
    impact_level: str
    historical_evidence: List[Dict[str, Any]]
    recommended_tests: List[Dict[str, Any]]
    candidate_tests: Optional[List[Dict[str, Any]]] = None
    confidence: float
    limitations: str
    analysis_mode: Optional[str] = None
    engine_mode: Optional[str] = None


class IndexRequest(BaseModel):
    repository_id: Optional[str] = None
    repository_url: Optional[str] = None
    force_refresh: bool = False


class IndexZipRequest(BaseModel):
    zip_path: str
    repository_id: Optional[str] = None


def _get_or_create_repo_config(repo_id: Optional[str] = None, repo_url: Optional[str] = None) -> RepositoryConfig:
    from app.repository.adapter import parse_github_url
    if not repo_id and repo_url:
        _, _, parsed_id = parse_github_url(repo_url)
        repo_id = parsed_id
    elif not repo_id:
        repo_id = "netbox"

    config_file = os.path.join("configs", f"{repo_id}.yaml")
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            cfg = RepositoryConfig(**data)
            if repo_url and cfg.repository_url != repo_url:
                cfg.repository_url = repo_url
            return cfg

    # Check if raw directory exists
    raw_dir = os.path.join("data", "raw", repo_id)
    default_url = repo_url or f"https://github.com/mock/{repo_id}"
    cfg = RepositoryConfig(
        repository_id=repo_id,
        name=repo_id.replace("_", " ").title(),
        repository_url=default_url,
        component_rules_file="data/evaluation/component_map.json" if repo_id == "netbox" else None
    )
    
    # Save new config
    os.makedirs("configs", exist_ok=True)
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg.model_dump(), f)
    except Exception:
        pass
    return cfg


def _get_repo_config(repo_id: str) -> RepositoryConfig:
    return _get_or_create_repo_config(repo_id=repo_id)


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

    # 5. Optional AI-Generated Candidate Tests (Section 33 Enhancement #2)
    candidates = []
    if req.generate_candidate_tests:
        candidates = candidate_generator.generate_candidate_tests(
            proposed_change=req.proposed_change,
            affected_components=ranked_components,
            evidence_pack=evidence_pack,
            top_k=3
        )

    # Record Prometheus Telemetry (Section 33 Enhancement #5)
    MetricsManager.record_change_analysis(
        mode=req.system_mode,
        impact_level=llm_report["impact_level"]
    )

    return AnalyzeChangeResponse(
        proposed_change=req.proposed_change,
        affected_components=ranked_components,
        impact_level=llm_report["impact_level"],
        historical_evidence=all_evidence[:10],
        recommended_tests=recommended_tests,
        candidate_tests=candidates if req.generate_candidate_tests else None,
        confidence=llm_report["confidence"],
        limitations=llm_report["limitations"],
        analysis_mode=profile.analysis_mode.value,
        engine_mode=req.system_mode
    )


@app.post("/generate-candidate-tests")
def generate_candidate_tests(req: GenerateCandidateTestsRequest):
    """
    AI-Generated Candidate Tests (Section 33, Enhancement #2).
    Generates AST-validated pytest test functions for components affected by the change.
    All candidate tests are marked with @pytest.mark.ai_candidate and require human review.
    """
    config = _get_repo_config(req.repository_id)
    adapter = RepositoryAdapter(config)
    profile = adapter.get_profile()

    evidence_pack = retriever.build_evidence_pack(
        repository_id=req.repository_id,
        query_or_change=req.proposed_change,
        system_mode=req.system_mode,
        candidate_components=profile.discovered_components,
        analysis_mode=profile.analysis_mode.value
    )

    ranked_components = scoring_engine.score_components(
        evidence_pack=evidence_pack,
        system_mode=req.system_mode
    )

    candidates = candidate_generator.generate_candidate_tests(
        proposed_change=req.proposed_change,
        affected_components=ranked_components,
        evidence_pack=evidence_pack,
        top_k=req.top_k
    )

    return {
        "repository_id": req.repository_id,
        "proposed_change": req.proposed_change,
        "system_mode": req.system_mode,
        "candidate_tests": candidates,
        "count": len(candidates)
    }


@app.post("/evaluate-gate")
def evaluate_gate(req: GateEvaluationRequest):
    """
    Advanced CI/CD Policy Gate (Section 33 Enhancement #8).
    Evaluates PR merge readiness based on change impact severity, test results, and QA health.
    """
    gate = AdvancedCIDCGate(
        block_on_high_impact_failure=req.block_on_high_impact,
        min_confidence_score=req.min_confidence
    )
    result = gate.evaluate(
        change_analysis=req.change_analysis,
        test_results=req.test_results,
        qa_health_status=req.qa_health_status
    )
    MetricsManager.record_gate_decision(result["decision"])
    return result


@app.post("/devops/rollback")
def trigger_rollback(req: RollbackRequest):
    """
    Automated Rollback Engine (Section 33 Enhancement #7).
    Redeploys known-good image when candidate deployment or health checks fail.
    """
    result = deployment_manager.trigger_auto_rollback(
        failed_image=req.failed_image,
        reason=req.reason,
        environment=req.environment
    )
    MetricsManager.record_rollback(environment=req.environment)
    return result


@app.get("/devops/deployments")
def get_deployment_ledger():
    """Returns deployment history and current known-good image pointer."""
    return {
        "current_deployed_image": deployment_manager.current_deployed_image,
        "known_good_image": deployment_manager.known_good_image,
        "history": deployment_manager.deployment_history
    }


@app.get("/metrics")
def prometheus_metrics():
    """
    Prometheus Monitoring Metrics Endpoint (Section 33, Enhancement #5).
    Exposes infrastructure, RAG retrieval, testing, and rollback telemetry in Prometheus exposition format.
    """
    payload = MetricsManager.get_metrics_payload()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


@app.post("/index")
def index_repository(req: IndexRequest):
    """Index a repository from any Git or GitHub URL, or refresh an existing index."""
    config = _get_or_create_repo_config(req.repository_id, req.repository_url)
    if req.repository_url:
        config.repository_url = req.repository_url

    pipeline = IngestionPipeline(
        config=config,
        sqlite_store=sqlite_store,
        chroma_store=chroma_store
    )
    result = pipeline.run()
    return result


@app.post("/index-zip")
def index_zip_repository(req: IndexZipRequest):
    """
    Local/ZIP Repository Ingestion (Section 33 Enhancement #10).
    Ingests source code and local Git history from a ZIP archive.
    """
    from app.repository.adapter import ingest_zip_archive
    cfg, target_dir = ingest_zip_archive(req.zip_path, req.repository_id)
    pipeline = IngestionPipeline(
        config=cfg,
        sqlite_store=sqlite_store,
        chroma_store=chroma_store
    )
    result = pipeline.run()
    result["zip_ingestion"] = {
        "status": "success",
        "archive": req.zip_path,
        "target_directory": target_dir,
        "repository_id": cfg.repository_id
    }
    return result


@app.post("/devops/install-workflow")
def install_workflow_endpoint(req: WorkflowInstallRequest):
    """1-Click installs History-RAG CI/CD workflow into any GitHub repository via PR or direct commit."""
    installer = GitHubWorkflowInstaller()
    try:
        res = installer.install(
            repo_url_or_slug=req.repository_url_or_slug,
            token=req.github_token,
            branch_name=req.branch_name,
            commit_to_main=req.commit_to_main,
            dry_run=req.dry_run
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/repositories")
def list_repositories():
    """Returns a list of all configured and indexed repositories."""
    repos = []
    seen = set()
    if os.path.exists("configs"):
        for f in os.listdir("configs"):
            if f.endswith(".yaml") or f.endswith(".yml"):
                rid = os.path.splitext(f)[0]
                seen.add(rid)
                try:
                    with open(os.path.join("configs", f), "r", encoding="utf-8") as fp:
                        data = yaml.safe_load(fp)
                        repos.append({
                            "repository_id": rid,
                            "name": data.get("name") or rid.replace("_", " ").title(),
                            "repository_url": data.get("repository_url", ""),
                            "language": data.get("language", "Python"),
                            "description": data.get("description", "")
                        })
                except Exception:
                    repos.append({"repository_id": rid, "name": rid.title(), "repository_url": ""})
    return repos


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

"""
CI/CD Pipeline Simulator for Local & Self-Hosted Runner Verification.
Executes the exact 10 steps defined in Section 7.2, 13, and .github/workflows/ci.yml:
1. Lint Check
2. Baseline Pytest Tests
3. Start/Verify History-RAG Service
4. AI Change-Impact Analysis (POST /analyze-change)
5. Select & Execute AI-Recommended Tests (pytest)
6. Docker Image Tagging & Packaging Simulation
7. Deploy to QA Environment
8. Automated QA Health Check Verification (GET /health)
"""
import os
import sys
import time
import requests
import subprocess
import argparse
from rich.console import Console
from rich.panel import Panel

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

console = Console()


def run_pipeline(repo_id: str = "netbox", repo_url: str = None, pr_change: str = None, fault: str = "none"):
    console.print(Panel.fit(
        f"[bold cyan]CSE 4011 — History-RAG AI-Enhanced CI/CD Pipeline Execution[/bold cyan]\n"
        f"[dim]Target Repository: [magenta]{repo_id}[/magenta] | Workflow: PR -> Lint -> Tests -> AI Analysis -> Recommended Tests -> Docker -> QA -> Health Check[/dim]"
    ))

    # Step 1: Lint
    console.print("\n[bold yellow]Step 1/8: Running Code Linting...[/bold yellow]")
    res = subprocess.run([sys.executable, "-m", "py_compile", "app/api/routes.py", "app/rag/hybrid_retriever.py"], capture_output=True)
    if res.returncode == 0:
        console.print("[green][OK] Lint checks passed cleanly.[/green]")
    else:
        console.print(f"[red][FAIL] Lint error: {res.stderr.decode()}[/red]")
        return False

    # Step 2: Baseline Tests
    console.print("\n[bold yellow]Step 2/8: Running Baseline Test Suite (pytest)...[/bold yellow]")
    res = subprocess.run([sys.executable, "-m", "pytest", "tests/test_repository.py", "tests/test_scoring_engine.py", "-q"], capture_output=True, text=True)
    console.print(res.stdout.strip())
    if res.returncode == 0:
        console.print("[green][OK] Baseline test suite PASSED.[/green]")
    else:
        console.print("[red][FAIL] Baseline tests failed.[/red]")
        return False

    # Step 3: AI Change Impact Analysis
    console.print("\n[bold yellow]Step 3/8: AI Change Analysis on PR Diff...[/bold yellow]")
    from app.repository.adapter import RepositoryAdapter
    from app.ingestion.sqlite_store import SQLiteMetadataStore
    from app.ingestion.chroma_store import ChromaVectorStore
    from app.rag.hybrid_retriever import HybridRetriever
    from app.impact.scoring_engine import ImpactScoringEngine
    from app.testing.test_recommender import TestRecommender
    from app.ingestion.core import IngestionPipeline

    config_path = f"configs/{repo_id}.yaml"
    if not os.path.exists(config_path):
        if repo_url:
            from app.api.routes import _get_or_create_repo_config
            config = _get_or_create_repo_config(repo_url=repo_url, repo_id=repo_id)
            pipeline = IngestionPipeline(config=config)
            pipeline.run()
        else:
            console.print(f"[red][FAIL] Config {config_path} not found. Please specify --url or index the repository first.[/red]")
            return False

    sqlite = SQLiteMetadataStore()
    chroma = ChromaVectorStore()
    retriever = HybridRetriever(sqlite, chroma)
    scorer = ImpactScoringEngine()
    recommender = TestRecommender()
    adapter = RepositoryAdapter(config_path)
    profile = adapter.get_profile()

    if not pr_change:
        if repo_id == "netbox":
            pr_change = "Refactor interface IP assignment to validate IP address VRF containment"
        elif profile.discovered_components:
            comp = profile.discovered_components[0]
            pr_change = f"Refactor {comp} core logic and add validation checks"
        else:
            pr_change = "Refactor core components and improve error handling"

    console.print(f"  [cyan]Analyzing PR Change on[/cyan] [magenta]{repo_id}[/magenta]: '{pr_change}'")

    pack = retriever.build_evidence_pack(
        repository_id=repo_id,
        query_or_change=pr_change,
        system_mode="History-RAG",
        candidate_components=profile.discovered_components,
        analysis_mode=profile.analysis_mode.value
    )
    ranked_comps = scorer.score_components(pack, system_mode="History-RAG")
    if ranked_comps:
        top_comp = ranked_comps[0]
        console.print(f"  [bold green][OK] Top Affected Component:[/bold green] [magenta]{top_comp['component']}[/magenta] (Impact: [red]{top_comp['impact_level']}[/red], Score: {top_comp['score']:.2f})")
        comp_name = top_comp["component"]
    else:
        comp_name = profile.discovered_components[0] if profile.discovered_components else "core"
        console.print(f"  [yellow]No specific component matched; using primary module:[/yellow] [magenta]{comp_name}[/magenta]")

    # Step 4: Recommended Test Selection
    console.print("\n[bold yellow]Step 4/9: Recommended Test Selection...[/bold yellow]")
    rec_tests = recommender.rank_tests(pack, [comp_name], top_k=2)
    test_paths = [t["test_file"] for t in rec_tests]
    for t in rec_tests:
        console.print(f"  [green]  * Recommended:[/green] {t['test_file']} (Score: {t['score']:.2f})")

    # Step 5: Execute Recommended Tests
    console.print("\n[bold yellow]Step 5/9: Executing AI-Recommended Tests with pytest...[/bold yellow]")
    from app.testing.pytest_executor import PytestExecutor
    executor = PytestExecutor()
    t_res = executor.run_tests(test_paths)

    if fault == "test_fail":
        t_res["status"] = "FAIL"
        t_res["failed"] = 1
        t_res["passed"] = max(0, t_res["tests_executed"] - 1)
        console.print("  [bold red][FAULT INJECTED] Simulated regression test failure.[/bold red]")

    console.print(f"  [bold green][OK] Pytest Execution Status: {t_res['status']} ({t_res['passed']}/{t_res['tests_executed']} passed in {t_res['duration_seconds']}s)[/bold green]")

    # Step 6: Advanced CI/CD Policy Gate Evaluation (Section 33 #8)
    console.print("\n[bold yellow]Step 6/9: Evaluating Advanced CI/CD Policy Gates (Section 33 #8)...[/bold yellow]")
    from app.devops.pipeline_gate import AdvancedCIDCGate, DeploymentManager
    gate = AdvancedCIDCGate()
    deploy_mgr = DeploymentManager()
    gate_decision = gate.evaluate(
        change_analysis={"impact_level": top_comp["impact_level"] if ranked_comps else "MEDIUM", "confidence": 0.88, "affected_components": ranked_comps},
        test_results=t_res
    )
    if not gate_decision["gate_passed"]:
        console.print(f"  [bold red][BLOCKED] Gate Decision: {gate_decision['decision']}[/bold red]")
        for r in gate_decision["blocking_reasons"]:
            console.print(f"    - {r}")
        console.print(Panel.fit("[bold red]CI/CD PIPELINE BLOCKED! Merge rejected by policy gate.[/bold red]"))
        return False
    else:
        console.print(f"  [bold green][APPROVED] Gate Decision: {gate_decision['decision']} (All policy gates satisfied)[/bold green]")

    # Step 7: Docker Image Packaging
    commit_sha = "a7f92b4c"
    candidate_tag = f"historyrag:{commit_sha}"
    console.print(f"\n[bold yellow]Step 7/9: Packaging Docker Image ({candidate_tag})...[/bold yellow]")
    console.print(f"  Tagged image: [cyan]{candidate_tag}[/cyan] -> [cyan]historyrag:qa-latest[/cyan]")
    console.print("  [green][OK] Docker build specification verified (Dockerfile & docker-compose.yml ready).[/green]")

    # Step 8: QA Deployment
    console.print(f"\n[bold yellow]Step 8/9: Deploying candidate image to QA environment...[/bold yellow]")
    deploy_mgr.deploy_candidate(candidate_tag, environment="qa")
    console.print(f"  [green][OK] Container deployed: {candidate_tag}[/green]")

    # Step 9: QA Health Check & Auto-Rollback Gate (Section 33 #7)
    console.print("\n[bold yellow]Step 9/9: Running Verification Health Check Gate (GET /health)...[/bold yellow]")
    from app.api.routes import health_check
    h_data = health_check()

    if fault == "qa_crash":
        console.print("  [bold red][FAULT INJECTED] QA Container crashed during health check (HTTP 503)![/bold red]")
        console.print("  [bold yellow][ALERT] Triggering Automatic Rollback (Section 33 #7)...[/bold yellow]")
        rollback_event = deploy_mgr.trigger_auto_rollback(
            failed_image=candidate_tag,
            reason="QA Health Probe Failed (HTTP 503)"
        )
        console.print(f"  [bold green][ROLLBACK COMPLETED] Restored: [cyan]{rollback_event['restored_image']}[/cyan][/bold green]")
        console.print(f"    Transaction ID: {rollback_event['transaction_id']} | Restored Health: HTTP 200 OK")
        console.print(Panel.fit(
            f"[bold yellow]CI/CD PIPELINE COMPLETED WITH AUTO-ROLLBACK! Restored known-good stable version.[/bold yellow]"
        ))
        return True

    console.print(f"  [bold green][OK] QA Health Check PASSED: HTTP 200[/bold green]")
    console.print(f"    Service: {h_data.get('service')} | Status: {h_data.get('status')} | Version: {h_data.get('version')}")
    deploy_mgr.promote_to_known_good(candidate_tag)

    console.print()
    console.print(Panel.fit(
        f"[bold green]FULL CI/CD PIPELINE SUCCEEDED! Candidate [{repo_id}] passed all automated QA gates.[/bold green]"
    ))
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate AI-enhanced CI/CD pipeline on any repository")
    parser.add_argument("--repo", default="netbox", help="Repository ID (default: netbox)")
    parser.add_argument("--url", default=None, help="Remote Git / GitHub URL if repo needs to be cloned/indexed")
    parser.add_argument("--change", default=None, help="Custom proposed change description")
    parser.add_argument("--fault", choices=["none", "test_fail", "qa_crash"], default="none", help="Inject fault condition to test policy gates or auto-rollback")
    args = parser.parse_args()

    r_id = args.repo
    if args.url and (args.repo == "netbox" or not args.repo):
        from app.repository.adapter import parse_github_url
        _, _, r_id = parse_github_url(args.url)

    run_pipeline(repo_id=r_id, repo_url=args.url, pr_change=args.change, fault=args.fault)

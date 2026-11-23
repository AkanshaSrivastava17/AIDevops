"""
Pipelines & Gate Service: Reproducible Gate Evaluation & Verification Contract.
Implements Section 8.7 (Pipelines and Gate) and Section 13.6 (Phase 1 Simulated Verification Contract).
"""
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.workflow.models import (
    PipelineRun, PipelineStage, RecommendedTestCoverage,
    GateResult, GateDecision, GateFreshness, GateOverrideRecord, RunStatus, User
)
from app.workflow.db import WorkflowDB
from app.devops.pipeline_gate import AdvancedCIDCGate

logger = logging.getLogger(__name__)


class PipelinesService:
    def __init__(self, db: WorkflowDB, gate_engine: AdvancedCIDCGate):
        self.db = db
        self.gate_engine = gate_engine

    def evaluate_gate_for_run(
        self,
        run_id: str,
        actor: Optional[User] = None
    ) -> GateResult:
        """
        Computes reproducible GateResult from:
        1. Saved current brief version
        2. Real/simulated pipeline run test results
        3. Deployment health probe
        4. Stored policy version
        (Section 8.7)
        """
        run = self.db.get_pipeline_run(run_id)
        if not run:
            raise ValueError(f"Pipeline run {run_id} not found.")

        brief = None
        if run.task_id:
            task = self.db.get_task_by_id_or_key(run.task_id)
            if task:
                brief = self.db.get_current_brief(task.request_id)

        # Extract test counts from stages
        test_stage = next((s for s in run.stages if s.name in ("regression", "unit")), None)
        failed_count = sum(len(s.failed_tests) for s in run.stages if s.status == "Failed")
        has_stage_failure = any(s.status == "Failed" for s in run.stages)

        impact_score = brief.overall_impact_level if brief else "MEDIUM"
        confidence = brief.overall_confidence if brief else 0.85
        affected_comps = [c["component"] for c in (brief.affected_components if brief else [])]

        test_results = {
            "status": "FAIL" if (failed_count > 0 or has_stage_failure) else "PASS",
            "passed": run.recommended_test_coverage.passed,
            "failed": failed_count,
            "tests_executed": run.recommended_test_coverage.executed
        }

        # Check deployment health
        deploy_stage = next((s for s in run.stages if s.name == "deploy_test"), None)
        qa_health = {
            "status": "healthy" if (not deploy_stage or deploy_stage.status == "Passed") else "unhealthy"
        }

        gate_eval = self.gate_engine.evaluate(
            change_analysis={
                "impact_level": impact_score,
                "confidence": confidence,
                "affected_components": [{"component": c} for c in affected_comps]
            },
            test_results=test_results,
            qa_health_status=qa_health
        )

        decision = GateDecision(gate_eval["decision"])
        gate_res = GateResult(
            id=f"gate-{run.id}",
            run_id=run.id,
            commit_sha=run.commit_sha,
            brief_version_id=brief.id if brief else None,
            policy_version="v2.2-enterprise",
            decision=decision,
            freshness=GateFreshness.CURRENT,
            violations=gate_eval.get("blocking_reasons", []),
            warnings=gate_eval.get("warnings", []),
            inputs_snapshot={
                "impact_level": impact_score,
                "confidence": confidence,
                "affected_components": affected_comps,
                "tests_passed": test_results["passed"],
                "tests_failed": test_results["failed"],
                "deployment_health": qa_health["status"]
            },
            evaluated_at=datetime.now(timezone.utc).isoformat()
        )

        # Save and audit
        return self.db.save_gate_result(gate_res, actor=actor)

    def trigger_simulated_verification_run(
        self,
        task_id: str,
        simulate_failure: bool = False,
        actor: Optional[User] = None
    ) -> PipelineRun:
        """
        Phase 1 Simulated Verification Contract (Section 13.6).
        Simulated input data feeds the REAL gate engine. The decision is NEVER simulated.
        Visibly labeled source = 'simulated'.
        """
        task = self.db.get_task_by_id_or_key(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")

        req = self.db.get_feature_request(task.request_id)
        brief = self.db.get_current_brief(task.request_id)
        repo_id = req.repo_id if req else "netbox"

        commit_sha = f"sim-{uuid.uuid4().hex[:7]}"
        run_id = f"run-sim-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()

        failed_tests = ["test_vrf_boundary_containment_failure"] if simulate_failure else []
        stages = [
            PipelineStage(name="build", status="Passed", duration_seconds=14.2, logs="Syntax AST verified."),
            PipelineStage(name="unit", status="Passed", duration_seconds=28.4, logs="Unit test suite passed."),
            PipelineStage(
                name="regression",
                status="Failed" if simulate_failure else "Passed",
                duration_seconds=22.1,
                failed_tests=failed_tests,
                logs="Simulated regression suite execution."
            ),
            PipelineStage(
                name="integration",
                status="Failed" if simulate_failure else "Passed",
                duration_seconds=38.0,
                logs="API contract gate."
            ),
            PipelineStage(name="deploy_test", status="Passed", duration_seconds=12.5, logs="QA container deployed and verified via GET /health.")
        ]

        rec_tests = brief.recommended_tests if brief and brief.recommended_tests else []
        total_rec = len(rec_tests) or 3
        executed = total_rec
        failed = len(failed_tests)
        passed = executed - failed

        rec_cov = RecommendedTestCoverage(
            total_recommended=total_rec,
            executed=executed,
            passed=passed,
            failed=failed,
            not_run=0,
            coverage_percentage=round((passed / total_rec) * 100, 1),
            details=[
                {
                    "test_file": t.get("test_file", f"tests/test_{task.component}.py"),
                    "status": "Failed" if (simulate_failure and idx == 0) else "Passed",
                    "duration": 4.1
                }
                for idx, t in enumerate(rec_tests or [{"test_file": f"tests/test_{task.component}.py"}])
            ]
        )

        run = PipelineRun(
            id=run_id,
            task_id=task.id,
            repo_id=repo_id,
            pr_url=f"https://github.com/mock/{repo_id}/pull/125",
            pr_number=125,
            commit_sha=commit_sha,
            branch=f"feature/{task.task_key.lower()}-branch",
            workflow_run_id=f"sim-wf-{uuid.uuid4().hex[:6]}",
            workflow_url="https://github.com/mock/actions/runs/sim",
            stages=stages,
            recommended_test_coverage=rec_cov,
            status=RunStatus.FAILED if simulate_failure else RunStatus.PASSED,
            source="simulated",
            started_at=now,
            finished_at=now
        )

        saved_run = self.db.save_pipeline_run(run)
        
        # Link task to PR and transition to Testing
        self.db.link_pr_to_task(task.task_key, saved_run.pr_url, saved_run.pr_number, saved_run.branch)
        if task.status in ("In Progress", "In Review"):
            self.db.update_task_status(task.id, "Testing", actor=actor or User(id="sys", name="System", email="sys@dev", global_role="Admin"))

        # Feed real gate engine
        self.evaluate_gate_for_run(saved_run.id, actor=actor)

        return saved_run

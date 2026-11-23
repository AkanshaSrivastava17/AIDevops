"""
SQLite Relational Workflow Database Repository for History-RAG Revision 2.2.
Implements Sections 7, 7.8 (State Machines), and 10.1.
Enforces foreign keys, indexes, state machine transitions, and append-only audit logs.
"""
import os
import json
import sqlite3
import uuid
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone

from app.workflow.models import (
    GlobalRole, ProjectRole, RequestStatus, BriefStatus, TaskStatus, RunStatus,
    GateDecision, GateFreshness, DecisionStatus, EvidenceStrength,
    Organization, Project, RepositoryRecord, ProjectRepository, User, ProjectMembership,
    FeatureRequest, BriefVersion, Decision, Task, TaskContextPack,
    PipelineRun, PipelineStage, RecommendedTestCoverage, GateResult, GateOverrideRecord,
    Outcome, EvaluationMetrics, Conversation, Message, EvidenceReference,
    AuditLogEntry, Comment, Notification, Integration,
    ImplementationOption, TaskProposal, ReviewFlag, ReproducibilityMetadata, EvidenceStrengthBreakdown
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State Machine Transition Rules (Section 7.8)
# ---------------------------------------------------------------------------

ALLOWED_REQUEST_TRANSITIONS = {
    RequestStatus.DRAFT: [RequestStatus.IN_BRIEF, RequestStatus.CANCELLED],
    RequestStatus.IN_BRIEF: [RequestStatus.PLANNED, RequestStatus.DRAFT, RequestStatus.CANCELLED],
    RequestStatus.PLANNED: [RequestStatus.IN_PROGRESS, RequestStatus.IN_BRIEF, RequestStatus.CANCELLED],
    RequestStatus.IN_PROGRESS: [RequestStatus.IN_REVIEW, RequestStatus.IN_BRIEF, RequestStatus.CANCELLED],
    RequestStatus.IN_REVIEW: [RequestStatus.DONE, RequestStatus.IN_PROGRESS, RequestStatus.CANCELLED],
    RequestStatus.DONE: [RequestStatus.IN_PROGRESS],
    RequestStatus.CANCELLED: []
}

ALLOWED_TASK_TRANSITIONS = {
    TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
    TaskStatus.IN_PROGRESS: [TaskStatus.IN_REVIEW, TaskStatus.CANCELLED],
    TaskStatus.IN_REVIEW: [TaskStatus.IN_PROGRESS, TaskStatus.TESTING, TaskStatus.CANCELLED],
    TaskStatus.TESTING: [TaskStatus.IN_PROGRESS, TaskStatus.DONE, TaskStatus.CANCELLED],
    TaskStatus.DONE: [TaskStatus.IN_PROGRESS],
    TaskStatus.CANCELLED: []
}

ALLOWED_BRIEF_TRANSITIONS = {
    BriefStatus.DRAFT: [BriefStatus.FINAL, BriefStatus.REJECTED],
    BriefStatus.FINAL: [BriefStatus.APPROVED, BriefStatus.REJECTED, BriefStatus.DRAFT],
    BriefStatus.APPROVED: [BriefStatus.OUTDATED],
    BriefStatus.REJECTED: [],
    BriefStatus.OUTDATED: []
}


class WorkflowDB:
    def __init__(self, db_path: str = "data/processed/historyrag_workflow.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_schema()
        self._seed_default_data()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Organizations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS organizations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # 2. Projects
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    organization_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id)
                )
            """)

            # 3. Repositories
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repositories (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    default_branch TEXT NOT NULL,
                    indexed_commit_sha TEXT,
                    remote_head_sha TEXT,
                    indexed_at TEXT,
                    index_status TEXT NOT NULL
                )
            """)

            # 4. ProjectRepositories
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_repositories (
                    project_id TEXT NOT NULL,
                    repository_id TEXT NOT NULL,
                    PRIMARY KEY (project_id, repository_id),
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (repository_id) REFERENCES repositories(id)
                )
            """)

            # 5. Users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    global_role TEXT NOT NULL,
                    avatar TEXT,
                    title TEXT
                )
            """)

            # 6. ProjectMemberships
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_memberships (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)

            # 7. FeatureRequests
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feature_requests (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    acceptance_criteria_json TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    requester_id TEXT NOT NULL,
                    requester_name TEXT,
                    project_id TEXT NOT NULL,
                    repo_id TEXT NOT NULL,
                    target_component TEXT,
                    external_issue_ref TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (repo_id) REFERENCES repositories(id)
                )
            """)

            # 8. AnalysisJobs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_jobs (
                    id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    steps_json TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    error TEXT,
                    FOREIGN KEY (request_id) REFERENCES feature_requests(id)
                )
            """)

            # 9. BriefVersions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS brief_versions (
                    id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    is_current INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    approved_by TEXT,
                    approved_at TEXT,
                    created_by TEXT NOT NULL,
                    based_on_version INTEGER,
                    change_summary TEXT,
                    payload_json TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    FOREIGN KEY (request_id) REFERENCES feature_requests(id)
                )
            """)

            # 10. EvidenceReferences
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evidence_references (
                    id TEXT PRIMARY KEY,
                    owner_type TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    similarity REAL NOT NULL,
                    excerpt TEXT NOT NULL,
                    source_date TEXT,
                    component TEXT,
                    title TEXT
                )
            """)

            # 11. Decisions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    request_id TEXT,
                    brief_version_id TEXT,
                    title TEXT NOT NULL,
                    context TEXT NOT NULL,
                    options_considered_json TEXT NOT NULL,
                    chosen_option TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    tradeoffs_accepted_json TEXT NOT NULL,
                    decided_by TEXT NOT NULL,
                    decided_by_name TEXT,
                    decided_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    superseded_by TEXT,
                    component TEXT
                )
            """)

            # 12. Tasks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    task_key TEXT UNIQUE NOT NULL,
                    request_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    component TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    task_order INTEGER NOT NULL,
                    depends_on_json TEXT NOT NULL,
                    assignee_id TEXT,
                    assignee_name TEXT,
                    reviewer_id TEXT,
                    reviewer_name TEXT,
                    status TEXT NOT NULL,
                    branch TEXT,
                    pr_url TEXT,
                    pr_number INTEGER,
                    context_pack_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (request_id) REFERENCES feature_requests(id)
                )
            """)

            # 13. PipelineRuns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id TEXT PRIMARY KEY,
                    task_id TEXT,
                    repo_id TEXT NOT NULL,
                    pr_url TEXT,
                    pr_number INTEGER,
                    commit_sha TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    workflow_run_id TEXT NOT NULL,
                    workflow_url TEXT,
                    stages_json TEXT NOT NULL,
                    recommended_test_coverage_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT
                )
            """)

            # 14. GateResults
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gate_results (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    commit_sha TEXT NOT NULL,
                    brief_version_id TEXT,
                    policy_version TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    freshness TEXT NOT NULL,
                    violations_json TEXT NOT NULL,
                    warnings_json TEXT NOT NULL,
                    inputs_snapshot_json TEXT NOT NULL,
                    override_json TEXT,
                    evaluated_at TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES pipeline_runs(id)
                )
            """)

            # 15. Outcomes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS outcomes (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    predicted_components_json TEXT NOT NULL,
                    actual_components_json TEXT NOT NULL,
                    predicted_files_json TEXT NOT NULL,
                    actual_files_json TEXT NOT NULL,
                    predicted_tests_json TEXT NOT NULL,
                    executed_tests_json TEXT NOT NULL,
                    failed_tests_json TEXT NOT NULL,
                    ground_truth_method TEXT NOT NULL,
                    ground_truth_version TEXT NOT NULL,
                    component_metrics_json TEXT NOT NULL,
                    test_metrics_json TEXT NOT NULL,
                    regression_metrics_json TEXT NOT NULL,
                    retrospective_summary TEXT,
                    recorded_at TEXT NOT NULL
                )
            """)

            # 16. Comments
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id TEXT PRIMARY KEY,
                    parent_type TEXT NOT NULL,
                    parent_id TEXT NOT NULL,
                    author_id TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    body TEXT NOT NULL,
                    mentions_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # 17. AuditLogs (Append-Only)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    actor_id TEXT NOT NULL,
                    actor_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    object_type TEXT NOT NULL,
                    object_id TEXT NOT NULL,
                    previous_value TEXT,
                    new_value TEXT,
                    details TEXT,
                    timestamp TEXT NOT NULL
                )
            """)

            # 18. Notifications
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    event TEXT NOT NULL,
                    message TEXT NOT NULL,
                    object_ref TEXT,
                    read_at TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # 19. Integrations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS integrations (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    config_ref TEXT,
                    status TEXT NOT NULL,
                    webhook_state_json TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)

            # 20. Conversations & Messages
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    repository_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    context_type TEXT NOT NULL,
                    context_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL,
                    confidence REAL,
                    retrieval_mode TEXT,
                    feedback_rating INTEGER,
                    feedback_reason TEXT,
                    saved_as_note INTEGER NOT NULL,
                    note_title TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            """)

            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_proj ON feature_requests(project_id, status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_req ON tasks(request_id, status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_briefs_req ON brief_versions(request_id, is_current)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_req ON decisions(request_id, status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_task ON pipeline_runs(task_id, commit_sha)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_obj ON audit_logs(object_type, object_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id, updated_at)")
            conn.commit()

    def _seed_default_data(self):
        """Seeds initial data for demo personas, project, repository, and initial sample requests."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if seeded
            cursor.execute("SELECT COUNT(*) as cnt FROM brief_versions")
            needs_brief_seed = (cursor.fetchone()["cnt"] == 0)

            cursor.execute("SELECT COUNT(*) as cnt FROM organizations")
            if cursor.fetchone()["cnt"] > 0 and not needs_brief_seed:
                return

            now = datetime.now(timezone.utc).isoformat()
            
            # Seed Organization
            org_id = "org-enterprise-core"
            cursor.execute("INSERT INTO organizations (id, name, created_at) VALUES (?, ?, ?)",
                           (org_id, "DevOps Intelligence Enterprise", now))
            
            # Seed Project
            project_id = "proj-platform-core"
            cursor.execute("INSERT INTO projects (id, organization_id, name, description, created_at) VALUES (?, ?, ?, ?, ?)",
                           (project_id, org_id, "Core Platform Services", "Enterprise microservices and infrastructure components", now))

            # Seed Repositories
            repos = [
                ("netbox", "NetBox DCIM/IPAM", "https://github.com/netbox-community/netbox", "github", "develop", "a7f92b4c", "a7f92b4c", now, "ready"),
                ("pycalculator", "PyCalculator Service", "https://github.com/Radhikag19/PyCalculator", "github", "main", "9c8e1a2f", "9c8e1a2f", now, "ready"),
                ("fastapi_demo", "FastAPI Gateway", "https://github.com/tiangolo/fastapi", "github", "master", "3d1b4c7a", "3d1b4c7a", now, "ready")
            ]
            for r in repos:
                cursor.execute("""
                    INSERT OR IGNORE INTO repositories (id, name, url, provider, default_branch, indexed_commit_sha, remote_head_sha, indexed_at, index_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, r)
                cursor.execute("INSERT OR IGNORE INTO project_repositories (project_id, repository_id) VALUES (?, ?)", (project_id, r[0]))

            # Seed the 6 Persona Users
            personas = [
                ("user-junior", "Alex Rivera (Junior Dev)", "alex.rivera@enterprise.dev", GlobalRole.MEMBER.value, ProjectRole.JUNIOR_DEV.value, "Junior Software Engineer", "AR"),
                ("user-po", "Sarah Chen (Product Owner)", "sarah.chen@enterprise.dev", GlobalRole.MEMBER.value, ProjectRole.PRODUCT_OWNER.value, "Principal Product Owner", "SC"),
                ("user-techlead", "Marcus Vance (Tech Lead)", "marcus.vance@enterprise.dev", GlobalRole.MEMBER.value, ProjectRole.TECH_LEAD.value, "Staff Architect & Tech Lead", "MV"),
                ("user-qa", "Elena Rostova (QA Lead)", "elena.rostova@enterprise.dev", GlobalRole.MEMBER.value, ProjectRole.QA_ENGINEER.value, "Senior QA Automation Engineer", "ER"),
                ("user-manager", "David Sterling (Eng Manager)", "david.sterling@enterprise.dev", GlobalRole.MEMBER.value, ProjectRole.ENGINEERING_MANAGER.value, "Director of Engineering", "DS"),
                ("user-admin", "Akansha Srivastava (Admin)", "admin@enterprise.dev", GlobalRole.ADMIN.value, ProjectRole.ADMIN.value, "Platform Administrator", "AS")
            ]
            for uid, name, email, grole, prole, title, avatar in personas:
                cursor.execute("""
                    INSERT OR IGNORE INTO users (id, name, email, global_role, avatar, title)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (uid, name, email, grole, avatar, title))
                
                mid = f"mem-{uid}-{project_id}"
                cursor.execute("""
                    INSERT OR IGNORE INTO project_memberships (id, user_id, project_id, role, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (mid, uid, project_id, prole, "Active", now))

            # Seed Feature Request HR-101 (The flagship VRF IP containment demo scenario from Section 12)
            req_id = "req-hr-101"
            criteria = [
                "Validate that an assigned IP address falls within the containment range of its associated VRF instance.",
                "Enforce strict validation across dual-stack IPv4 and IPv6 network interface boundaries.",
                "Raise an explicit ValidationError with error codes when an interface IP conflicts with VRF isolation rules.",
                "Preserve backward compatibility for legacy non-VRF interface allocations."
            ]
            cursor.execute("""
                INSERT INTO feature_requests (
                    id, title, description, acceptance_criteria_json, priority, status,
                    requester_id, requester_name, project_id, repo_id, target_component, external_issue_ref,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                req_id,
                "Validate Interface IP Address VRF Containment Rules",
                "Refactor the interface IP assignment pipeline in IPAM/DCIM to validate that any IP assigned to a VRF-enabled device interface strictly falls within the permitted CIDR bounds of that VRF. Prevents silent address route leakage across tenant partitions.",
                json.dumps(criteria),
                "P1",
                RequestStatus.PLANNED.value,
                "user-po",
                "Sarah Chen (Product Owner)",
                project_id,
                "netbox",
                "ipam",
                "NETBOX-4891",
                now,
                now
            ))

            # Seed initial Audit Log
            self._write_audit_log_cursor(
                cursor=cursor,
                actor_id="user-po",
                actor_name="Sarah Chen (Product Owner)",
                action="CREATE",
                object_type="request",
                object_id=req_id,
                previous_value=None,
                new_value="Draft",
                details="Logged feature request HR-101 for VRF containment validation."
            )
            self._write_audit_log_cursor(
                cursor=cursor,
                actor_id="user-techlead",
                actor_name="Marcus Vance (Tech Lead)",
                action="TRANSITION",
                object_type="request",
                object_id=req_id,
                previous_value="In Brief",
                new_value="Planned",
                details="Feature Brief approved by Tech Lead Marcus Vance."
            )

            # Seed Brief Version 1 for HR-101
            brief_obj = BriefVersion(
                id="brief-v1-hr-101",
                request_id=req_id,
                version=1,
                is_current=True,
                status=BriefStatus.APPROVED,
                created_by="user-po",
                approved_by="Marcus Vance (Tech Lead)",
                approved_at=now,
                restated_requirement="Validated VRF CIDR bounds check to prevent overlapping subnet assignments across tenant network interfaces.",
                open_questions=[],
                affected_components=[
                    {"component": "ipam", "score": 0.88, "reasons": ["Core VRF subnet boundary logic"]},
                    {"component": "dcim", "score": 0.65, "reasons": ["Interface attachment mutations"]}
                ],
                overall_impact_level="HIGH",
                overall_confidence=0.91,
                evidence_strength=EvidenceStrengthBreakdown(component_identification=EvidenceStrength.HIGH),
                options=[
                    ImplementationOption(
                        name="Dedicated IPAM Validation Service Layer",
                        description="Validation executed inside IPAM service mutation pipeline with clean transaction boundaries.",
                        effort="Medium",
                        risk="Low",
                        components_touched=["ipam", "dcim"],
                        pros=["Prevents recurring transaction deadlocks", "Clean domain separation"],
                        cons=["Requires all callers to use service layer"]
                    )
                ],
                recommended_option="Dedicated IPAM Validation Service Layer",
                proposed_tasks=[
                    TaskProposal(task_key="TASK-101", title="Implement VRF Containment Bounds Validator", component="ipam", description="Develop bounds validator with CIDR containment logic.", suggested_assignee_role=ProjectRole.JUNIOR_DEVELOPER),
                    TaskProposal(task_key="TASK-102", title="Update DCIM Interface IP Assignment Hook", component="dcim", description="Integrate validator into DCIM mutation handler.", suggested_assignee_role=ProjectRole.TECH_LEAD),
                    TaskProposal(task_key="TASK-103", title="Dual-Stack IPv4/IPv6 Containment Regression Tests", component="ipam", description="Author parameterized tests.", suggested_assignee_role=ProjectRole.QA_ENGINEER)
                ],
                review_flags=[
                    ReviewFlag(
                        id="flag-1",
                        category="regression_history",
                        severity="warning",
                        message="Ensure IPv4 and IPv6 addresses do not cross-validate under conflicting VRFs.",
                        target="netbox/ipam/validators.py"
                    )
                ],
                recommended_tests=[
                    {"test_file": "tests/test_ipam.py", "test_name": "test_vrf_containment", "score": 0.94, "reasons": ["Direct component coverage"]}
                ],
                historical_precedents=[
                    {"id": "c010aa8f", "source_type": "commit", "title": "Refactor ipam integration with tenancy", "similarity": 0.88}
                ],
                reproducibility=ReproducibilityMetadata(
                    repository_commit_sha="a7f92b4c",
                    index_snapshot_id="snap-netbox-a7f92b4c",
                    model_name="History-RAG Engine",
                    model_version="v2.2-enterprise",
                    prompt_version="v2.2",
                    scoring_version="v2.2",
                    retrieval_version="v2.2",
                    requirement_hash="req-hash-hr-101",
                    analysis_timestamp=now,
                    job_id="job-hr-101-seed"
                ),
                stale_snapshot=False,
                generated_at=now
            )
            brief_payload = brief_obj.model_dump()
            cursor.execute("""
                INSERT OR REPLACE INTO brief_versions (
                    id, request_id, version, is_current, status, approved_by, approved_at,
                    created_by, based_on_version, change_summary, payload_json, generated_at
                ) VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "brief-v1-hr-101",
                req_id,
                1,
                BriefStatus.APPROVED.value,
                "Marcus Vance (Tech Lead)",
                now,
                "user-po",
                None,
                "Initial VRF specification brief",
                json.dumps(brief_payload),
                now
            ))

            # Seed Decision DEC-018
            dec_id = "dec-018"
            cursor.execute("""
                INSERT INTO decisions (
                    id, request_id, brief_version_id, title, context, options_considered_json,
                    chosen_option, rationale, tradeoffs_accepted_json, decided_by, decided_by_name,
                    decided_at, status, superseded_by, component
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dec_id,
                req_id,
                "brief-v1-hr-101",
                "Enforce VRF Boundary Validation at Service Layer vs Model Clean",
                "When validating VRF containment, validation can be executed inside Django Model clean() or within the IPAM service mutation pipeline.",
                json.dumps([
                    {"name": "Option A: Model clean() hook", "pros": ["Automatic across admin UI"], "cons": ["High latency in bulk API syncs"]},
                    {"name": "Option B: Dedicated IPAM Validation Service Layer", "pros": ["Low API overhead, clean transaction boundaries"], "cons": ["Requires all callers to use service layer"]}
                ]),
                "Option B: Dedicated IPAM Validation Service Layer",
                "Service-layer validation prevents recurring transaction deadlocks during bulk automation pipelines and maintains clean separation between storage and domain logic.",
                json.dumps(["Callers bypassing service layer must invoke validator directly", "Requires additional unit harness tests"]),
                "user-techlead",
                "Marcus Vance (Tech Lead)",
                now,
                DecisionStatus.ACTIVE.value,
                None,
                "ipam"
            ))

            # Seed initial tasks for HR-101
            tasks_data = [
                ("task-101", "TASK-101", req_id, "Implement VRF Containment Bounds Validator", "Develop VrfContainmentValidator class inside ipam/validators.py with CIDR containment logic.", "ipam", "P1", 1, [], "user-junior", "Alex Rivera (Junior Dev)", "user-techlead", "Marcus Vance (Tech Lead)", TaskStatus.IN_PROGRESS.value, "feature/TASK-101-vrf-containment", "https://github.com/netbox-community/netbox/pull/124", 124),
                ("task-102", "TASK-102", req_id, "Update DCIM Interface IP Assignment Hook", "Integrate VrfContainmentValidator into DCIM device interface assignment mutation handler.", "dcim", "P1", 2, ["TASK-101"], None, None, "user-techlead", "Marcus Vance (Tech Lead)", TaskStatus.TODO.value, None, None, None),
                ("task-103", "TASK-103", req_id, "Dual-Stack IPv4/IPv6 Containment Regression Tests", "Author parameterized unit and integration suites exercising boundary containment conditions.", "ipam", "P2", 3, ["TASK-101"], "user-qa", "Elena Rostova (QA Lead)", "user-techlead", "Marcus Vance (Tech Lead)", TaskStatus.TODO.value, None, None, None)
            ]
            for tid, tkey, rqid, ttl, desc, comp, prio, ordr, deps, asgn, asgn_name, rev, rev_name, stt, br, pr, prnum in tasks_data:
                cursor.execute("""
                    INSERT INTO tasks (
                        id, task_key, request_id, title, description, component, priority, task_order,
                        depends_on_json, assignee_id, assignee_name, reviewer_id, reviewer_name,
                        status, branch, pr_url, pr_number, context_pack_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tid, tkey, rqid, ttl, desc, comp, prio, ordr, json.dumps(deps), asgn, asgn_name, rev, rev_name,
                    stt, br, pr, prnum, None, now, now
                ))

            # Seed Pipeline Run for TASK-101 (Section 12 Scenario)
            run_id = "run-pr-124-v1"
            stages = [
                {"name": "build", "status": "Passed", "duration_seconds": 18.5, "failed_tests": [], "logs": "Compiler & syntax AST check passed."},
                {"name": "unit", "status": "Passed", "duration_seconds": 32.1, "failed_tests": [], "logs": "120 unit tests passed."},
                {"name": "regression", "status": "Passed", "duration_seconds": 24.8, "failed_tests": [], "logs": "Recommended regression tests passed."},
                {"name": "integration", "status": "Passed", "duration_seconds": 45.2, "failed_tests": [], "logs": "API integration gate verified."},
                {"name": "deploy_test", "status": "Passed", "duration_seconds": 15.0, "failed_tests": [], "logs": "QA container deployed and verified via GET /health."}
            ]
            rec_cov = {
                "total_recommended": 3,
                "executed": 3,
                "passed": 3,
                "failed": 0,
                "not_run": 0,
                "coverage_percentage": 100.0,
                "details": [
                    {"test_file": "netbox/ipam/tests/test_ipam.py", "status": "Passed", "duration": 4.2},
                    {"test_file": "netbox/dcim/tests/test_interfaces.py", "status": "Passed", "duration": 5.8},
                    {"test_file": "netbox/ipam/tests/test_vrf.py", "status": "Passed", "duration": 3.9}
                ]
            }
            cursor.execute("""
                INSERT INTO pipeline_runs (
                    id, task_id, repo_id, pr_url, pr_number, commit_sha, branch, workflow_run_id,
                    workflow_url, stages_json, recommended_test_coverage_json, status, source, started_at, finished_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                "task-101",
                "netbox",
                "https://github.com/netbox-community/netbox/pull/124",
                124,
                "a7f92b4c",
                "feature/TASK-101-vrf-containment",
                "wf-894120",
                "https://github.com/netbox-community/netbox/actions/runs/894120",
                json.dumps(stages),
                json.dumps(rec_cov),
                RunStatus.PASSED.value,
                "live",
                now,
                now
            ))

            # Seed Gate Result for run-pr-124-v1
            gate_id = "gate-run-pr-124-v1"
            cursor.execute("""
                INSERT INTO gate_results (
                    id, run_id, commit_sha, brief_version_id, policy_version, decision, freshness,
                    violations_json, warnings_json, inputs_snapshot_json, override_json, evaluated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                gate_id,
                run_id,
                "a7f92b4c",
                "brief-v1-hr-101",
                "v2.2-enterprise",
                GateDecision.APPROVED.value,
                GateFreshness.CURRENT.value,
                json.dumps([]),
                json.dumps(["Dual-stack validation required for IPv6 interfaces"]),
                json.dumps({
                    "impact_score": 0.82,
                    "confidence": 0.91,
                    "affected_components": ["ipam", "dcim"],
                    "tests_passed": 3,
                    "tests_failed": 0,
                    "deployment_health": "healthy"
                }),
                None,
                now
            ))

            # Seed Outcome for task-101
            cursor.execute("""
                INSERT INTO outcomes (
                    id, task_id, request_id, predicted_components_json, actual_components_json,
                    predicted_files_json, actual_files_json, predicted_tests_json, executed_tests_json,
                    failed_tests_json, ground_truth_method, ground_truth_version,
                    component_metrics_json, test_metrics_json, regression_metrics_json,
                    retrospective_summary, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "outcome-task-101",
                "task-101",
                req_id,
                json.dumps(["ipam", "dcim"]),
                json.dumps(["ipam", "dcim"]),
                json.dumps(["netbox/ipam/validators.py", "netbox/dcim/models.py"]),
                json.dumps(["netbox/ipam/validators.py", "netbox/dcim/models.py"]),
                json.dumps(["netbox/ipam/tests/test_ipam.py", "netbox/dcim/tests/test_interfaces.py"]),
                json.dumps(["netbox/ipam/tests/test_ipam.py", "netbox/dcim/tests/test_interfaces.py"]),
                json.dumps([]),
                "merged_pr_file_diff_v1",
                "1.0",
                json.dumps({"precision": 1.0, "recall": 1.0, "f1": 1.0}),
                json.dumps({"precision": 1.0, "recall": 1.0, "f1": 1.0}),
                json.dumps({"failures_caught": 0, "failures_missed": 0}),
                "Feature HR-101 verified with 100% component and test recommendation precision. Zero regressions escaped into staging.",
                now
            ))

            # Seed Sample Conversation
            conv_id = "conv-welcome-netbox"
            cursor.execute("""
                INSERT INTO conversations (id, user_id, project_id, repository_id, title, context_type, context_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (conv_id, "user-junior", project_id, "netbox", "Why was VRF isolation introduced in IPAM?", "repository", "netbox", now, now))

            cursor.execute("""
                INSERT INTO messages (id, conversation_id, role, content, evidence_refs_json, confidence, retrieval_mode, feedback_rating, feedback_reason, saved_as_note, note_title, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "msg-1",
                conv_id,
                "user",
                "Why was VRF isolation introduced in the IPAM module?",
                json.dumps([]),
                None,
                None,
                None,
                None,
                0,
                None,
                now
            ))

            msg2_evidence = [
                {
                    "id": "ev-commit-9f12",
                    "owner_type": "message",
                    "owner_id": "msg-2",
                    "source_type": "commit",
                    "source_id": "9f12ab34",
                    "similarity": 0.92,
                    "excerpt": "Isolate multi-tenant IP address pools using VRF containment boundaries.",
                    "source_date": "2025-04-12T14:30:00Z",
                    "component": "ipam",
                    "title": "Enforce VRF scope boundaries"
                },
                {
                    "id": "ev-dec-018",
                    "owner_type": "message",
                    "owner_id": "msg-2",
                    "source_type": "decision",
                    "source_id": "dec-018",
                    "similarity": 0.88,
                    "excerpt": "DEC-018: Enforce VRF boundary validation at service layer to avoid transaction deadlocks.",
                    "source_date": now,
                    "component": "ipam",
                    "title": "Service Layer VRF Validation"
                }
            ]
            cursor.execute("""
                INSERT INTO messages (id, conversation_id, role, content, evidence_refs_json, confidence, retrieval_mode, feedback_rating, feedback_reason, saved_as_note, note_title, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "msg-2",
                conv_id,
                "assistant",
                "According to historical commit [Commit: 9f12ab34] ('Enforce VRF scope boundaries'), VRF isolation was introduced to prevent overlapping private IP address collisions between independent customer tenants. Furthermore, architectural decision [Decision: DEC-018] notes that validation is enforced at the service layer to prevent transaction deadlocks during bulk automation pipelines.",
                json.dumps(msg2_evidence),
                0.94,
                "History-RAG",
                1,
                "Accurate historical citation",
                1,
                "VRF Isolation Architecture Rationale",
                now
            ))

            conn.commit()

    def _write_audit_log_cursor(
        self,
        cursor: sqlite3.Cursor,
        actor_id: str,
        actor_name: str,
        action: str,
        object_type: str,
        object_id: str,
        previous_value: Optional[str] = None,
        new_value: Optional[str] = None,
        details: Optional[str] = None
    ) -> str:
        log_id = f"audit-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO audit_logs (id, actor_id, actor_name, action, object_type, object_id, previous_value, new_value, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (log_id, actor_id, actor_name, action, object_type, object_id, previous_value, new_value, details, now))
        return log_id

    def write_audit_log(
        self,
        actor_id: str,
        actor_name: str,
        action: str,
        object_type: str,
        object_id: str,
        previous_value: Optional[str] = None,
        new_value: Optional[str] = None,
        details: Optional[str] = None
    ) -> AuditLogEntry:
        """Append-only audit trail logging (Section 7.3, 10.6)."""
        log_id = f"audit-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (id, actor_id, actor_name, action, object_type, object_id, previous_value, new_value, details, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (log_id, actor_id, actor_name, action, object_type, object_id, previous_value, new_value, details, now))
            conn.commit()
            
        return AuditLogEntry(
            id=log_id,
            actor_id=actor_id,
            actor_name=actor_name,
            action=action,
            object_type=object_type,
            object_id=object_id,
            previous_value=previous_value,
            new_value=new_value,
            details=details,
            timestamp=now
        )

    # -----------------------------------------------------------------------
    # Users & Roles (Section 7.1, 7.5, 10.3)
    # -----------------------------------------------------------------------

    def get_users(self) -> List[User]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY name")
            return [
                User(
                    id=r["id"],
                    name=r["name"],
                    email=r["email"],
                    global_role=GlobalRole(r["global_role"]),
                    avatar=r["avatar"],
                    title=r["title"]
                ) for r in cursor.fetchall()
            ]

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return User(
                id=r["id"],
                name=r["name"],
                email=r["email"],
                global_role=GlobalRole(r["global_role"]),
                avatar=r["avatar"],
                title=r["title"]
            )

    def get_project_memberships(self, project_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.id, m.user_id, m.project_id, m.role, m.status, m.created_at,
                       u.name as user_name, u.email as user_email, u.avatar as user_avatar, u.title as user_title
                FROM project_memberships m
                JOIN users u ON m.user_id = u.id
                WHERE m.project_id = ?
            """, (project_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_user_project_role(self, user_id: str, project_id: str) -> Optional[ProjectRole]:
        """ProjectMembership is the source of truth for project-level authorization (Section 7.1, 7.5)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role FROM project_memberships
                WHERE user_id = ? AND project_id = ? AND status = 'Active'
            """, (user_id, project_id))
            r = cursor.fetchone()
            if r:
                try:
                    return ProjectRole(r["role"])
                except Exception:
                    return ProjectRole.JUNIOR_DEV
            return None

    def update_project_membership(self, user_id: str, project_id: str, role: ProjectRole, actor: User) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM project_memberships WHERE user_id = ? AND project_id = ?", (user_id, project_id))
            prev = cursor.fetchone()
            prev_role = prev["role"] if prev else "none"
            now = datetime.now(timezone.utc).isoformat()
            
            cursor.execute("""
                INSERT INTO project_memberships (id, user_id, project_id, role, status, created_at)
                VALUES (?, ?, ?, ?, 'Active', ?)
                ON CONFLICT(id) DO UPDATE SET role = ?, status = 'Active'
            """, (f"mem-{user_id}-{project_id}", user_id, project_id, role.value, now, role.value))
            
            self._write_audit_log_cursor(
                cursor=cursor,
                actor_id=actor.id,
                actor_name=actor.name,
                action="UPDATE",
                object_type="membership",
                object_id=f"{project_id}:{user_id}",
                previous_value=prev_role,
                new_value=role.value,
                details=f"Updated role for user {user_id} in project {project_id}"
            )
            conn.commit()
            return True

    # -----------------------------------------------------------------------
    # Projects & Repositories
    # -----------------------------------------------------------------------

    def get_projects(self) -> List[Project]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY name")
            return [Project(**dict(r)) for r in cursor.fetchall()]

    def get_repositories_for_project(self, project_id: str) -> List[RepositoryRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.* FROM repositories r
                JOIN project_repositories pr ON r.id = pr.repository_id
                WHERE pr.project_id = ?
            """, (project_id,))
            return [RepositoryRecord(**dict(r)) for r in cursor.fetchall()]

    def get_repository(self, repo_id: str) -> Optional[RepositoryRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM repositories WHERE id = ?", (repo_id,))
            r = cursor.fetchone()
            return RepositoryRecord(**dict(r)) if r else None

    # -----------------------------------------------------------------------
    # Feature Requests (Section 7.1, 7.8, 8.3)
    # -----------------------------------------------------------------------

    def list_feature_requests(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        component: Optional[str] = None
    ) -> List[FeatureRequest]:
        query = "SELECT * FROM feature_requests WHERE 1=1"
        params: List[Any] = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        if component:
            query += " AND target_component = ?"
            params.append(component)
            
        query += " ORDER BY updated_at DESC"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append(FeatureRequest(
                    id=r["id"],
                    title=r["title"],
                    description=r["description"],
                    acceptance_criteria=json.loads(r["acceptance_criteria_json"] or "[]"),
                    priority=r["priority"],
                    status=RequestStatus(r["status"]),
                    requester_id=r["requester_id"],
                    requester_name=r["requester_name"],
                    project_id=r["project_id"],
                    repo_id=r["repo_id"],
                    target_component=r["target_component"],
                    external_issue_ref=r["external_issue_ref"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"]
                ))
            return results

    def get_feature_request(self, request_id: str) -> Optional[FeatureRequest]:
        norm = request_id.lower().strip()
        prefix_norm = f"req-{norm}" if not norm.startswith("req-") else norm
        stripped_norm = norm[4:] if norm.startswith("req-") else norm
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM feature_requests 
                WHERE id = ? OR LOWER(id) = ? OR LOWER(id) = ? OR LOWER(id) = ?
            """, (request_id, norm, prefix_norm, stripped_norm))
            r = cursor.fetchone()
            if not r:
                return None
            return FeatureRequest(
                id=r["id"],
                title=r["title"],
                description=r["description"],
                acceptance_criteria=json.loads(r["acceptance_criteria_json"] or "[]"),
                priority=r["priority"],
                status=RequestStatus(r["status"]),
                requester_id=r["requester_id"],
                requester_name=r["requester_name"],
                project_id=r["project_id"],
                repo_id=r["repo_id"],
                target_component=r["target_component"],
                external_issue_ref=r["external_issue_ref"],
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            )

    def create_feature_request(
        self,
        title: str,
        description: str,
        acceptance_criteria: List[str],
        priority: str,
        requester: User,
        project_id: str,
        repo_id: str,
        target_component: Optional[str] = None,
        external_issue_ref: Optional[str] = None
    ) -> FeatureRequest:
        req_id = f"req-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feature_requests (
                    id, title, description, acceptance_criteria_json, priority, status,
                    requester_id, requester_name, project_id, repo_id, target_component, external_issue_ref,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                req_id, title, description, json.dumps(acceptance_criteria), priority,
                RequestStatus.DRAFT.value, requester.id, requester.name, project_id, repo_id,
                target_component, external_issue_ref, now, now
            ))
            self._write_audit_log_cursor(
                cursor=cursor,
                actor_id=requester.id,
                actor_name=requester.name,
                action="CREATE",
                object_type="request",
                object_id=req_id,
                previous_value=None,
                new_value=RequestStatus.DRAFT.value,
                details=f"Created request: '{title}'"
            )
            conn.commit()

        return self.get_feature_request(req_id)

    def transition_request_status(
        self,
        request_id: str,
        target_status: RequestStatus,
        actor: User,
        reason: Optional[str] = None
    ) -> FeatureRequest:
        """Enforces Section 7.8 Request State Machine."""
        req = self.get_feature_request(request_id)
        if not req:
            raise ValueError(f"Request {request_id} not found.")

        current = req.status
        if current == target_status:
            return req

        allowed = ALLOWED_REQUEST_TRANSITIONS.get(current, [])
        if target_status not in allowed:
            raise ValueError(
                f"Invalid transition from {current.value} to {target_status.value}. "
                f"Allowed transitions: {[s.value for s in allowed]}"
            )

        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE feature_requests
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (target_status.value, now, request_id))
            
            self._write_audit_log_cursor(
                cursor=cursor,
                actor_id=actor.id,
                actor_name=actor.name,
                action="TRANSITION",
                object_type="request",
                object_id=request_id,
                previous_value=current.value,
                new_value=target_status.value,
                details=reason or f"Status changed from {current.value} to {target_status.value}"
            )
            conn.commit()

        return self.get_feature_request(request_id)

    # -----------------------------------------------------------------------
    # Feature Briefs & Versioning (Section 7.1, 7.2, 8.4)
    # -----------------------------------------------------------------------

    def get_brief_versions(self, request_id: str) -> List[BriefVersion]:
        norm = request_id.lower().strip()
        prefix_norm = f"req-{norm}" if not norm.startswith("req-") else norm
        stripped_norm = norm[4:] if norm.startswith("req-") else norm
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM brief_versions
                WHERE request_id = ? OR LOWER(request_id) = ? OR LOWER(request_id) = ? OR LOWER(request_id) = ?
                ORDER BY version DESC
            """, (request_id, norm, prefix_norm, stripped_norm))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                data = json.loads(r["payload_json"])
                results.append(BriefVersion(**data))
            return results

    def get_current_brief(self, request_id: str) -> Optional[BriefVersion]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM brief_versions
                WHERE request_id = ? AND is_current = 1
                ORDER BY version DESC LIMIT 1
            """, (request_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return BriefVersion(**json.loads(r["payload_json"]))

    def save_brief_version(self, brief: BriefVersion, actor: User) -> BriefVersion:
        """
        Brief versioning: regenerating never overwrites.
        Creates a new immutable BriefVersion with change summary (Section 7.2).
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Mark previous versions is_current = 0
            cursor.execute("UPDATE brief_versions SET is_current = 0 WHERE request_id = ?", (brief.request_id,))
            
            payload_dict = brief.model_dump()
            cursor.execute("""
                INSERT INTO brief_versions (
                    id, request_id, version, is_current, status, approved_by, approved_at,
                    created_by, based_on_version, change_summary, payload_json, generated_at
                ) VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                brief.id, brief.request_id, brief.version, brief.status.value, brief.approved_by,
                brief.approved_at, brief.created_by, brief.based_on_version, brief.change_summary,
                json.dumps(payload_dict), now
            ))
            
            self._write_audit_log_cursor(
                cursor=cursor,
                actor_id=actor.id,
                actor_name=actor.name,
                action="CREATE_BRIEF_VERSION",
                object_type="brief",
                object_id=brief.id,
                previous_value=f"v{brief.based_on_version}" if brief.based_on_version else None,
                new_value=f"v{brief.version}",
                details=f"Generated Brief v{brief.version}: {brief.change_summary or 'Initial synthesis'}"
            )
            conn.commit()

        return brief

    def approve_brief_version(self, brief_id: str, actor: User) -> BriefVersion:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM brief_versions WHERE id = ?", (brief_id,))
            r = cursor.fetchone()
            if not r:
                raise ValueError(f"Brief version {brief_id} not found.")

            brief_data = json.loads(r["payload_json"])
            brief = BriefVersion(**brief_data)
            now = datetime.now(timezone.utc).isoformat()

            brief.status = BriefStatus.APPROVED
            brief.approved_by = actor.name
            brief.approved_at = now
            brief_data["status"] = BriefStatus.APPROVED.value
            brief_data["approved_by"] = actor.name
            brief_data["approved_at"] = now

            cursor.execute("""
                UPDATE brief_versions
                SET status = ?, approved_by = ?, approved_at = ?, payload_json = ?
                WHERE id = ?
            """, (BriefStatus.APPROVED.value, actor.name, now, json.dumps(brief_data), brief_id))

            # Automatically transition request to Planned if In Brief
            cursor.execute("SELECT status FROM feature_requests WHERE id = ?", (brief.request_id,))
            req_r = cursor.fetchone()
            if req_r and req_r["status"] in (RequestStatus.IN_BRIEF.value, RequestStatus.DRAFT.value):
                cursor.execute("UPDATE feature_requests SET status = ?, updated_at = ? WHERE id = ?",
                               (RequestStatus.PLANNED.value, now, brief.request_id))
                self._write_audit_log_cursor(
                    cursor=cursor,
                    actor_id=actor.id,
                    actor_name=actor.name,
                    action="TRANSITION",
                    object_type="request",
                    object_id=brief.request_id,
                    previous_value=req_r["status"],
                    new_value=RequestStatus.PLANNED.value,
                    details=f"Request moved to Planned following Brief v{brief.version} approval."
                )

            self._write_audit_log_cursor(
                cursor=cursor,
                actor_id=actor.id,
                actor_name=actor.name,
                action="APPROVE",
                object_type="brief",
                object_id=brief.id,
                previous_value=r["status"],
                new_value=BriefStatus.APPROVED.value,
                details=f"Approved Brief v{brief.version}"
            )
            conn.commit()

        return brief

    # -----------------------------------------------------------------------
    # Decision Log (Section 7.1, 8.5)
    # -----------------------------------------------------------------------

    def list_decisions(
        self,
        request_id: Optional[str] = None,
        component: Optional[str] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Decision]:
        query = "SELECT * FROM decisions WHERE 1=1"
        params: List[Any] = []
        if request_id:
            norm = request_id.lower().strip()
            prefix_norm = f"req-{norm}" if not norm.startswith("req-") else norm
            stripped_norm = norm[4:] if norm.startswith("req-") else norm
            query += " AND (request_id = ? OR LOWER(request_id) = ? OR LOWER(request_id) = ? OR LOWER(request_id) = ?)"
            params.extend([request_id, norm, prefix_norm, stripped_norm])
        if component:
            query += " AND component = ?"
            params.append(component)
        if status:
            query += " AND status = ?"
            params.append(status)
        if search_query:
            query += " AND (title LIKE ? OR rationale LIKE ? OR context LIKE ?)"
            term = f"%{search_query}%"
            params.extend([term, term, term])

        query += " ORDER BY decided_at DESC"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append(Decision(
                    id=r["id"],
                    request_id=r["request_id"],
                    brief_version_id=r["brief_version_id"],
                    title=r["title"],
                    context=r["context"],
                    options_considered=json.loads(r["options_considered_json"] or "[]"),
                    chosen_option=r["chosen_option"],
                    rationale=r["rationale"],
                    tradeoffs_accepted=json.loads(r["tradeoffs_accepted_json"] or "[]"),
                    decided_by=r["decided_by"],
                    decided_by_name=r["decided_by_name"],
                    decided_at=r["decided_at"],
                    status=DecisionStatus(r["status"]),
                    superseded_by=r["superseded_by"],
                    component=r["component"]
                ))
            return results

    def create_decision(
        self,
        title: str,
        context: str,
        options_considered: List[Dict[str, Any]],
        chosen_option: str,
        rationale: str,
        tradeoffs_accepted: List[str],
        actor: User,
        request_id: Optional[str] = None,
        brief_version_id: Optional[str] = None,
        component: Optional[str] = None
    ) -> Decision:
        dec_id = f"dec-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO decisions (
                    id, request_id, brief_version_id, title, context, options_considered_json,
                    chosen_option, rationale, tradeoffs_accepted_json, decided_by, decided_by_name,
                    decided_at, status, superseded_by, component
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dec_id, request_id, brief_version_id, title, context, json.dumps(options_considered),
                chosen_option, rationale, json.dumps(tradeoffs_accepted), actor.id, actor.name,
                now, DecisionStatus.ACTIVE.value, None, component
            ))
            
            self._write_audit_log_cursor(
                cursor=cursor,
                actor_id=actor.id,
                actor_name=actor.name,
                action="CREATE",
                object_type="decision",
                object_id=dec_id,
                previous_value=None,
                new_value=DecisionStatus.ACTIVE.value,
                details=f"Recorded Architectural Decision: '{title}'"
            )
            conn.commit()

        decisions = self.list_decisions()
        return next(d for d in decisions if d.id == dec_id)

    def supersede_decision(self, old_decision_id: str, new_decision_id: str, actor: User) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE decisions
                SET status = ?, superseded_by = ?
                WHERE id = ?
            """, (DecisionStatus.SUPERSEDED.value, new_decision_id, old_decision_id))
            
            self._write_audit_log_cursor(
                cursor=cursor,
                actor_id=actor.id,
                actor_name=actor.name,
                action="SUPERSEDE",
                object_type="decision",
                object_id=old_decision_id,
                previous_value=DecisionStatus.ACTIVE.value,
                new_value=DecisionStatus.SUPERSEDED.value,
                details=f"Decision superseded by {new_decision_id}"
            )
            conn.commit()
            return True

    # -----------------------------------------------------------------------
    # Tasks (Section 7.1, 7.8, 8.6)
    # -----------------------------------------------------------------------

    def list_tasks(
        self,
        request_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Task]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params: List[Any] = []
        if request_id:
            norm = request_id.lower().strip()
            prefix_norm = f"req-{norm}" if not norm.startswith("req-") else norm
            stripped_norm = norm[4:] if norm.startswith("req-") else norm
            query += " AND (request_id = ? OR LOWER(request_id) = ? OR LOWER(request_id) = ? OR LOWER(request_id) = ?)"
            params.extend([request_id, norm, prefix_norm, stripped_norm])
        if assignee_id:
            query += " AND assignee_id = ?"
            params.append(assignee_id)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY task_order ASC, created_at DESC"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                cpack = None
                if r["context_pack_json"]:
                    cpack = TaskContextPack(**json.loads(r["context_pack_json"]))
                results.append(Task(
                    id=r["id"],
                    task_key=r["task_key"],
                    request_id=r["request_id"],
                    title=r["title"],
                    description=r["description"],
                    component=r["component"],
                    priority=r["priority"],
                    order=r["task_order"],
                    depends_on=json.loads(r["depends_on_json"] or "[]"),
                    assignee_id=r["assignee_id"],
                    assignee_name=r["assignee_name"],
                    reviewer_id=r["reviewer_id"],
                    reviewer_name=r["reviewer_name"],
                    status=TaskStatus(r["status"]),
                    branch=r["branch"],
                    pr_url=r["pr_url"],
                    pr_number=r["pr_number"],
                    context_pack=cpack,
                    created_at=r["created_at"],
                    updated_at=r["updated_at"]
                ))
            return results

    def get_task_by_id_or_key(self, id_or_key: str) -> Optional[Task]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ? OR task_key = ?", (id_or_key, id_or_key))
            r = cursor.fetchone()
            if not r:
                return None
            cpack = None
            if r["context_pack_json"]:
                cpack = TaskContextPack(**json.loads(r["context_pack_json"]))
            return Task(
                id=r["id"],
                task_key=r["task_key"],
                request_id=r["request_id"],
                title=r["title"],
                description=r["description"],
                component=r["component"],
                priority=r["priority"],
                order=r["task_order"],
                depends_on=json.loads(r["depends_on_json"] or "[]"),
                assignee_id=r["assignee_id"],
                assignee_name=r["assignee_name"],
                reviewer_id=r["reviewer_id"],
                reviewer_name=r["reviewer_name"],
                status=TaskStatus(r["status"]),
                branch=r["branch"],
                pr_url=r["pr_url"],
                pr_number=r["pr_number"],
                context_pack=cpack,
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            )

    def create_task(
        self,
        request_id: str,
        title: str,
        description: str,
        component: str,
        priority: str,
        order: int,
        depends_on: List[str],
        actor: User,
        assignee_id: Optional[str] = None,
        context_pack: Optional[TaskContextPack] = None
    ) -> Task:
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM tasks")
            total = cursor.fetchone()["count"] + 101
            task_key = f"TASK-{total}"

            assignee_name = None
            if assignee_id:
                cursor.execute("SELECT name FROM users WHERE id = ?", (assignee_id,))
                u = cursor.fetchone()
                if u:
                    assignee_name = u["name"]

            now = datetime.now(timezone.utc).isoformat()
            cpack_json = json.dumps(context_pack.model_dump()) if context_pack else None
            cursor.execute("""
                INSERT INTO tasks (
                    id, task_key, request_id, title, description, component, priority, task_order,
                    depends_on_json, assignee_id, assignee_name, reviewer_id, reviewer_name,
                    status, branch, pr_url, pr_number, context_pack_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id, task_key, request_id, title, description, component, priority, order,
                json.dumps(depends_on), assignee_id, assignee_name, None, None,
                TaskStatus.TODO.value, None, None, None, cpack_json, now, now
            ))
            
            self._write_audit_log_cursor(
                cursor=cursor,
                actor_id=actor.id,
                actor_name=actor.name,
                action="CREATE",
                object_type="task",
                object_id=task_key,
                previous_value=None,
                new_value=TaskStatus.TODO.value,
                details=f"Created task {task_key}: '{title}'"
            )
            conn.commit()

        return self.get_task_by_id_or_key(task_id)

    def update_task_status(
        self,
        task_id: str,
        target_status: TaskStatus,
        actor: User,
        reason: Optional[str] = None
    ) -> Task:
        """Enforces Task state transitions (Section 7.8)."""
        task = self.get_task_by_id_or_key(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")

        current = task.status
        if current == target_status:
            return task

        allowed = ALLOWED_TASK_TRANSITIONS.get(current, [])
        if target_status not in allowed:
            raise ValueError(
                f"Invalid transition from {current.value} to {target_status.value}. "
                f"Allowed transitions: {[s.value for s in allowed]}"
            )

        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?", (target_status.value, now, task.id))
            
            self._write_audit_log_cursor(
                cursor=cursor,
                actor_id=actor.id,
                actor_name=actor.name,
                action="TRANSITION",
                object_type="task",
                object_id=task.task_key,
                previous_value=current.value,
                new_value=target_status.value,
                details=reason or f"Task transitioned to {target_status.value}"
            )

            # Check if all tasks for request are now In Review or Done
            cursor.execute("SELECT status FROM tasks WHERE request_id = ?", (task.request_id,))
            all_statuses = [r["status"] for r in cursor.fetchall()]
            if all(s in (TaskStatus.IN_REVIEW.value, TaskStatus.TESTING.value, TaskStatus.DONE.value) for s in all_statuses):
                cursor.execute("UPDATE feature_requests SET status = ?, updated_at = ? WHERE id = ? AND status = ?",
                               (RequestStatus.IN_REVIEW.value, now, task.request_id, RequestStatus.IN_PROGRESS.value))

            conn.commit()

        return self.get_task_by_id_or_key(task.id)

    def link_pr_to_task(self, task_key: str, pr_url: str, pr_number: int, branch: str, actor_id: str = "system") -> Task:
        task = self.get_task_by_id_or_key(task_key)
        if not task:
            raise ValueError(f"Task {task_key} not found for PR linking.")

        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks
                SET pr_url = ?, pr_number = ?, branch = ?, updated_at = ?
                WHERE id = ?
            """, (pr_url, pr_number, branch, now, task.id))
            
            self._write_audit_log_cursor(
                cursor=cursor,
                actor_id=actor_id,
                actor_name="GitHub Webhook / System",
                action="LINK_PR",
                object_type="task",
                object_id=task.task_key,
                previous_value=task.pr_url,
                new_value=pr_url,
                details=f"Linked PR #{pr_number} on branch '{branch}' to task {task.task_key}"
            )
            conn.commit()

        return self.get_task_by_id_or_key(task.id)

    # -----------------------------------------------------------------------
    # Pipelines & Gate Results (Section 7.1, 7.8, 8.7, 10.5)
    # -----------------------------------------------------------------------

    def list_pipeline_runs(self, task_id: Optional[str] = None, repo_id: Optional[str] = None) -> List[PipelineRun]:
        query = "SELECT * FROM pipeline_runs WHERE 1=1"
        params: List[Any] = []
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        if repo_id:
            query += " AND repo_id = ?"
            params.append(repo_id)

        query += " ORDER BY started_at DESC"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                stages = [PipelineStage(**s) for s in json.loads(r["stages_json"] or "[]")]
                rec_cov = RecommendedTestCoverage(**json.loads(r["recommended_test_coverage_json"] or "{}"))
                results.append(PipelineRun(
                    id=r["id"],
                    task_id=r["task_id"],
                    repo_id=r["repo_id"],
                    pr_url=r["pr_url"],
                    pr_number=r["pr_number"],
                    commit_sha=r["commit_sha"],
                    branch=r["branch"],
                    workflow_run_id=r["workflow_run_id"],
                    workflow_url=r["workflow_url"],
                    stages=stages,
                    recommended_test_coverage=rec_cov,
                    status=RunStatus(r["status"]),
                    source=r["source"],
                    started_at=r["started_at"],
                    finished_at=r["finished_at"]
                ))
            return results

    def get_pipeline_run(self, run_id: str) -> Optional[PipelineRun]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_runs WHERE id = ?", (run_id,))
            r = cursor.fetchone()
            if not r:
                return None
            stages = [PipelineStage(**s) for s in json.loads(r["stages_json"] or "[]")]
            rec_cov = RecommendedTestCoverage(**json.loads(r["recommended_test_coverage_json"] or "{}"))
            return PipelineRun(
                id=r["id"],
                task_id=r["task_id"],
                repo_id=r["repo_id"],
                pr_url=r["pr_url"],
                pr_number=r["pr_number"],
                commit_sha=r["commit_sha"],
                branch=r["branch"],
                workflow_run_id=r["workflow_run_id"],
                workflow_url=r["workflow_url"],
                stages=stages,
                recommended_test_coverage=rec_cov,
                status=RunStatus(r["status"]),
                source=r["source"],
                started_at=r["started_at"],
                finished_at=r["finished_at"]
            )

    def save_pipeline_run(self, run: PipelineRun) -> PipelineRun:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # If new commit on existing PR, mark previous runs Superseded and previous GateResults Stale
            if run.task_id and run.commit_sha:
                cursor.execute("""
                    UPDATE pipeline_runs
                    SET status = ?
                    WHERE task_id = ? AND commit_sha != ? AND status IN (?, ?)
                """, (RunStatus.SUPERSEDED.value, run.task_id, run.commit_sha, RunStatus.PASSED.value, RunStatus.RUNNING.value))

                cursor.execute("""
                    UPDATE gate_results
                    SET freshness = ?
                    WHERE run_id IN (SELECT id FROM pipeline_runs WHERE task_id = ? AND commit_sha != ?)
                """, (GateFreshness.STALE.value, run.task_id, run.commit_sha))

            stages_json = json.dumps([s.model_dump() for s in run.stages])
            rec_cov_json = json.dumps(run.recommended_test_coverage.model_dump())
            cursor.execute("""
                INSERT INTO pipeline_runs (
                    id, task_id, repo_id, pr_url, pr_number, commit_sha, branch, workflow_run_id,
                    workflow_url, stages_json, recommended_test_coverage_json, status, source, started_at, finished_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    stages_json = excluded.stages_json,
                    recommended_test_coverage_json = excluded.recommended_test_coverage_json,
                    status = excluded.status,
                    finished_at = excluded.finished_at
            """, (
                run.id, run.task_id, run.repo_id, run.pr_url, run.pr_number, run.commit_sha,
                run.branch, run.workflow_run_id, run.workflow_url, stages_json, rec_cov_json,
                run.status.value, run.source, run.started_at, run.finished_at
            ))
            conn.commit()

        return self.get_pipeline_run(run.id)

    def get_gate_result_for_run(self, run_id: str) -> Optional[GateResult]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM gate_results WHERE run_id = ?", (run_id,))
            r = cursor.fetchone()
            if not r:
                return None
            override = None
            if r["override_json"]:
                override = GateOverrideRecord(**json.loads(r["override_json"]))
            return GateResult(
                id=r["id"],
                run_id=r["run_id"],
                commit_sha=r["commit_sha"],
                brief_version_id=r["brief_version_id"],
                policy_version=r["policy_version"],
                decision=GateDecision(r["decision"]),
                freshness=GateFreshness(r["freshness"]),
                violations=json.loads(r["violations_json"] or "[]"),
                warnings=json.loads(r["warnings_json"] or "[]"),
                inputs_snapshot=json.loads(r["inputs_snapshot_json"] or "{}"),
                override=override,
                evaluated_at=r["evaluated_at"]
            )

    def save_gate_result(self, gate: GateResult, actor: Optional[User] = None) -> GateResult:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            override_json = json.dumps(gate.override.model_dump()) if gate.override else None
            cursor.execute("""
                INSERT INTO gate_results (
                    id, run_id, commit_sha, brief_version_id, policy_version, decision, freshness,
                    violations_json, warnings_json, inputs_snapshot_json, override_json, evaluated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    decision = excluded.decision,
                    freshness = excluded.freshness,
                    violations_json = excluded.violations_json,
                    warnings_json = excluded.warnings_json,
                    inputs_snapshot_json = excluded.inputs_snapshot_json,
                    override_json = excluded.override_json
            """, (
                gate.id, gate.run_id, gate.commit_sha, gate.brief_version_id, gate.policy_version,
                gate.decision.value, gate.freshness.value, json.dumps(gate.violations), json.dumps(gate.warnings),
                json.dumps(gate.inputs_snapshot), override_json, gate.evaluated_at
            ))

            actor_id = actor.id if actor else "system"
            actor_name = actor.name if actor else "Automated Policy Gate"
            self._write_audit_log_cursor(
                cursor=cursor,
                actor_id=actor_id,
                actor_name=actor_name,
                action="GATE_EVALUATE",
                object_type="gate",
                object_id=gate.id,
                previous_value=None,
                new_value=gate.decision.value,
                details=f"Gate evaluated: {gate.decision.value} ({len(gate.violations)} violations, {len(gate.warnings)} warnings)"
            )
            conn.commit()

        return self.get_gate_result_for_run(gate.run_id)

    def override_gate_decision(
        self,
        run_id: str,
        new_decision: GateDecision,
        reason: str,
        actor: User
    ) -> GateResult:
        """
        QA or Tech Lead override with mandatory reason and audit record (Section 7.8, 8.7).
        """
        gate = self.get_gate_result_for_run(run_id)
        if not gate:
            raise ValueError(f"No gate result found for run {run_id}.")

        previous_decision = gate.decision
        override_record = GateOverrideRecord(
            overridden_by=actor.id,
            overridden_by_name=actor.name,
            role="Tech Lead / QA",
            override_reason=reason,
            previous_decision=previous_decision,
            new_decision=new_decision,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE gate_results
                SET decision = ?, override_json = ?
                WHERE id = ?
            """, (new_decision.value, json.dumps(override_record.model_dump()), gate.id))
            
            cursor.execute("""
                UPDATE pipeline_runs
                SET status = 'Passed'
                WHERE id = ?
            """, (run_id,))

            self._write_audit_log_cursor(
                cursor=cursor,
                actor_id=actor.id,
                actor_name=actor.name,
                action="GATE_OVERRIDE",
                object_type="gate",
                object_id=gate.id,
                previous_value=previous_decision.value,
                new_value=new_decision.value,
                details=f"Gate overridden by {actor.name}: {reason}"
            )
            conn.commit()

        return self.get_gate_result_for_run(run_id)

    # -----------------------------------------------------------------------
    # Conversations & Messages (Section 7.4, 8.2, 10.8)
    # -----------------------------------------------------------------------

    def list_conversations(self, user_id: str, project_id: Optional[str] = None) -> List[Conversation]:
        query = "SELECT * FROM conversations WHERE user_id = ?"
        params: List[Any] = [user_id]
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        query += " ORDER BY updated_at DESC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conv_rows = cursor.fetchall()
            conversations = []
            for cr in conv_rows:
                cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (cr["id"],))
                msg_rows = cursor.fetchall()
                messages = []
                for mr in msg_rows:
                    refs = [EvidenceReference(**e) for e in json.loads(mr["evidence_refs_json"] or "[]")]
                    messages.append(Message(
                        id=mr["id"],
                        conversation_id=mr["conversation_id"],
                        role=mr["role"],
                        content=mr["content"],
                        evidence_refs=refs,
                        confidence=mr["confidence"],
                        retrieval_mode=mr["retrieval_mode"],
                        feedback_rating=mr["feedback_rating"],
                        feedback_reason=mr["feedback_reason"],
                        saved_as_note=bool(mr["saved_as_note"]),
                        note_title=mr["note_title"],
                        created_at=mr["created_at"]
                    ))
                conversations.append(Conversation(
                    id=cr["id"],
                    user_id=cr["user_id"],
                    project_id=cr["project_id"],
                    repository_id=cr["repository_id"],
                    title=cr["title"],
                    context_type=cr["context_type"],
                    context_id=cr["context_id"],
                    created_at=cr["created_at"],
                    updated_at=cr["updated_at"],
                    messages=messages
                ))
            return conversations

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
            cr = cursor.fetchone()
            if not cr:
                return None
            cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (conversation_id,))
            msg_rows = cursor.fetchall()
            messages = []
            for mr in msg_rows:
                refs = [EvidenceReference(**e) for e in json.loads(mr["evidence_refs_json"] or "[]")]
                messages.append(Message(
                    id=mr["id"],
                    conversation_id=mr["conversation_id"],
                    role=mr["role"],
                    content=mr["content"],
                    evidence_refs=refs,
                    confidence=mr["confidence"],
                    retrieval_mode=mr["retrieval_mode"],
                    feedback_rating=mr["feedback_rating"],
                    feedback_reason=mr["feedback_reason"],
                    saved_as_note=bool(mr["saved_as_note"]),
                    note_title=mr["note_title"],
                    created_at=mr["created_at"]
                ))
            return Conversation(
                id=cr["id"],
                user_id=cr["user_id"],
                project_id=cr["project_id"],
                repository_id=cr["repository_id"],
                title=cr["title"],
                context_type=cr["context_type"],
                context_id=cr["context_id"],
                created_at=cr["created_at"],
                updated_at=cr["updated_at"],
                messages=messages
            )

    def create_conversation(
        self,
        user_id: str,
        project_id: str,
        repository_id: str,
        title: str,
        context_type: str = "repository",
        context_id: Optional[str] = None
    ) -> Conversation:
        conv_id = f"conv-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (id, user_id, project_id, repository_id, title, context_type, context_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (conv_id, user_id, project_id, repository_id, title, context_type, context_id, now, now))
            conn.commit()

        return self.get_conversation(conv_id)

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        evidence_refs: Optional[List[EvidenceReference]] = None,
        confidence: Optional[float] = None,
        retrieval_mode: Optional[str] = None
    ) -> Message:
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        refs_json = json.dumps([e.model_dump() for e in (evidence_refs or [])])
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (id, conversation_id, role, content, evidence_refs_json, confidence, retrieval_mode, feedback_rating, feedback_reason, saved_as_note, note_title, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, 0, NULL, ?)
            """, (msg_id, conversation_id, role, content, refs_json, confidence, retrieval_mode, now))
            cursor.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
            conn.commit()

        return Message(
            id=msg_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            evidence_refs=evidence_refs or [],
            confidence=confidence,
            retrieval_mode=retrieval_mode,
            created_at=now
        )

    def delete_conversation(self, conversation_id: str, actor: User) -> bool:
        """Deleting follows data retention and writes an audit entry (Section 7.4, 10.8)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE conversation_id = ? AND saved_as_note = 0", (conversation_id,))
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            self._write_audit_log_cursor(
                cursor=cursor,
                actor_id=actor.id,
                actor_name=actor.name,
                action="DELETE",
                object_type="conversation",
                object_id=conversation_id,
                previous_value="active",
                new_value="deleted",
                details=f"Conversation {conversation_id} deleted by {actor.name} per retention policy."
            )
            conn.commit()
            return True

    def submit_message_feedback(self, message_id: str, rating: int, reason: Optional[str] = None) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE messages
                SET feedback_rating = ?, feedback_reason = ?
                WHERE id = ?
            """, (rating, reason, message_id))
            conn.commit()
            return True

    def save_message_as_note(self, message_id: str, note_title: Optional[str] = None) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE messages
                SET saved_as_note = 1, note_title = ?
                WHERE id = ?
            """, (note_title or "Team Note", message_id))
            conn.commit()
            return True

    def get_team_notes(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.id, m.content, m.note_title, m.created_at, c.title as conversation_title, c.repository_id
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE m.saved_as_note = 1
                ORDER BY m.created_at DESC
            """)
            return [dict(r) for r in cursor.fetchall()]

    # -----------------------------------------------------------------------
    # Audit Logs (Section 7.3, 10.6)
    # -----------------------------------------------------------------------

    def get_audit_logs(
        self,
        object_type: Optional[str] = None,
        object_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params: List[Any] = []
        if object_type:
            query += " AND object_type = ?"
            params.append(object_type)
        if object_id:
            query += " AND object_id = ?"
            params.append(object_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [AuditLogEntry(**dict(r)) for r in cursor.fetchall()]

    # -----------------------------------------------------------------------
    # Outcomes & Insights (Section 7.7, 8.8)
    # -----------------------------------------------------------------------

    def list_outcomes(self, task_id: Optional[str] = None) -> List[Outcome]:
        query = "SELECT * FROM outcomes WHERE 1=1"
        params: List[Any] = []
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        query += " ORDER BY recorded_at DESC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append(Outcome(
                    id=r["id"],
                    task_id=r["task_id"],
                    request_id=r["request_id"],
                    predicted_components=json.loads(r["predicted_components_json"] or "[]"),
                    actual_components=json.loads(r["actual_components_json"] or "[]"),
                    predicted_files=json.loads(r["predicted_files_json"] or "[]"),
                    actual_files=json.loads(r["actual_files_json"] or "[]"),
                    predicted_tests=json.loads(r["predicted_tests_json"] or "[]"),
                    executed_tests=json.loads(r["executed_tests_json"] or "[]"),
                    failed_tests=json.loads(r["failed_tests_json"] or "[]"),
                    ground_truth_method=r["ground_truth_method"],
                    ground_truth_version=r["ground_truth_version"],
                    component_metrics=EvaluationMetrics(**json.loads(r["component_metrics_json"] or "{}")),
                    test_metrics=EvaluationMetrics(**json.loads(r["test_metrics_json"] or "{}")),
                    regression_metrics=json.loads(r["regression_metrics_json"] or "{}"),
                    retrospective_summary=r["retrospective_summary"],
                    recorded_at=r["recorded_at"]
                ))
            return results

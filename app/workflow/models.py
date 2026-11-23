"""
Core domain models and schemas for History-RAG Revision 2.2.
Implements Section 7 (Entities, Rules, State Machines).
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Roles & Personas
# ---------------------------------------------------------------------------

class GlobalRole(str, Enum):
    ADMIN = "Admin"
    MEMBER = "Member"


class ProjectRole(str, Enum):
    JUNIOR_DEV = "junior_developer"
    JUNIOR_DEVELOPER = "junior_developer"
    PRODUCT_OWNER = "product_owner"
    TECH_LEAD = "tech_lead"
    QA_ENGINEER = "qa_engineer"
    ENGINEERING_MANAGER = "engineering_manager"
    ADMIN = "admin"


# ---------------------------------------------------------------------------
# State Enums
# ---------------------------------------------------------------------------

class RequestStatus(str, Enum):
    DRAFT = "Draft"
    IN_BRIEF = "In Brief"
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"
    CANCELLED = "Cancelled"


class BriefStatus(str, Enum):
    DRAFT = "Draft"
    FINAL = "Final"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    OUTDATED = "Outdated"


class TaskStatus(str, Enum):
    TODO = "Todo"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    TESTING = "Testing"
    DONE = "Done"
    CANCELLED = "Cancelled"


class RunStatus(str, Enum):
    QUEUED = "Queued"
    RUNNING = "Running"
    PASSED = "Passed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"
    ERRORED = "Errored"
    SUPERSEDED = "Superseded"


class GateDecision(str, Enum):
    APPROVED = "Approved"
    WARNING = "Warning"
    BLOCKED = "Blocked"


class GateFreshness(str, Enum):
    CURRENT = "Current"
    STALE = "Stale"


class DecisionStatus(str, Enum):
    ACTIVE = "Active"
    SUPERSEDED = "Superseded"


class EvidenceStrength(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# ---------------------------------------------------------------------------
# Core Entities
# ---------------------------------------------------------------------------

class Organization(BaseModel):
    id: str
    name: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Project(BaseModel):
    id: str
    organization_id: str
    name: str
    description: Optional[str] = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RepositoryRecord(BaseModel):
    id: str
    name: str
    url: str
    provider: str = "github"
    default_branch: str = "main"
    indexed_commit_sha: Optional[str] = None
    remote_head_sha: Optional[str] = None
    indexed_at: Optional[str] = None
    index_status: str = "ready"  # ready, indexing, stale, error


class ProjectRepository(BaseModel):
    project_id: str
    repository_id: str


class User(BaseModel):
    id: str
    name: str
    email: str
    global_role: GlobalRole = GlobalRole.MEMBER
    avatar: Optional[str] = None
    title: Optional[str] = None


class ProjectMembership(BaseModel):
    id: str
    user_id: str
    project_id: str
    role: ProjectRole
    status: str = "Active"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Feature Request & Analysis
# ---------------------------------------------------------------------------

class FeatureRequest(BaseModel):
    id: str
    title: str
    description: str
    acceptance_criteria: List[str] = Field(default_factory=list)
    priority: str = "P1"  # P0, P1, P2, P3
    status: RequestStatus = RequestStatus.DRAFT
    requester_id: str
    requester_name: Optional[str] = None
    project_id: str
    repo_id: str
    target_component: Optional[str] = None
    external_issue_ref: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AnalysisJobStep(BaseModel):
    name: str
    status: str  # Waiting, Running, Complete, Failed
    message: Optional[str] = None


class AnalysisJob(BaseModel):
    id: str
    request_id: str
    status: str = "queued"  # queued, running, completed, failed
    steps: List[AnalysisJobStep] = Field(default_factory=list)
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: Optional[str] = None
    error: Optional[str] = None


class EvidenceReference(BaseModel):
    id: str
    owner_type: str  # brief, message, flag, task
    owner_id: str
    source_type: str  # commit, PR, issue, file, decision
    source_id: str
    similarity: float = 0.85
    excerpt: str = ""
    source_date: Optional[str] = None
    component: Optional[str] = None
    title: Optional[str] = None


class ImplementationOption(BaseModel):
    name: str
    description: str
    effort: str = "Medium"  # Low, Medium, High
    risk: str = "Low"  # Low, Medium, High
    components_touched: List[str] = Field(default_factory=list)
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    maintainability: Optional[str] = None
    reusability: Optional[str] = None
    main_risk: Optional[str] = None


class TaskProposal(BaseModel):
    title: str
    description: str
    component: str
    priority: str = "P1"
    order: int = 1
    depends_on: List[str] = Field(default_factory=list)
    estimated_complexity: str = "Medium"


class ReviewFlag(BaseModel):
    id: str
    category: str  # high_churn, regression_history, low_tests, security, weak_evidence, decision_conflict
    severity: str  # warning, critical, info
    message: str
    target: str  # component or file or decision ID
    evidence_ref: Optional[str] = None


class EvidenceStrengthBreakdown(BaseModel):
    component_identification: EvidenceStrength = EvidenceStrength.HIGH
    historical_similarity: EvidenceStrength = EvidenceStrength.MEDIUM
    dependency_relationships: EvidenceStrength = EvidenceStrength.HIGH
    test_recommendations: EvidenceStrength = EvidenceStrength.HIGH
    implementation_options: EvidenceStrength = EvidenceStrength.MEDIUM


class ReproducibilityMetadata(BaseModel):
    repository_commit_sha: str
    index_snapshot_id: str
    model_name: str
    model_version: str
    prompt_version: str
    scoring_version: str
    retrieval_version: str
    requirement_hash: str
    analysis_timestamp: str
    job_id: str


class BriefVersion(BaseModel):
    id: str
    request_id: str
    version: int = 1
    is_current: bool = True
    status: BriefStatus = BriefStatus.FINAL
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_by: str = "system"
    based_on_version: Optional[int] = None
    change_summary: Optional[str] = None
    
    # Requirement understanding
    restated_requirement: str = ""
    open_questions: List[str] = Field(default_factory=list)

    # Core Intelligence
    affected_components: List[Dict[str, Any]] = Field(default_factory=list)
    overall_impact_level: str = "MEDIUM"
    overall_confidence: float = 0.85
    evidence_strength: EvidenceStrengthBreakdown = Field(default_factory=EvidenceStrengthBreakdown)
    
    # Tradeoffs & Tasks
    options: List[ImplementationOption] = Field(default_factory=list)
    recommended_option: Optional[str] = None
    proposed_tasks: List[TaskProposal] = Field(default_factory=list)
    review_flags: List[ReviewFlag] = Field(default_factory=list)
    recommended_tests: List[Dict[str, Any]] = Field(default_factory=list)
    candidate_tests: List[Dict[str, Any]] = Field(default_factory=list)
    historical_precedents: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Reproducibility
    reproducibility: ReproducibilityMetadata
    stale_snapshot: bool = False
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def impact_analysis(self) -> Dict[str, Any]:
        return {
            "overall_impact": self.overall_impact_level,
            "components": self.affected_components,
            "confidence": self.overall_confidence
        }


# ---------------------------------------------------------------------------
# Decision Log
# ---------------------------------------------------------------------------

class Decision(BaseModel):
    id: str
    key: Optional[str] = None
    request_id: Optional[str] = None
    brief_version_id: Optional[str] = None
    title: str
    context: str
    options_considered: List[Dict[str, Any]] = Field(default_factory=list)
    chosen_option: str
    rationale: str
    tradeoffs_accepted: List[str] = Field(default_factory=list)
    decided_by: str
    decided_by_name: Optional[str] = None
    decided_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: DecisionStatus = DecisionStatus.ACTIVE
    superseded_by: Optional[str] = None
    component: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.key:
            self.key = self.id.upper()


# ---------------------------------------------------------------------------
# Tasks & Pre-PR
# ---------------------------------------------------------------------------

class TaskContextPack(BaseModel):
    task_description: str
    acceptance_criteria: List[str] = Field(default_factory=list)
    relevant_files: List[Dict[str, Any]] = Field(default_factory=list)
    historical_changes: List[Dict[str, Any]] = Field(default_factory=list)
    known_pitfalls: List[str] = Field(default_factory=list)
    recommended_tests: List[Dict[str, Any]] = Field(default_factory=list)
    related_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    suggested_reviewers: List[Dict[str, Any]] = Field(default_factory=list)


class Task(BaseModel):
    id: str
    task_key: str  # e.g. TASK-101
    request_id: str
    title: str
    description: str
    component: str
    priority: str = "P1"
    order: int = 1
    depends_on: List[str] = Field(default_factory=list)
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    reviewer_id: Optional[str] = None
    reviewer_name: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    branch: Optional[str] = None
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    context_pack: Optional[TaskContextPack] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PrePrCheckResult(BaseModel):
    task_id: str
    planned_components: List[str] = Field(default_factory=list)
    unplanned_components: List[str] = Field(default_factory=list)
    scope_drift_detected: bool = False
    modified_files: List[str] = Field(default_factory=list)
    high_risk_files: List[str] = Field(default_factory=list)
    recommended_tests_matched: List[str] = Field(default_factory=list)
    missing_recommended_tests: List[str] = Field(default_factory=list)
    suggested_reviewers: List[Dict[str, Any]] = Field(default_factory=list)
    check_passed: bool = True
    summary: str = ""


# ---------------------------------------------------------------------------
# CI/CD Pipelines & Policy Gate
# ---------------------------------------------------------------------------

class PipelineStage(BaseModel):
    name: str  # build, unit, regression, integration, deploy_test
    status: str  # Passed, Failed, Running, Pending, Skipped
    duration_seconds: float = 0.0
    failed_tests: List[str] = Field(default_factory=list)
    logs: Optional[str] = None


class RecommendedTestCoverage(BaseModel):
    total_recommended: int = 0
    executed: int = 0
    passed: int = 0
    failed: int = 0
    not_run: int = 0
    coverage_percentage: float = 100.0
    details: List[Dict[str, Any]] = Field(default_factory=list)


class PipelineRun(BaseModel):
    id: str
    task_id: Optional[str] = None
    repo_id: str
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    commit_sha: str
    branch: str = "main"
    workflow_run_id: str
    workflow_url: Optional[str] = None
    stages: List[PipelineStage] = Field(default_factory=list)
    recommended_test_coverage: RecommendedTestCoverage = Field(default_factory=RecommendedTestCoverage)
    status: RunStatus = RunStatus.RUNNING
    source: str = "live"  # live | simulated
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: Optional[str] = None


class GateOverrideRecord(BaseModel):
    overridden_by: str
    overridden_by_name: str
    role: str
    override_reason: str
    previous_decision: GateDecision
    new_decision: GateDecision
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GateResult(BaseModel):
    id: str
    run_id: str
    commit_sha: str
    brief_version_id: Optional[str] = None
    policy_version: str = "v2.2-enterprise"
    decision: GateDecision = GateDecision.APPROVED
    freshness: GateFreshness = GateFreshness.CURRENT
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    inputs_snapshot: Dict[str, Any] = Field(default_factory=dict)
    override: Optional[GateOverrideRecord] = None
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Outcomes & Evaluation Protocol (Section 7.7)
# ---------------------------------------------------------------------------

class EvaluationMetrics(BaseModel):
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None


class Outcome(BaseModel):
    id: str
    task_id: str
    request_id: str
    predicted_components: List[str] = Field(default_factory=list)
    actual_components: List[str] = Field(default_factory=list)
    predicted_files: List[str] = Field(default_factory=list)
    actual_files: List[str] = Field(default_factory=list)
    predicted_tests: List[str] = Field(default_factory=list)
    executed_tests: List[str] = Field(default_factory=list)
    failed_tests: List[str] = Field(default_factory=list)
    ground_truth_method: str = "merged_pr_file_diff_v1"
    ground_truth_version: str = "1.0"
    
    component_metrics: EvaluationMetrics = Field(default_factory=EvaluationMetrics)
    test_metrics: EvaluationMetrics = Field(default_factory=EvaluationMetrics)
    regression_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    retrospective_summary: str = ""
    recorded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Conversations & Notes
# ---------------------------------------------------------------------------

class Message(BaseModel):
    id: str
    conversation_id: str
    role: str  # user, assistant, system
    content: str
    evidence_refs: List[EvidenceReference] = Field(default_factory=list)
    confidence: Optional[float] = None
    retrieval_mode: Optional[str] = None
    feedback_rating: Optional[int] = None  # 1 (up) or -1 (down)
    feedback_reason: Optional[str] = None
    saved_as_note: bool = False
    note_title: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Conversation(BaseModel):
    id: str
    user_id: str
    project_id: str
    repository_id: str
    title: str
    context_type: str = "repository"  # repository, request, brief, task, failed_test, decision
    context_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    messages: List[Message] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Audit, Comments, Notifications, Integrations
# ---------------------------------------------------------------------------

class AuditLogEntry(BaseModel):
    id: str
    actor_id: str
    actor_name: str
    action: str  # CREATE, UPDATE, TRANSITION, APPROVE, REJECT, OVERRIDE, DELETE
    object_type: str  # request, brief, task, decision, gate, run, conversation
    object_id: str
    previous_value: Optional[str] = None
    new_value: Optional[str] = None
    details: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Comment(BaseModel):
    id: str
    parent_type: str  # request, brief, task, decision
    parent_id: str
    author_id: str
    author_name: str
    body: str
    mentions: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Notification(BaseModel):
    id: str
    user_id: str
    event: str
    message: str
    object_ref: Optional[str] = None
    read_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Integration(BaseModel):
    id: str
    project_id: str
    type: str  # GitHub, Jira, Slack
    config_ref: Optional[str] = None
    status: str = "active"  # active, inactive, error
    webhook_state: Dict[str, Any] = Field(default_factory=dict)

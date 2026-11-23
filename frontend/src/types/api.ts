/**
 * History-RAG Revision 2.2 TypeScript API Types
 * Full domain models for Engineering Memory, Workflow Lifecycle, RBAC,
 * Briefs, Tasks, Pre-PR Checks, Gates, Insights, and Cited Q&A.
 */

// ---------------------------------------------------------------------------
// 1. Roles & Auth
// ---------------------------------------------------------------------------

export type GlobalRole = 'Admin' | 'Member';

export type ProjectRole =
  | 'junior_developer'
  | 'product_owner'
  | 'tech_lead'
  | 'qa_engineer'
  | 'engineering_manager'
  | 'admin';

export interface User {
  id: string;
  name: string;
  email: string;
  global_role: GlobalRole;
  avatar?: string;
  title?: string;
}

export interface DemoPersona {
  id: string;
  name: string;
  role: ProjectRole;
  email: string;
  title: string;
  avatar: string;
  global_role: GlobalRole;
  description?: string;
}

export interface AuthProfileResponse {
  user: User;
  available_personas: DemoPersona[];
  mode: 'demo' | 'real';
}

// ---------------------------------------------------------------------------
// 2. Organization, Projects & Repositories
// ---------------------------------------------------------------------------

export interface Project {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface RepositoryRecord {
  id: string;
  name: string;
  url: string;
  provider: string;
  default_branch: string;
  indexed_commit_sha?: string;
  remote_head_sha?: string;
  indexed_at?: string;
  index_status: 'ready' | 'indexing' | 'error';
}

export interface ProjectMembership {
  id: string;
  user_id: string;
  project_id: string;
  role: ProjectRole;
  status: 'Active' | 'Invited' | 'Suspended';
  created_at: string;
  user?: User;
}

// ---------------------------------------------------------------------------
// 3. Cited Q&A and Evidence
// ---------------------------------------------------------------------------

export interface EvidenceReference {
  id: string;
  owner_type: 'message' | 'brief' | 'task' | 'gate';
  owner_id: string;
  source_type: 'commit' | 'issue' | 'pr' | 'test' | 'code';
  source_id: string;
  similarity: number;
  excerpt?: string;
  source_date?: string;
  component?: string;
  title?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  evidence_refs: EvidenceReference[];
  confidence?: number;
  retrieval_mode?: string;
  feedback_rating?: number;
  feedback_reason?: string;
  saved_as_note?: boolean;
  note_title?: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  project_id: string;
  repository_id: string;
  title: string;
  context_type: 'repository' | 'request' | 'file';
  context_id?: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface SendMessageResponse {
  user_message: Message;
  assistant_message: Message;
}

// ---------------------------------------------------------------------------
// 4. Feature Requests & AI Clarity Assistant
// ---------------------------------------------------------------------------

export type RequestStatus =
  | 'Draft'
  | 'In Brief'
  | 'Planned'
  | 'In Progress'
  | 'In Review'
  | 'Done'
  | 'Cancelled';

export interface FeatureRequest {
  id: string;
  title: string;
  description: string;
  acceptance_criteria: string[];
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  status: RequestStatus;
  requester_id: string;
  requester_name: string;
  project_id: string;
  repo_id: string;
  target_component?: string;
  external_issue_ref?: string;
  created_at: string;
  updated_at: string;
}

export interface ClarityCheckPayload {
  title: string;
  description: string;
  acceptance_criteria?: string[];
  project_id: string;
  repository_id: string;
}

export interface ClarityFlag {
  criterion_index: number;
  criterion: string;
  term: string;
  question: string;
}

export interface SuggestedCriterion {
  id: string;
  text: string;
  reason: string;
}

export interface SimilarPastWork {
  type: string;
  id: string;
  title: string;
  similarity: number;
  component?: string;
}

export interface ClarityCheckResult {
  clarity_score: number;
  is_ambiguous: boolean;
  flags: ClarityFlag[];
  suggested_criteria: SuggestedCriterion[];
  similar_past_work: SimilarPastWork[];
  duplicate_warning?: string | null;
}

export interface TimelineEvent {
  timestamp: string;
  action: string;
  actor_name: string;
  details?: string;
  previous_value?: string;
  new_value?: string;
}

// ---------------------------------------------------------------------------
// 5. Feature Briefs & Versioning
// ---------------------------------------------------------------------------

export type BriefStatus = 'Draft' | 'Final' | 'Approved' | 'Rejected' | 'Outdated';

export interface ImplementationOption {
  name: string;
  description: string;
  effort: 'Low' | 'Medium' | 'High' | string;
  risk: 'Low' | 'Medium' | 'High' | string;
  components_touched: string[];
  pros: string[];
  cons: string[];
  maintainability?: string;
  reusability?: string;
  main_risk?: string;
}

export interface TaskProposal {
  title: string;
  description: string;
  component: string;
  task_key?: string;
  suggested_assignee_role?: ProjectRole;
  dependencies?: string[];
}

export interface ReviewFlag {
  id: string;
  category: string;
  severity: 'warning' | 'critical' | 'info' | string;
  message: string;
  target: string;
  evidence_ref?: string;
}

export interface ReproducibilityMetadata {
  repository_commit_sha: string;
  index_snapshot_id: string;
  model_name: string;
  model_version: string;
  prompt_version: string;
  scoring_version: string;
  retrieval_version: string;
  requirement_hash: string;
  analysis_timestamp: string;
  job_id: string;
}

export interface EvidenceStrengthBreakdown {
  component_identification: 'High' | 'Medium' | 'Low';
  historical_precedent: 'High' | 'Medium' | 'Low';
  test_relevance: 'High' | 'Medium' | 'Low';
}

export interface AffectedComponent {
  component: string;
  score: number;
  impact_level?: 'LOW' | 'MEDIUM' | 'HIGH';
  reasons?: string[];
  breakdown?: {
    semantic_relevance?: number;
    dependency_evidence?: number;
    historical_cochange?: number;
    test_relationship?: number;
    graph_connectivity?: number;
  };
}

export interface RecommendedTest {
  test_file: string;
  test_name: string;
  relevance_score?: number;
  score?: number;
  component?: string;
  reasons?: string[];
  historical_failure_rate?: number;
}

export interface CandidateTest {
  test_name: string;
  target_component: string;
  target_function_or_scenario: string;
  test_code: string;
  rationale: string;
  validation_status: string;
  review_status: string;
  framework: string;
  test_type: string;
  ast_valid: boolean;
  created_at?: string;
}

export interface BriefVersion {
  id: string;
  request_id: string;
  version: number;
  is_current: boolean;
  status: BriefStatus;
  approved_by?: string;
  approved_at?: string;
  created_by: string;
  based_on_version?: number;
  change_summary?: string;
  restated_requirement: string;
  open_questions: string[];
  affected_components: AffectedComponent[];
  overall_impact_level: string;
  overall_confidence: number;
  evidence_strength: EvidenceStrengthBreakdown;
  options: ImplementationOption[];
  recommended_option?: string;
  proposed_tasks: TaskProposal[];
  review_flags: ReviewFlag[];
  recommended_tests: RecommendedTest[];
  candidate_tests: CandidateTest[];
  historical_precedents: any[];
  reproducibility: ReproducibilityMetadata;
  stale_snapshot: boolean;
  generated_at: string;
  markdown_content?: string;
  impact_analysis?: {
    overall_impact: string;
    components: AffectedComponent[];
    confidence: number;
  };
}

export interface BriefDiff {
  request_id: string;
  version_a: number;
  version_b: number;
  components_added: string[];
  components_removed: string[];
  options_added: string[];
  tests_added: string[];
  tasks_added: string[];
  summary: string;
}

// ---------------------------------------------------------------------------
// 6. Tasks & Context Packs
// ---------------------------------------------------------------------------

export type TaskStatus =
  | 'Todo'
  | 'In Progress'
  | 'In Review'
  | 'Testing'
  | 'Done'
  | 'Cancelled';

export interface Task {
  id: string;
  task_key: string;
  request_id: string;
  title: string;
  description: string;
  component: string;
  priority: string;
  task_order: number;
  depends_on: string[];
  assignee_id?: string;
  assignee_name?: string;
  reviewer_id?: string;
  reviewer_name?: string;
  status: TaskStatus;
  branch_name?: string;
  pr_url?: string;
  pr_number?: number;
  created_at: string;
  updated_at: string;
}

export interface TaskContextPack {
  task_description: string;
  acceptance_criteria: string[];
  relevant_files: Array<{ path: string; title?: string; similarity?: number }>;
  historical_changes: Array<{ sha: string; title: string; date?: string }>;
  known_pitfalls: string[];
  recommended_tests: Array<{ test_file: string; score: number; reasons: string[] }>;
  related_decisions: Array<{ id: string; title: string; chosen_option: string; rationale: string }>;
  suggested_reviewers: Array<{ id: string; name: string; title: string; avatar: string; prior_modifications_count: number }>;
}

export interface PrePRCheckResult {
  task_id: string;
  check_passed: boolean;
  planned_components: string[];
  unplanned_components: string[];
  scope_drift_detected: boolean;
  modified_files: string[];
  high_risk_files: string[];
  recommended_tests_matched: string[];
  missing_recommended_tests: string[];
  suggested_reviewers: Array<{ id: string; name: string; title: string; avatar: string }>;
  summary: string;
}

// ---------------------------------------------------------------------------
// 7. Architectural Decision Records (ADRs)
// ---------------------------------------------------------------------------

export type DecisionStatus = 'Active' | 'Superseded' | 'Deprecated';

export interface Decision {
  id: string;
  key?: string;
  request_id?: string;
  brief_version_id?: string;
  title: string;
  context: string;
  options_considered: Array<Record<string, any>>;
  chosen_option: string;
  rationale: string;
  tradeoffs_accepted: string[];
  decided_by: string;
  decided_by_name?: string;
  decided_at: string;
  status: DecisionStatus;
  superseded_by?: string;
  component?: string;
}

export interface CreateDecisionPayload {
  title: string;
  context: string;
  options_considered?: Array<Record<string, any>>;
  chosen_option?: string;
  rationale: string;
  tradeoffs_accepted?: string[];
  request_id?: string;
  brief_version_id?: string;
  component?: string;
  project_id?: string;
}

// ---------------------------------------------------------------------------
// 8. CI/CD Pipelines & Reproducible Gates
// ---------------------------------------------------------------------------

export type RunStatus =
  | 'Queued'
  | 'Running'
  | 'Passed'
  | 'Failed'
  | 'Cancelled'
  | 'Errored'
  | 'Superseded';

export type GateDecision = 'Approved' | 'Warning' | 'Blocked';
export type GateFreshness = 'Current' | 'Stale';

export interface PipelineStage {
  name: string;
  status: string;
  duration_s: number;
  logs?: string;
}

export interface RecommendedTestCoverage {
  recommended_count: number;
  executed_count: number;
  passed_count: number;
  missed_tests: string[];
  coverage_pct: number;
}

export interface PipelineRun {
  id: string;
  task_id?: string;
  repo_id: string;
  commit_sha: string;
  branch: string;
  status: RunStatus;
  gate_decision: GateDecision;
  stages: PipelineStage[];
  recommended_test_coverage: RecommendedTestCoverage;
  started_at: string;
  finished_at?: string;
}

export interface GateOverrideRecord {
  overridden_by: string;
  overridden_by_name: string;
  role: string;
  override_reason: string;
  previous_decision: string;
  new_decision: string;
  timestamp: string;
}

export interface GateResult {
  id?: string;
  run_id: string;
  commit_sha: string;
  brief_version_id?: string;
  engine_version?: string;
  policy_version?: string;
  decision: GateDecision;
  freshness: GateFreshness;
  blocking_reasons?: string[];
  violations?: string[];
  warnings?: string[];
  evaluation_details?: Record<string, any>;
  inputs_snapshot?: Record<string, any>;
  evaluator_role?: string;
  evaluated_at: string;
  override?: GateOverrideRecord;
  override_reason?: string;
  overridden_by?: string;
  overridden_at?: string;
}

// ---------------------------------------------------------------------------
// 9. Insights, Retrospectives & 4 Core Questions
// ---------------------------------------------------------------------------

export interface CoreQuestionAnswer {
  question: string;
  headline: string;
  metric: string;
  detail: string;
}

export interface InsightsDashboardResponse {
  has_sufficient_sample: boolean;
  sample_size: number;
  questions: {
    early_risk: CoreQuestionAnswer;
    testing_efficiency: CoreQuestionAnswer;
    effort_reduction: CoreQuestionAnswer;
    release_quality: CoreQuestionAnswer;
  };
  role_metrics: Record<string, Record<string, string>>;
  retrospectives: Array<{
    feature_id?: string;
    request_id?: string;
    task_id?: string;
    title?: string;
    completed_at?: string;
    planned_vs_actual_cycle_time?: string;
    component_accuracy_pct?: string;
    precision?: string;
    recall?: string;
    f1?: string;
    tests_run_vs_total?: string;
    regressions_caught?: number;
    escaped_bugs?: number;
    unplanned_components?: string[];
    [key: string]: any;
  }>;
}

// ---------------------------------------------------------------------------
// 10. Audit Log & System Health
// ---------------------------------------------------------------------------

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  actor_id: string;
  actor_name: string;
  action: string;
  object_type: string;
  object_id: string;
  previous_value?: string;
  new_value?: string;
  details?: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  timestamp: string;
  version: string;
  database: string;
  vector_store: string;
}

export interface RepositoryProfile {
  repository_id: string;
  name?: string;
  repository_url?: string;
  pinned_commit?: string;
  mode?: string;
  language?: string;
  test_framework?: string;
  git_history?: boolean;
  source_code?: boolean;
  issues?: boolean;
  prs?: boolean;
  tests?: boolean;
  python_ast?: boolean;
  import_analysis?: boolean;
  analysis_mode?: string;
  discovered_components?: string[];
  total_commits?: number;
  total_issues?: number;
  total_prs?: number;
  total_tests?: number;
  profile_summary?: string;
  capabilities?: {
    git_history?: boolean;
    source_code?: boolean;
    issues?: boolean;
    prs?: boolean;
    tests?: boolean;
    python_ast?: boolean;
    import_analysis?: boolean;
  };
  stats?: {
    commits?: number;
    files?: number;
    issues?: number;
    prs?: number;
    tests?: number;
    [key: string]: any;
  };
}

export interface RepositoryStatusResponse {
  repository_id: string;
  name: string;
  repository_url: string;
  pinned_commit?: string | null;
  profile: RepositoryProfile;
  stats: {
    repository_id?: string;
    counts_by_type?: {
      code?: number;
      commit?: number;
      issue?: number;
      pr?: number;
      test?: number;
      [key: string]: number | undefined;
    };
    total_documents?: number;
    components_count?: number;
    latest_event_time?: string;
    commits?: number;
    files?: number;
    issues?: number;
    prs?: number;
    tests?: number;
    [key: string]: any;
  };
  mode?: string;
  capabilities?: {
    git_history?: boolean;
    source_code?: boolean;
    issues?: boolean;
    prs?: boolean;
    tests?: boolean;
    python_ast?: boolean;
    import_analysis?: boolean;
  };
}

export interface RepositoryItem {
  repository_id: string;
  name: string;
  repository_url: string;
  language?: string;
  description?: string;
}

export interface RepositoryFileItem {
  path: string;
  name?: string;
  extension?: string;
  type?: string;
  size?: number;
  size_bytes?: number;
  last_modified?: string;
  churn_count?: number;
}

export interface RepositoryFilesResponse {
  repository_id: string;
  files: RepositoryFileItem[];
}

export interface RepositoryFileContentResponse {
  repository_id: string;
  file_path: string;
  content: string;
}

// ---------------------------------------------------------------------------
// 11. Legacy Change Analysis & Policy Gate Types
// ---------------------------------------------------------------------------

export interface HistoricalEvidence {
  source_type?: string;
  id: string;
  message?: string;
  title?: string;
  content?: string;
  commit_sha?: string;
  similarity: number;
  date?: string;
  component?: string;
  author?: string;
}

export type CandidateTestModel = CandidateTest;

export interface AnalyzeChangeResponse {
  proposed_change: string;
  affected_components: AffectedComponent[];
  impact_level: 'LOW' | 'MEDIUM' | 'HIGH';
  historical_evidence: HistoricalEvidence[];
  recommended_tests: RecommendedTest[];
  candidate_tests?: CandidateTest[];
  confidence: number;
  limitations: string;
  analysis_mode?: string;
  engine_mode?: string;
}

export interface GateEvaluationResponse {
  decision: 'APPROVED' | 'BLOCKED' | 'WARNING' | 'REVIEW_REQUIRED';
  risk_level?: 'LOW' | 'MEDIUM' | 'HIGH';
  impact_level?: 'LOW' | 'MEDIUM' | 'HIGH';
  confidence: number;
  gate_passed?: boolean;
  tests_passed?: boolean;
  blocking_reasons?: string[];
  warnings?: string[];
  violations?: string[];
  recommendations?: string[];
  summary?: string;
  timestamp?: string;
  evaluated_at?: string;
}

export interface WorkflowInstallResponse {
  status: string;
  repository: string;
  branch: string;
  workflow_path: string;
  commit_sha?: string;
  pull_request_url?: string;
  pull_request_number?: number;
  message: string;
  workflow_preview?: string;
}

export interface DeploymentRecord {
  deployment_id: string;
  image_tag: string;
  environment: string;
  status: string;
  deployed_at: string;
  is_known_good: boolean;
}

export interface DeploymentLedgerResponse {
  current_deployed_image: string;
  known_good_image: string;
  history: DeploymentRecord[];
}

export interface RollbackResponse {
  status: string;
  action: string;
  redeployed_image: string;
  rolled_back_from: string;
  environment: string;
  timestamp: string;
  health_status: string;
  message: string;
}

export interface ParsedPrometheusMetrics {
  analysesTotal: number;
  analysesByMode: { mode: string; count: number }[];
  analysesBySeverity: { severity: string; count: number }[];
  latencyP50: number;
  latencyP90: number;
  latencyP95: number;
  gateDecisions: { decision: string; count: number }[];
  rollbacksTotal: number;
}

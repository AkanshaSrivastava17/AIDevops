export interface AffectedComponent {
  component: string;
  score: number;
  reason?: string;
  reasons?: string[];
  impact_level?: 'LOW' | 'MEDIUM' | 'HIGH';
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
  relevance_score: number;
  score?: number;
  component?: string;
  reasons?: string[];
  historical_failure_rate?: number;
}

export interface HistoricalEvidence {
  source_type?: string; // 'commit' | 'issue' | 'pr'
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

export interface HealthResponse {
  status: string;
  service: string;
  timestamp: string;
  version: string;
  database: string;
  vector_store: string;
}

export interface RepositoryItem {
  repository_id: string;
  name: string;
  repository_url: string;
  language?: string;
  description?: string;
}

export interface RepositoryProfile {
  repository_id: string;
  language: string;
  test_framework: string;
  git_history: boolean;
  source_code: boolean;
  issues: boolean;
  prs: boolean;
  tests: boolean;
  python_ast: boolean;
  import_analysis: boolean;
  analysis_mode: string;
  discovered_components: string[];
  total_commits: number;
  total_issues: number;
  total_prs: number;
  total_tests: number;
  profile_summary: string;
}

export interface RepositoryStatusResponse {
  repository_id: string;
  name: string;
  repository_url: string;
  pinned_commit?: string | null;
  profile: RepositoryProfile;
  stats: {
    repository_id: string;
    counts_by_type: {
      code?: number;
      commit?: number;
      issue?: number;
      pr?: number;
      test?: number;
      [key: string]: number | undefined;
    };
    total_documents: number;
    components_count: number;
    latest_event_time?: string;
  };
  mode: string;
  capabilities: {
    git_history: boolean;
    source_code: boolean;
    issues: boolean;
    prs: boolean;
    tests: boolean;
    python_ast: boolean;
    import_analysis: boolean;
  };
}

export interface RepositoryFileItem {
  path: string;
  name: string;
  extension: string;
  size_bytes: number;
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

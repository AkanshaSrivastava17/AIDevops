import type {
  AnalyzeChangeResponse,
  GateEvaluationResponse,
  WorkflowInstallResponse,
  HealthResponse,
  RepositoryStatusResponse,
  DemoPersona,
  AuthProfileResponse,
  Project,
  ProjectMembership,
  FeatureRequest,
  ClarityCheckPayload,
  ClarityCheckResult,
  TimelineEvent,
  BriefVersion,
  BriefDiff,
  Task,
  TaskContextPack,
  PrePRCheckResult,
  Decision,
  CreateDecisionPayload,
  PipelineRun,
  GateResult,
  InsightsDashboardResponse,
  Conversation,
  SendMessageResponse,
  AuditLogEntry,
  DeploymentLedgerResponse,
  ParsedPrometheusMetrics,
} from '../types/api'

const API_BASE = '/api'

export class ApiError extends Error {
  status?: number
  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

let activePersonaId: string = 'user-techlead'

export function getActivePersonaId(): string {
  return activePersonaId
}

export function setActivePersonaId(id: string): void {
  activePersonaId = id
  try {
    localStorage.setItem('historyrag_active_persona', id)
  } catch {
    // ignore local storage error
  }
}

// Restore on startup
try {
  const saved = localStorage.getItem('historyrag_active_persona')
  if (saved) {
    activePersonaId = saved
  }
} catch {
  // ignore
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        Accept: 'application/json',
        'X-Demo-User-Id': activePersonaId,
        ...(options.headers || {}),
      },
    })

    if (!res.ok) {
      let errorMsg = `Server returned status ${res.status}`
      try {
        const text = await res.text()
        try {
          const errorData = JSON.parse(text)
          if (errorData.detail) {
            errorMsg = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail)
          } else if (errorData.message) {
            errorMsg = errorData.message
          }
        } catch {
          if (text) errorMsg = text.slice(0, 300)
        }
      } catch {
        // stream read fallback
      }
      throw new ApiError(errorMsg, res.status)
    }

    const contentType = res.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      return (await res.json()) as T
    }
    return (await res.text()) as unknown as T
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err
    const message = err instanceof Error ? err.message : 'Network request failed'
    throw new ApiError(`Unable to connect to History-RAG backend: ${message}`)
  }
}

// ---------------------------------------------------------------------------
// 1. Auth & Persona Switcher (Section 4 & 10.4)
// ---------------------------------------------------------------------------

export async function fetchAuthProfile(): Promise<AuthProfileResponse> {
  return request<AuthProfileResponse>('/auth/me')
}

export async function fetchPersonas(): Promise<DemoPersona[]> {
  return request<DemoPersona[]>('/auth/personas')
}

export async function switchPersona(userId: string): Promise<{ status: string; active_persona: any }> {
  setActivePersonaId(userId)
  return request<{ status: string; active_persona: any }>('/auth/switch-persona', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId }),
  })
}

// ---------------------------------------------------------------------------
// 2. Projects & Repositories
// ---------------------------------------------------------------------------

export async function fetchProjects(): Promise<Project[]> {
  return request<Project[]>('/projects')
}

export async function fetchProjectMembers(projectId: string): Promise<ProjectMembership[]> {
  return request<ProjectMembership[]>(`/projects/${encodeURIComponent(projectId)}/members`)
}

export async function fetchRepositories(): Promise<Array<{ repository_id: string; name: string; repository_url: string; language: string; description: string }>> {
  return request('/repositories')
}

export async function fetchRepositoryStatus(repositoryId: string = 'netbox'): Promise<RepositoryStatusResponse> {
  return request<RepositoryStatusResponse>(`/repository-status?repository_id=${encodeURIComponent(repositoryId)}`)
}

export async function fetchRepositoryFiles(repositoryId: string = 'netbox'): Promise<{ repository_id: string; files: any[] }> {
  return request(`/repository-files?repository_id=${encodeURIComponent(repositoryId)}`)
}

export async function fetchRepositoryFileContent(repositoryId: string = 'netbox', filePath: string = ''): Promise<{ repository_id: string; file_path: string; content: string }> {
  return request(`/repository-file-content?repository_id=${encodeURIComponent(repositoryId)}&file_path=${encodeURIComponent(filePath)}`)
}

// ---------------------------------------------------------------------------
// 3. Cited Q&A Conversations (Section 7.4 & 8.2)
// ---------------------------------------------------------------------------

export async function fetchConversations(projectId?: string): Promise<Conversation[]> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''
  return request<Conversation[]>(`/conversations${query}`)
}

export async function createConversation(params: {
  title: string
  project_id?: string
  repository_id?: string
  context_type?: string
  context_id?: string
}): Promise<Conversation> {
  return request<Conversation>('/conversations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: params.title,
      project_id: params.project_id || 'proj-platform-core',
      repository_id: params.repository_id || 'netbox',
      context_type: params.context_type || 'repository',
      context_id: params.context_id,
    }),
  })
}

export async function fetchConversation(convId: string): Promise<Conversation> {
  return request<Conversation>(`/conversations/${encodeURIComponent(convId)}`)
}

export async function deleteConversation(convId: string): Promise<{ status: string; deleted: boolean }> {
  return request<{ status: string; deleted: boolean }>(`/conversations/${encodeURIComponent(convId)}`, {
    method: 'DELETE',
  })
}

export async function sendConversationMessage(
  convId: string,
  content: string,
  systemMode: string = 'History-RAG'
): Promise<SendMessageResponse> {
  return request<SendMessageResponse>(`/conversations/${encodeURIComponent(convId)}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, system_mode: systemMode }),
  })
}

export async function submitMessageFeedback(messageId: string, rating: number, reason?: string): Promise<any> {
  return request(`/messages/${encodeURIComponent(messageId)}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rating, reason }),
  })
}

export async function saveMessageNote(messageId: string, noteTitle?: string): Promise<any> {
  return request(`/messages/${encodeURIComponent(messageId)}/save-note`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ note_title: noteTitle }),
  })
}

export async function fetchKnowledgeMap(repositoryId: string = 'netbox'): Promise<any> {
  return request(`/knowledge-map?repository_id=${encodeURIComponent(repositoryId)}`)
}

// ---------------------------------------------------------------------------
// 4. Feature Requests & AI Clarity Assistant (Section 7.1 & 8.3)
// ---------------------------------------------------------------------------

export async function fetchRequests(projectId?: string): Promise<FeatureRequest[]> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''
  return request<FeatureRequest[]>(`/requests${query}`)
}

export async function fetchRequest(reqId: string): Promise<FeatureRequest> {
  return request<FeatureRequest>(`/requests/${encodeURIComponent(reqId)}`)
}

export async function createRequest(payload: {
  title: string
  description: string
  acceptance_criteria: string[]
  priority?: string
  project_id?: string
  repository_id?: string
  target_component?: string
}): Promise<FeatureRequest> {
  return request<FeatureRequest>('/requests', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: payload.title,
      description: payload.description,
      acceptance_criteria: payload.acceptance_criteria,
      priority: payload.priority || 'P1',
      project_id: payload.project_id || 'proj-platform-core',
      repository_id: payload.repository_id || 'netbox',
      target_component: payload.target_component,
    }),
  })
}

export async function updateRequestStatus(
  reqId: string,
  status: string,
  reason?: string
): Promise<FeatureRequest> {
  return request<FeatureRequest>(`/requests/${encodeURIComponent(reqId)}/status`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, reason }),
  })
}

export async function checkRequestClarity(payload: ClarityCheckPayload): Promise<ClarityCheckResult> {
  return request<ClarityCheckResult>('/requests/clarity-check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function fetchRequestTimeline(reqId: string): Promise<TimelineEvent[]> {
  return request<TimelineEvent[]>(`/requests/${encodeURIComponent(reqId)}/timeline`)
}

// ---------------------------------------------------------------------------
// 5. Feature Briefs (Section 7.2 & 8.4)
// ---------------------------------------------------------------------------

export async function generateBrief(reqId: string): Promise<BriefVersion> {
  return request<BriefVersion>(`/requests/${encodeURIComponent(reqId)}/brief`, {
    method: 'POST',
  })
}

export async function fetchCurrentBrief(reqId: string): Promise<BriefVersion> {
  return request<BriefVersion>(`/requests/${encodeURIComponent(reqId)}/brief`)
}

export async function fetchBriefVersions(reqId: string): Promise<BriefVersion[]> {
  return request<BriefVersion[]>(`/briefs/${encodeURIComponent(reqId)}/versions`)
}

export async function fetchBriefDiff(reqId: string, versionA: number, versionB: number): Promise<BriefDiff> {
  return request<BriefDiff>(`/briefs/${encodeURIComponent(reqId)}/versions/diff?version_a=${versionA}&version_b=${versionB}`)
}

export async function approveBrief(briefId: string): Promise<BriefVersion> {
  return request<BriefVersion>(`/briefs/${encodeURIComponent(briefId)}/approve`, {
    method: 'POST',
  })
}

export async function exportBriefMarkdown(reqId: string): Promise<string> {
  return request<string>(`/requests/${encodeURIComponent(reqId)}/brief/export`)
}

// ---------------------------------------------------------------------------
// 6. Tasks & Context Packs (Section 7.5 & 8.5)
// ---------------------------------------------------------------------------

export async function fetchTasks(params?: {
  requestId?: string
  assigneeId?: string
  status?: string
}): Promise<Task[]> {
  const searchParams = new URLSearchParams()
  if (params?.requestId) searchParams.append('request_id', params.requestId)
  if (params?.assigneeId) searchParams.append('assignee_id', params.assigneeId)
  if (params?.status) searchParams.append('status', params.status)
  const qs = searchParams.toString() ? `?${searchParams.toString()}` : ''
  return request<Task[]>(`/tasks${qs}`)
}

export async function fetchTask(taskId: string): Promise<Task> {
  return request<Task>(`/tasks/${encodeURIComponent(taskId)}`)
}

export async function createTasksFromBrief(
  reqId: string,
  briefId: string,
  tasks?: Array<{ title: string; component: string; description: string }>
): Promise<Task[]> {
  return request<Task[]>(`/requests/${encodeURIComponent(reqId)}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ brief_id: briefId, tasks }),
  })
}

export async function updateTaskStatus(
  taskId: string,
  status: string,
  reason?: string
): Promise<Task> {
  return request<Task>(`/tasks/${encodeURIComponent(taskId)}/status`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, reason }),
  })
}

export async function fetchTaskContextPack(taskId: string): Promise<TaskContextPack> {
  return request<TaskContextPack>(`/tasks/${encodeURIComponent(taskId)}/context-pack`)
}

export async function runPrePrCheck(
  taskId: string,
  diffText: string,
  branch?: string
): Promise<PrePRCheckResult> {
  return request<PrePRCheckResult>(`/tasks/${encodeURIComponent(taskId)}/pre-pr-check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ diff_text: diffText, branch }),
  })
}

export async function fetchSuggestedReviewers(taskId: string): Promise<any[]> {
  return request(`/tasks/${encodeURIComponent(taskId)}/suggest-reviewers`)
}

// ---------------------------------------------------------------------------
// 7. Architectural Decisions (Section 7.3 & 8.6)
// ---------------------------------------------------------------------------

export async function fetchDecisions(params?: {
  requestId?: string
  component?: string
  status?: string
  search?: string
  projectId?: string
}): Promise<Decision[]> {
  const searchParams = new URLSearchParams()
  if (params?.requestId) searchParams.append('request_id', params.requestId)
  if (params?.component) searchParams.append('component', params.component)
  if (params?.status) searchParams.append('status', params.status)
  if (params?.search) searchParams.append('search', params.search)
  if (params?.projectId) searchParams.append('project_id', params.projectId)
  const qs = searchParams.toString() ? `?${searchParams.toString()}` : ''
  return request<Decision[]>(`/decisions${qs}`)
}

export async function createDecision(payload: CreateDecisionPayload): Promise<Decision> {
  return request<Decision>('/decisions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function supersedeDecision(
  decId: string,
  payload: { new_decision_id?: string; new_decision_payload?: CreateDecisionPayload; reason: string }
): Promise<any> {
  return request(`/decisions/${encodeURIComponent(decId)}/supersede`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

// ---------------------------------------------------------------------------
// 8. CI/CD Pipelines & Gates (Section 7.6 & 8.7)
// ---------------------------------------------------------------------------

export async function fetchPipelines(params?: { taskId?: string; repoId?: string }): Promise<PipelineRun[]> {
  const searchParams = new URLSearchParams()
  if (params?.taskId) searchParams.append('task_id', params.taskId)
  if (params?.repoId) searchParams.append('repo_id', params.repoId)
  const qs = searchParams.toString() ? `?${searchParams.toString()}` : ''
  return request<PipelineRun[]>(`/pipelines${qs}`)
}

export async function fetchPipelineRun(runId: string): Promise<PipelineRun> {
  return request<PipelineRun>(`/pipelines/${encodeURIComponent(runId)}`)
}

export async function fetchPipelineGate(runId: string): Promise<GateResult> {
  return request<GateResult>(`/pipelines/${encodeURIComponent(runId)}/gate`)
}

export async function evaluatePipelineGate(runId: string): Promise<GateResult> {
  return request<GateResult>(`/pipelines/${encodeURIComponent(runId)}/gate`, {
    method: 'POST',
  })
}

export async function overridePipelineGate(
  runId: string,
  reason: string,
  newDecision: string = 'Approved'
): Promise<GateResult> {
  return request<GateResult>(`/pipelines/${encodeURIComponent(runId)}/override`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason, new_decision: newDecision }),
  })
}

export async function triggerSimulatedRun(payload: {
  repo_id: string
  branch?: string
  commit_sha?: string
  task_id?: string
  fail_high_impact_test?: boolean
  low_confidence?: boolean
  qa_health_failure?: boolean
}): Promise<PipelineRun> {
  return request<PipelineRun>('/pipelines/simulate-run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

// ---------------------------------------------------------------------------
// 9. Insights Dashboard & Retrospectives (Section 7.7 & 8.8)
// ---------------------------------------------------------------------------

export async function fetchInsights(projectId: string = 'proj-platform-core'): Promise<InsightsDashboardResponse> {
  return request<InsightsDashboardResponse>(`/insights?project_id=${encodeURIComponent(projectId)}`)
}

// ---------------------------------------------------------------------------
// 10. Audit Logs & System Health
// ---------------------------------------------------------------------------

export async function fetchAuditLogs(params?: {
  objectId?: string
  objectType?: string
  actorId?: string
}): Promise<AuditLogEntry[]> {
  const searchParams = new URLSearchParams()
  if (params?.objectId) searchParams.append('object_id', params.objectId)
  if (params?.objectType) searchParams.append('object_type', params.objectType)
  if (params?.actorId) searchParams.append('actor_id', params.actorId)
  const qs = searchParams.toString() ? `?${searchParams.toString()}` : ''
  return request<AuditLogEntry[]>(`/audit${qs}`)
}

export async function fetchFileHistory(repositoryId: string, filePath: string): Promise<any> {
  return request(`/repository-file-history?repository_id=${encodeURIComponent(repositoryId)}&file_path=${encodeURIComponent(filePath)}`)
}

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

// ---------------------------------------------------------------------------
// 11. Legacy / Core Direct Analysis Methods
// ---------------------------------------------------------------------------

export async function analyzeChange(payload: {
  repository_id: string
  proposed_change: string
  system_mode?: string
  top_k_tests?: number
  generate_candidate_tests?: boolean
}): Promise<AnalyzeChangeResponse> {
  return request<AnalyzeChangeResponse>('/analyze-change', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function evaluateGate(payload: any): Promise<GateEvaluationResponse> {
  return request<GateEvaluationResponse>('/evaluate-gate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function triggerRollback(payload: any): Promise<any> {
  return request('/rollback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function installWorkflow(payload: any): Promise<WorkflowInstallResponse> {
  return request<WorkflowInstallResponse>('/ci/install', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function uploadRepositoryZip(
  file: File,
  repositoryId?: string
): Promise<{ status: string; repository_id: string; name: string; target_directory: string; profile: unknown; stats: unknown }> {
  const formData = new FormData()
  formData.append('file', file)
  if (repositoryId) {
    formData.append('repository_id', repositoryId)
  }
  const url = `${API_BASE}/repositories/upload`
  const res = await fetch(url, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    throw new ApiError(`Upload failed with status ${res.status}`, res.status)
  }
  return res.json()
}

export async function cloneRepository(
  payloadOrUrl: string | { repository_url: string; branch?: string; repository_id?: string },
  repositoryId?: string
): Promise<{ status: string; repository_id: string; name: string; target_directory: string; profile: unknown; stats: unknown }> {
  const payload =
    typeof payloadOrUrl === 'string'
      ? { repository_url: payloadOrUrl, repository_id: repositoryId }
      : payloadOrUrl
  return request('/repositories/clone', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function indexCustomRepository(repositoryId: string): Promise<any> {
  return request(`/repositories/${encodeURIComponent(repositoryId)}/index`, {
    method: 'POST',
  })
}

export async function fetchDeployments(): Promise<DeploymentLedgerResponse> {
  return request<DeploymentLedgerResponse>('/devops/deployments')
}

export async function fetchRawMetrics(): Promise<string> {
  return request<string>('/metrics')
}
export const fetchMetrics = fetchRawMetrics

export function parsePrometheusMetrics(rawText: string): ParsedPrometheusMetrics {
  let analysesTotal = 0
  const analysesByModeMap: Record<string, number> = {}
  const analysesBySeverityMap: Record<string, number> = {}
  let latencyP50 = 0.045
  let latencyP90 = 0.082
  let latencyP95 = 0.115
  const gateDecisionsMap: Record<string, number> = {}
  let rollbacksTotal = 0

  const lines = rawText.split('\n')
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue

    if (trimmed.startsWith('historyrag_change_analyses_total')) {
      const match = trimmed.match(/mode="([^"]+)",severity="([^"]+)"\}\s+([0-9.]+)/)
      if (match) {
        const mode = match[1]
        const severity = match[2]
        const val = parseFloat(match[3]) || 0
        analysesTotal += val
        analysesByModeMap[mode] = (analysesByModeMap[mode] || 0) + val
        analysesBySeverityMap[severity] = (analysesBySeverityMap[severity] || 0) + val
      }
    }

    if (trimmed.startsWith('historyrag_evidence_retrieval_latency_seconds')) {
      if (trimmed.includes('quantile="0.5"')) {
        const val = parseFloat(trimmed.split(/\s+/).pop() || '0')
        if (val) latencyP50 = val
      } else if (trimmed.includes('quantile="0.9"')) {
        const val = parseFloat(trimmed.split(/\s+/).pop() || '0')
        if (val) latencyP90 = val
      } else if (trimmed.includes('quantile="0.95"')) {
        const val = parseFloat(trimmed.split(/\s+/).pop() || '0')
        if (val) latencyP95 = val
      }
    }

    if (trimmed.startsWith('historyrag_cicd_gate_decisions_total')) {
      const match = trimmed.match(/decision="([^"]+)"\}\s+([0-9.]+)/)
      if (match) {
        const decision = match[1]
        const val = parseFloat(match[2]) || 0
        gateDecisionsMap[decision] = (gateDecisionsMap[decision] || 0) + val
      }
    }

    if (trimmed.startsWith('historyrag_rollbacks_total')) {
      const val = parseFloat(trimmed.split(/\s+/).pop() || '0')
      if (!isNaN(val)) rollbacksTotal += val
    }
  }

  return {
    analysesTotal,
    analysesByMode: Object.entries(analysesByModeMap).map(([mode, count]) => ({ mode, count })),
    analysesBySeverity: Object.entries(analysesBySeverityMap).map(([severity, count]) => ({ severity, count })),
    latencyP50: Math.round(latencyP50 * 1000),
    latencyP90: Math.round(latencyP90 * 1000),
    latencyP95: Math.round(latencyP95 * 1000),
    gateDecisions: Object.entries(gateDecisionsMap).map(([decision, count]) => ({ decision, count })),
    rollbacksTotal,
  }
}

export async function fetchPrometheusMetrics(): Promise<string> {
  return request<string>('/metrics')
}

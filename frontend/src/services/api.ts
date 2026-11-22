import type {
  AnalyzeChangeResponse,
  GateEvaluationResponse,
  WorkflowInstallResponse,
  HealthResponse,
  RepositoryItem,
  RepositoryStatusResponse,
  RepositoryFileItem,
  DeploymentLedgerResponse,
  RollbackResponse,
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

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  let url = `${API_BASE}${endpoint}`
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        Accept: 'application/json',
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

    // Check if plain text requested (e.g. metrics)
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

// 1. Health
export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

// 2. Repositories
export async function fetchRepositories(): Promise<RepositoryItem[]> {
  return request<RepositoryItem[]>('/repositories')
}

// 3. Repository Status & Stats
export async function fetchRepositoryStatus(repositoryId: string): Promise<RepositoryStatusResponse> {
  return request<RepositoryStatusResponse>(`/repository-status?repository_id=${encodeURIComponent(repositoryId)}`)
}

// 4. Upload Repository ZIP
export async function uploadRepositoryZip(
  file: File,
  repositoryId?: string
): Promise<{ status: string; repository_id: string; name: string; target_directory: string; profile: unknown; stats: unknown }> {
  const formData = new FormData()
  formData.append('file', file)
  if (repositoryId) {
    formData.append('repository_id', repositoryId)
  }

  let url = `${API_BASE}/upload-repository`
  const res = await fetch(url, {
    method: 'POST',
    body: formData,
  })

  if (!res.ok) {
    let errorMsg = `Upload failed with status ${res.status}`
    try {
      const text = await res.text()
      try {
        const errorData = JSON.parse(text)
        if (errorData.detail) errorMsg = errorData.detail
      } catch {
        if (text) errorMsg = text.slice(0, 300)
      }
    } catch {
      // stream read fallback
    }
    throw new ApiError(errorMsg, res.status)
  }

  return await res.json()
}

// 5. Clone Repository
export async function cloneRepository(
  repositoryUrl: string,
  repositoryId?: string
): Promise<{ status: string; total_documents_indexed: number; profile: unknown }> {
  return request<{ status: string; total_documents_indexed: number; profile: unknown }>('/index', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repository_url: repositoryUrl,
      repository_id: repositoryId,
      force_refresh: true,
    }),
  })
}

// 6. Repository Files
export async function fetchRepositoryFiles(
  repositoryId: string
): Promise<{ repository_id: string; count: number; files: RepositoryFileItem[] }> {
  return request<{ repository_id: string; count: number; files: RepositoryFileItem[] }>(
    `/repository-files?repository_id=${encodeURIComponent(repositoryId)}`
  )
}

// 7. Repository File Content
export async function fetchRepositoryFileContent(
  repositoryId: string,
  filePath: string
): Promise<{ repository_id: string; file_path: string; content: string }> {
  return request<{ repository_id: string; file_path: string; content: string }>(
    `/repository-file-content?repository_id=${encodeURIComponent(repositoryId)}&file_path=${encodeURIComponent(filePath)}`
  )
}

// 8. Analyze Change
export async function analyzeChange(payload: {
  repository_id: string
  proposed_change: string
  system_mode: string
  top_k_tests?: number
  generate_candidate_tests?: boolean
}): Promise<AnalyzeChangeResponse> {
  return request<AnalyzeChangeResponse>('/analyze-change', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

// 9. Evaluate Gate
export async function evaluateGate(payload: {
  change_analysis: Record<string, unknown>
  test_results: Record<string, unknown>
  qa_health_status?: Record<string, unknown>
  block_on_high_impact?: boolean
  min_confidence?: number
}): Promise<GateEvaluationResponse> {
  return request<GateEvaluationResponse>('/evaluate-gate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

// 10. Deployments Ledger
export async function fetchDeployments(): Promise<DeploymentLedgerResponse> {
  return request<DeploymentLedgerResponse>('/devops/deployments')
}

// 11. Rollback
export async function triggerRollback(payload: {
  failed_image?: string
  reason?: string
  environment?: string
}): Promise<RollbackResponse> {
  return request<RollbackResponse>('/devops/rollback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      failed_image: payload.failed_image || 'historyrag:candidate',
      reason: payload.reason || 'Manual Rollback Triggered from UI',
      environment: payload.environment || 'qa',
    }),
  })
}

// 12. 1-Click CI/CD Workflow Install
export async function installWorkflow(payload: {
  repository_url_or_slug: string
  github_token?: string
  branch_name: string
  commit_to_main?: boolean
  dry_run?: boolean
}): Promise<WorkflowInstallResponse> {
  return request<WorkflowInstallResponse>('/devops/install-workflow', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

// 13. Prometheus Metrics Stream
export async function fetchRawMetrics(): Promise<string> {
  return request<string>('/metrics')
}
export const fetchMetrics = fetchRawMetrics

// Helper: Parse Prometheus OpenMetrics stream
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

    // historyrag_change_analyses_total{mode="...",severity="..."} 42
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

    // historyrag_evidence_retrieval_latency_seconds{quantile="0.95"} 0.115
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

    // historyrag_cicd_gate_decisions_total{decision="..."} 51
    if (trimmed.startsWith('historyrag_cicd_gate_decisions_total')) {
      const match = trimmed.match(/decision="([^"]+)"\}\s+([0-9.]+)/)
      if (match) {
        const decision = match[1]
        const val = parseFloat(match[2]) || 0
        gateDecisionsMap[decision] = (gateDecisionsMap[decision] || 0) + val
      }
    }

    // historyrag_rollbacks_total{environment="..."} 0
    if (trimmed.startsWith('historyrag_rollbacks_total')) {
      const val = parseFloat(trimmed.split(/\s+/).pop() || '0')
      if (!isNaN(val)) rollbacksTotal += val
    }
  }

  return {
    analysesTotal,
    analysesByMode: Object.entries(analysesByModeMap).map(([mode, count]) => ({ mode, count })),
    analysesBySeverity: Object.entries(analysesBySeverityMap).map(([severity, count]) => ({ severity, count })),
    latencyP50: Math.round(latencyP50 * 1000), // ms
    latencyP90: Math.round(latencyP90 * 1000), // ms
    latencyP95: Math.round(latencyP95 * 1000), // ms
    gateDecisions: Object.entries(gateDecisionsMap).map(([decision, count]) => ({ decision, count })),
    rollbacksTotal,
  }
}

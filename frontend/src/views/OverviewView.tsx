import React, { useEffect, useState } from 'react'
import {
  FolderGit2,
  Search,
  GitPullRequest,
  Code2,
  FileText,
  GitCommit,
  Layers,
  ArrowRight,
  Shield,
  Activity,
} from 'lucide-react'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { fetchRepositoryStatus, fetchDeployments } from '../services/api'
import type { RepositoryItem, RepositoryStatusResponse, DeploymentRecord } from '../types/api'
import type { ViewId } from '../components/layout/Sidebar'

interface OverviewViewProps {
  repositories: RepositoryItem[]
  activeRepo: RepositoryItem | null
  onNavigate: (view: ViewId) => void
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  repositories,
  activeRepo,
  onNavigate,
}) => {
  const [status, setStatus] = useState<RepositoryStatusResponse | null>(null)
  const [deployments, setDeployments] = useState<DeploymentRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!activeRepo) return
    const loadData = async () => {
      setLoading(true)
      setError(null)
      try {
        const [repoStatus, depLedger] = await Promise.all([
          fetchRepositoryStatus(activeRepo.repository_id),
          fetchDeployments().catch(() => ({ history: [] as DeploymentRecord[], current_deployed_image: '', known_good_image: '' })),
        ])
        setStatus(repoStatus)
        setDeployments(depLedger.history || [])
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load repository status')
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [activeRepo])

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Welcome Header */}
      <div className="border-b border-slate-200/80 pb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Welcome to History-RAG
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Understand your codebase, predict change impact, and make safer software releases.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            onClick={() => onNavigate('analysis')}
            icon={<Search className="w-3.5 h-3.5" />}
          >
            Analyse a Code Change
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => onNavigate('repositories')}
            icon={<FolderGit2 className="w-3.5 h-3.5" />}
          >
            Manage Repositories
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-medium">Configured Repositories</span>
              <FolderGit2 className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2 font-mono">
              {repositories.length}
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">Active across platform</span>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-medium">Total Documents Indexed</span>
              <FileText className="w-4 h-4 text-indigo-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2 font-mono">
              {loading ? '...' : status?.stats?.total_documents ?? 0}
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">
              In SQLite + ChromaDB
            </span>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-medium">Components Discovered</span>
              <Layers className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2 font-mono">
              {loading ? '...' : status?.profile?.discovered_components?.length ?? 0}
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">
              Architecture modules
            </span>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-medium">Historical Commits</span>
              <GitCommit className="w-4 h-4 text-amber-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2 font-mono">
              {loading ? '...' : status?.profile?.total_commits ?? status?.stats?.counts_by_type?.commit ?? 0}
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">
              Grounded corpus
            </span>
          </CardContent>
        </Card>
      </div>

      {/* Active Repository Card & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Active Repo Detailed Card */}
        <div className="lg:col-span-7">
          <Card className="h-full flex flex-col justify-between">
            <CardHeader
              title={
                <div className="flex items-center gap-2">
                  <span>Active Repository Details</span>
                  <Badge variant="brand" size="sm">
                    {status?.profile?.language || 'Polyglot'}
                  </Badge>
                </div>
              }
              subtitle={activeRepo?.repository_url || 'Local codebase'}
              action={
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onNavigate('repositories')}
                >
                  Switch
                </Button>
              }
            />
            <CardContent className="space-y-4">
              <div>
                <h4 className="text-base font-bold text-slate-900">{activeRepo?.name}</h4>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  {status?.profile?.profile_summary || activeRepo?.description || 'Repository configured for History-RAG.'}
                </p>
              </div>

              {/* Capabilities checklist */}
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 text-xs">
                <div className="flex items-center gap-2 text-slate-600">
                  <span className={`w-1.5 h-1.5 rounded-full ${status?.capabilities?.python_ast ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                  <span>Tree-Sitter AST: <strong>{status?.capabilities?.python_ast ? 'Active' : 'Basic'}</strong></span>
                </div>
                <div className="flex items-center gap-2 text-slate-600">
                  <span className={`w-1.5 h-1.5 rounded-full ${status?.capabilities?.git_history ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                  <span>Git History: <strong>{status?.capabilities?.git_history ? 'Indexed' : 'None'}</strong></span>
                </div>
                <div className="flex items-center gap-2 text-slate-600">
                  <span className={`w-1.5 h-1.5 rounded-full ${status?.capabilities?.tests ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                  <span>Regression Tests: <strong>{status?.capabilities?.tests ? 'Linked' : 'None'}</strong></span>
                </div>
                <div className="flex items-center gap-2 text-slate-600">
                  <span className={`w-1.5 h-1.5 rounded-full ${status?.capabilities?.import_analysis ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                  <span>Import Graph: <strong>{status?.capabilities?.import_analysis ? 'Active' : 'Basic'}</strong></span>
                </div>
              </div>

              {/* Discovered Components preview */}
              {status?.profile?.discovered_components && status.profile.discovered_components.length > 0 && (
                <div className="pt-2">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
                    Discovered Architecture Modules ({status.profile.discovered_components.length}):
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {status.profile.discovered_components.slice(0, 8).map((comp) => (
                      <span
                        key={comp}
                        className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px] font-mono border border-slate-200"
                      >
                        {comp}
                      </span>
                    ))}
                    {status.profile.discovered_components.length > 8 && (
                      <span className="text-[11px] text-slate-400 self-center">
                        +{status.profile.discovered_components.length - 8} more
                      </span>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: Quick Actions */}
        <div className="lg:col-span-5 space-y-3">
          <Card hoverable onClick={() => onNavigate('analysis')}>
            <CardContent className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 flex-shrink-0">
                  <Search className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-slate-900">Analyse a Code Change</h4>
                  <p className="text-[11px] text-slate-500">Predict ripple effects & select tests</p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400" />
            </CardContent>
          </Card>

          <Card hoverable onClick={() => onNavigate('explorer')}>
            <CardContent className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600 flex-shrink-0">
                  <Code2 className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-slate-900">Explore Repository Code</h4>
                  <p className="text-[11px] text-slate-500">Browse files, AST symbols & dependencies</p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400" />
            </CardContent>
          </Card>

          <Card hoverable onClick={() => onNavigate('cicd')}>
            <CardContent className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 flex-shrink-0">
                  <GitPullRequest className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-slate-900">1-Click CI/CD Integration</h4>
                  <p className="text-[11px] text-slate-500">Install workflow directly into GitHub</p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400" />
            </CardContent>
          </Card>

          <Card hoverable onClick={() => onNavigate('observability')}>
            <CardContent className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600 flex-shrink-0">
                  <Activity className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-slate-900">View Prometheus Telemetry</h4>
                  <p className="text-[11px] text-slate-500">Inspect real-time P95 latency & decisions</p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400" />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Recent Activity / Deployments Table */}
      <Card>
        <CardHeader
          title="Recent CI/CD Deployment Records"
          subtitle="Real-time deployment audit log from DeploymentManager"
          action={
            <Button
              size="sm"
              variant="outline"
              onClick={() => onNavigate('gate')}
            >
              Policy Gate View
            </Button>
          }
        />
        <div className="overflow-x-auto">
          {deployments.length > 0 ? (
            <table className="saas-table">
              <thead>
                <tr>
                  <th>Deployment ID</th>
                  <th>Image Tag</th>
                  <th>Environment</th>
                  <th>Status</th>
                  <th>Known-Good</th>
                  <th>Deployed At</th>
                </tr>
              </thead>
              <tbody className="font-mono text-xs">
                {deployments.map((d) => (
                  <tr key={d.deployment_id}>
                    <td className="font-semibold text-slate-900">{d.deployment_id}</td>
                    <td className="text-slate-600">{d.image_tag}</td>
                    <td className="uppercase text-slate-500">{d.environment}</td>
                    <td>
                      <Badge variant={d.status === 'HEALTHY' ? 'success' : 'error'} size="sm" dot>
                        {d.status}
                      </Badge>
                    </td>
                    <td>
                      {d.is_known_good ? (
                        <span className="text-emerald-700 font-semibold text-[11px] flex items-center gap-1">
                          <Shield className="w-3 h-3 text-emerald-600" /> Pointer
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="text-slate-500">
                      {d.deployed_at ? new Date(d.deployed_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-8 text-center text-xs text-slate-500">
              No deployment records registered yet. Deployments are recorded when GitHub Actions triggers the QA gate.
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}

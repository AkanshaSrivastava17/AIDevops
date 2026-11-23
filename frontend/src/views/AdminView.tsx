import React, { useState, useEffect } from 'react'
import {
  FolderGit2,
  GitPullRequest,
  FileText,
  Sparkles,
  BarChart3,
  ExternalLink
} from 'lucide-react'
import type { AuditLogEntry, DemoPersona } from '../types/api'
import {
  fetchRepositories,
  fetchAuditLogs,
  installWorkflow,
  fetchPrometheusMetrics
} from '../services/api'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Tabs } from '../components/ui/Tabs'

interface AdminViewProps {
  activePersona?: DemoPersona | null
}

export const AdminView: React.FC<AdminViewProps> = () => {
  const [activeTab, setActiveTab] = useState<'repos' | 'integrations' | 'audit' | 'observability'>('repos')
  const [repos, setRepos] = useState<any[]>([])
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([])
  const [metricsText, setMetricsText] = useState('')

  // Installer Wizard State
  const [repoSlug, setRepoSlug] = useState('netbox-community/netbox')
  const [installStatus, setInstallStatus] = useState<any>(null)
  const [isInstalling, setIsInstalling] = useState(false)

  useEffect(() => {
    loadData()
  }, [activeTab])

  const loadData = async () => {
    try {
      if (activeTab === 'repos') {
        const data = await fetchRepositories()
        setRepos(data)
      } else if (activeTab === 'audit') {
        const logs = await fetchAuditLogs()
        setAuditLogs(logs)
      } else if (activeTab === 'observability') {
        const metrics = await fetchPrometheusMetrics()
        setMetricsText(metrics)
      }
    } catch (err) {
      console.error('Failed to load admin data', err)
    }
  }

  const handleInstallCI = async () => {
    setIsInstalling(true)
    try {
      const res = await installWorkflow({
        repository_url_or_slug: repoSlug,
        github_token: 'demo-token',
        dry_run: true,
      })
      setInstallStatus(res)
    } catch (err) {
      console.error('CI installation failed', err)
    } finally {
      setIsInstalling(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Bar Tabs */}
      <div className="flex items-center justify-between">
        <Tabs
          tabs={[
            { id: 'repos', label: 'Repositories & Indexes', icon: <FolderGit2 className="w-4 h-4" /> },
            { id: 'integrations', label: 'CI/CD & GitHub Webhooks', icon: <GitPullRequest className="w-4 h-4" /> },
            { id: 'audit', label: 'Append-Only Audit Trail', icon: <FileText className="w-4 h-4" /> },
            { id: 'observability', label: 'Telemetry & Observability', icon: <BarChart3 className="w-4 h-4" /> },
          ]}
          activeTab={activeTab}
          onChange={(id) => setActiveTab(id as any)}
          variant="pills"
        />
        <Badge variant="brand" size="sm">System Governance</Badge>
      </div>

      {/* 1. Repositories Tab */}
      {activeTab === 'repos' && (
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Connected Repositories</h3>
              <p className="text-xs text-slate-500">
                Repositories indexed into SQLite metadata and Chroma vector embeddings.
              </p>
            </div>
          </div>

          <div className="divide-y divide-slate-100 text-xs">
            {repos.map((r) => (
              <div key={r.repository_id} className="py-3 flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-slate-900 text-sm">{r.name}</h4>
                  <p className="text-slate-500 font-mono text-[11px]">{r.repository_url}</p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant="success" size="sm">Index Ready</Badge>
                  <Button variant="secondary" size="sm">Re-Index</Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 2. Integrations Tab */}
      {activeTab === 'integrations' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* GitHub Webhook Handler */}
          <Card className="p-5 space-y-3 text-xs">
            <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <GitPullRequest className="w-4 h-4 text-indigo-600" />
              <span>GitHub Webhooks Receiver</span>
            </h4>
            <p className="text-slate-600">
              Receives GitHub `push` and `pull_request` webhook events with HMAC-SHA256 signature verification and idempotency keys.
            </p>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1 font-mono text-[11px]">
              <div>Endpoint: <strong className="text-slate-800">/api/webhooks/github</strong></div>
              <div>Events: <strong className="text-indigo-700">pull_request, push</strong></div>
              <div>Signature: <strong className="text-emerald-700">X-Hub-Signature-256</strong></div>
            </div>
          </Card>

          {/* GitHub Actions CI Installer Wizard */}
          <Card className="p-5 space-y-3 text-xs">
            <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              <span>Install CI/CD Quality Gate Workflow</span>
            </h4>
            <p className="text-slate-600">
              Installs `.github/workflows/historyrag-gate.yml` into your target repository to enforce policy gates automatically.
            </p>

            <div className="space-y-2">
              <input
                type="text"
                value={repoSlug}
                onChange={(e) => setRepoSlug(e.target.value)}
                placeholder="owner/repo"
                className="w-full bg-slate-50 border border-slate-200 rounded p-2 text-xs"
              />
              <Button
                variant="primary"
                size="sm"
                className="w-full"
                loading={isInstalling}
                onClick={handleInstallCI}
              >
                Generate & Install Workflow
              </Button>
            </div>

            {installStatus && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-900 text-[11px] space-y-1">
                <strong>{installStatus.status}:</strong> {installStatus.message}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* 3. Append-Only Audit Trail Tab (Section 7.8 & 10.1) */}
      {activeTab === 'audit' && (
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Append-Only Audit Trail</h3>
              <p className="text-xs text-slate-500">
                Immutable, tamper-evident ledger tracking state transitions, brief versions, overrides, and approvals.
              </p>
            </div>
            <Badge variant="brand" size="sm">Tamper Evident</Badge>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-400 font-semibold text-[10px] uppercase">
                  <th className="py-2 px-3">Timestamp</th>
                  <th className="py-2 px-3">Actor</th>
                  <th className="py-2 px-3">Action</th>
                  <th className="py-2 px-3">Object Type</th>
                  <th className="py-2 px-3">Object ID</th>
                  <th className="py-2 px-3">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-2.5 px-3 font-mono text-[11px] text-slate-500">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-2.5 px-3 font-medium text-slate-900">{log.actor_name}</td>
                    <td className="py-2.5 px-3">
                      <span className="font-mono text-[10px] font-bold bg-slate-100 px-1.5 py-0.2 rounded text-slate-800">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-500">{log.object_type}</td>
                    <td className="py-2.5 px-3 font-mono text-indigo-700">{log.object_id}</td>
                    <td className="py-2.5 px-3 text-slate-600 max-w-xs truncate">{log.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* 4. Observability Tab */}
      {activeTab === 'observability' && (
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Prometheus Telemetry & Tracing</h3>
              <p className="text-xs text-slate-500">
                Live metrics scraping endpoint for Grafana, Arize Phoenix, and Prometheus.
              </p>
            </div>
            <a
              href="/metrics"
              target="_blank"
              rel="noreferrer"
              className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold flex items-center gap-1"
            >
              <span>View Raw /metrics</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>

          <pre className="p-4 bg-slate-900 text-emerald-400 font-mono text-xs rounded-xl overflow-x-auto max-h-96">
            {metricsText || '# Scraping Prometheus metrics...'}
          </pre>
        </Card>
      )}
    </div>
  )
}

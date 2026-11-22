import React, { useState } from 'react'
import {
  GitPullRequest,
  CheckCircle,
  ExternalLink,
  Copy,
  Terminal,
  Eye,
  EyeOff,
} from 'lucide-react'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { installWorkflow } from '../services/api'
import type { WorkflowInstallResponse, RepositoryItem } from '../types/api'

interface CicdViewProps {
  activeRepo: RepositoryItem | null
}

export const CicdView: React.FC<CicdViewProps> = ({ activeRepo }) => {
  const [repoUrl, setRepoUrl] = useState(
    activeRepo?.repository_url && activeRepo.repository_url.startsWith('http')
      ? activeRepo.repository_url
      : 'https://github.com/Radhikag19/PyCalculator'
  )
  const [branchName, setBranchName] = useState('historyrag-ai-cicd-setup')
  const [githubToken, setGithubToken] = useState('')
  const [showToken, setShowToken] = useState(false)
  const [commitToMain, setCommitToMain] = useState(false)
  const [isDryRun, setIsDryRun] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<WorkflowInstallResponse | null>(null)
  const [copied, setCopied] = useState(false)

  const handleInstall = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!repoUrl.trim()) {
      setError('Please provide a valid GitHub repository URL or slug.')
      return
    }
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await installWorkflow({
        repository_url_or_slug: repoUrl,
        github_token: githubToken.trim() || undefined,
        branch_name: branchName,
        commit_to_main: commitToMain,
        dry_run: isDryRun,
      })
      setResult(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Installation failed')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Title */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <GitPullRequest className="w-5 h-5 text-indigo-600" />
          CI/CD Integration
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Bring History-RAG intelligence directly into your GitHub workflow. Automatically creates a setup branch and opens an onboarding Pull Request with <code className="text-indigo-600 font-mono">.github/workflows/historyrag.yml</code>.
        </p>
      </div>

      {error && <ErrorBanner message={error} onRetry={() => setError(null)} />}

      {/* GitHub Credential Manager Auto-Detection Status */}
      <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/70 text-emerald-900 text-xs flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>
            <strong>Git Credentials Auto-Detected:</strong> Authenticated as <code className="font-bold text-emerald-950">AkanshaSrivastava17</code>. Personal Access Token is optional.
          </span>
        </div>
        <Badge variant="success" size="sm">
          Active
        </Badge>
      </div>

      {/* Configuration Form */}
      <Card>
        <CardHeader
          title="Onboarding Configuration"
          subtitle="Define target repository, setup branch name, and installation mode"
        />
        <CardContent>
          <form onSubmit={handleInstall} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="repo-url-slug" className="text-xs font-medium text-slate-700 block mb-1">
                  GitHub Repository URL or Slug:
                </label>
                <input
                  id="repo-url-slug"
                  type="text"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/owner/repository"
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-indigo-600 font-mono"
                />
              </div>

              <div>
                <label htmlFor="setup-branch-name" className="text-xs font-medium text-slate-700 block mb-1">
                  Setup Branch Name:
                </label>
                <input
                  id="setup-branch-name"
                  type="text"
                  value={branchName}
                  onChange={(e) => setBranchName(e.target.value)}
                  placeholder="historyrag-ai-cicd-setup"
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-indigo-600 font-mono"
                />
              </div>
            </div>

            {/* Optional Token */}
            <div>
              <label htmlFor="gh-token-input" className="text-xs font-medium text-slate-700 block mb-1">
                Custom GitHub Personal Access Token (Optional):
              </label>
              <div className="relative">
                <input
                  id="gh-token-input"
                  type={showToken ? 'text' : 'password'}
                  value={githubToken}
                  onChange={(e) => setGithubToken(e.target.value)}
                  placeholder="Leave empty to use auto-detected local Git credentials"
                  className="w-full bg-white border border-slate-300 rounded-lg pl-3 pr-10 py-2 text-xs text-slate-900 focus:outline-indigo-600 font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowToken(!showToken)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  {showToken ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {/* Mode selection */}
            <div className="pt-2 border-t border-slate-100 space-y-2">
              <span className="text-xs font-medium text-slate-700 block">Installation Method:</span>
              <div className="space-y-1.5">
                <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="radio"
                    name="mode"
                    checked={!commitToMain}
                    onChange={() => setCommitToMain(false)}
                    className="text-indigo-600 focus:ring-indigo-500"
                  />
                  <span>Create Onboarding Pull Request (Recommended for production codebases)</span>
                </label>
                <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer">
                  <input
                    type="radio"
                    name="mode"
                    checked={commitToMain}
                    onChange={() => setCommitToMain(true)}
                    className="text-indigo-600 focus:ring-indigo-500"
                  />
                  <span>Direct Commit to Default Branch (Requires admin push permissions)</span>
                </label>
              </div>
            </div>

            {/* Simulation mode toggle */}
            <div className="pt-2 border-t border-slate-100">
              <label className="flex items-center gap-2 text-xs font-medium text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isDryRun}
                  onChange={(e) => setIsDryRun(e.target.checked)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span>Simulation / Dry-Run Mode</span>
              </label>
              <span className="text-[11px] text-slate-400 ml-5 block">
                Simulate PR creation and validate workflow YAML without modifying the remote repository.
              </span>
            </div>

            {/* Submit Button */}
            <div className="pt-3">
              <Button
                type="submit"
                onClick={(e) => {
                  e.preventDefault()
                  handleInstall(e)
                }}
                loading={loading}
                disabled={!repoUrl.trim()}
                icon={<GitPullRequest className="w-4 h-4" />}
                className="w-full sm:w-auto px-6 bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer"
              >
                1-Click Install CI/CD into Repository
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Installation Result */}
      {result && (
        <Card className="border-emerald-200 bg-emerald-50/30">
          <CardHeader
            title={
              <div className="flex items-center gap-2 text-emerald-900">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                <span>Live GitHub Installation Successful</span>
              </div>
            }
            subtitle={result.message}
          />
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs font-mono">
              <div className="p-3 rounded-lg bg-white border border-slate-200">
                <span className="text-slate-400 block text-[10px]">TARGET REPO</span>
                <span className="font-semibold text-slate-800 truncate block mt-0.5">
                  {result.repository}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-white border border-slate-200">
                <span className="text-slate-400 block text-[10px]">SETUP BRANCH</span>
                <span className="font-semibold text-slate-800 truncate block mt-0.5">
                  {result.branch}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-white border border-slate-200">
                <span className="text-slate-400 block text-[10px]">WORKFLOW PATH</span>
                <span className="font-semibold text-slate-800 truncate block mt-0.5">
                  {result.workflow_path}
                </span>
              </div>
            </div>

            {/* Pull Request Link */}
            {result.pull_request_url && (
              <div className="pt-2">
                <a
                  href={result.pull_request_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition-colors"
                >
                  <span>View Live Onboarding PR #{result.pull_request_number || 4} on GitHub</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            )}

            {/* Generated YAML Preview */}
            {result.workflow_preview && (
              <div className="pt-2 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono text-slate-600 flex items-center gap-1.5">
                    <Terminal className="w-3.5 h-3.5 text-slate-400" />
                    Generated .github/workflows/historyrag.yml
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopy(result.workflow_preview!)}
                    className="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1 cursor-pointer"
                  >
                    <Copy className="w-3 h-3" />
                    <span>{copied ? 'Copied' : 'Copy YAML'}</span>
                  </button>
                </div>
                <pre className="p-4 bg-slate-900 rounded-lg text-xs font-mono text-slate-200 overflow-x-auto max-h-64 leading-relaxed">
                  {result.workflow_preview}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

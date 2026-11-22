import React, { useState } from 'react'
import {
  Upload,
  GitBranch,
  FolderGit2,
  CheckCircle,
  FileArchive,
  Search,
  Code2,
} from 'lucide-react'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { uploadRepositoryZip, cloneRepository } from '../services/api'
import type { RepositoryItem } from '../types/api'
import type { ViewId } from '../components/layout/Sidebar'

interface RepositoriesViewProps {
  repositories: RepositoryItem[]
  activeRepoId: string
  onSelectRepo: (repoId: string) => void
  onRepoAdded: (newRepo: RepositoryItem) => void
  onNavigate: (view: ViewId) => void
}

export const RepositoriesView: React.FC<RepositoriesViewProps> = ({
  repositories,
  activeRepoId,
  onSelectRepo,
  onRepoAdded,
  onNavigate,
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [zipFile, setZipFile] = useState<File | null>(null)
  const [customRepoName, setCustomRepoName] = useState('')
  const [githubUrl, setGithubUrl] = useState('')
  const [loadingZip, setLoadingZip] = useState(false)
  const [loadingGit, setLoadingGit] = useState(false)
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const handleUploadZip = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!zipFile) {
      setNotification({ type: 'error', message: 'Please select a .zip archive of your repository.' })
      return
    }
    setLoadingZip(true)
    setNotification(null)
    try {
      const slug = customRepoName.trim()
        ? customRepoName.toLowerCase().replace(/[^a-z0-9-_]/g, '_')
        : undefined
      const res = await uploadRepositoryZip(zipFile, slug)
      const newRepo: RepositoryItem = {
        repository_id: res.repository_id,
        name: res.name || res.repository_id,
        repository_url: 'Local Upload (ZIP)',
        language: 'Polyglot',
        description: 'Uploaded codebase indexed with Tree-Sitter',
      }
      onRepoAdded(newRepo)
      onSelectRepo(res.repository_id)
      setNotification({
        type: 'success',
        message: `Successfully uploaded and indexed "${res.name}" with Tree-Sitter AST!`,
      })
      setZipFile(null)
      setCustomRepoName('')
    } catch (err: unknown) {
      setNotification({ type: 'error', message: err instanceof Error ? err.message : 'Upload failed.' })
    } finally {
      setLoadingZip(false)
    }
  }

  const handleCloneGit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!githubUrl.trim()) {
      setNotification({ type: 'error', message: 'Please enter a valid GitHub repository URL.' })
      return
    }
    setLoadingGit(true)
    setNotification(null)
    try {
      const parts = githubUrl.split('/')
      const slug = parts[parts.length - 1].replace('.git', '').toLowerCase()
      await cloneRepository(githubUrl.trim(), slug)
      const formattedName = slug.charAt(0).toUpperCase() + slug.slice(1).replace(/[-_]/g, ' ')
      const newRepo: RepositoryItem = {
        repository_id: slug,
        name: formattedName,
        repository_url: githubUrl.trim(),
        language: 'Polyglot',
        description: 'Cloned from GitHub and indexed with Tree-Sitter',
      }
      onRepoAdded(newRepo)
      onSelectRepo(slug)
      setNotification({
        type: 'success',
        message: `Successfully cloned and indexed "${formattedName}" from GitHub!`,
      })
      setGithubUrl('')
    } catch (err: unknown) {
      setNotification({ type: 'error', message: err instanceof Error ? err.message : 'Clone failed.' })
    } finally {
      setLoadingGit(false)
    }
  }

  const filteredRepos = repositories.filter(
    (r) =>
      r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.repository_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.repository_url && r.repository_url.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <FolderGit2 className="w-5 h-5 text-indigo-600" />
          Repository Management
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Connect GitHub repositories or upload local project archives. Each repository is analyzed with Tree-Sitter to build AST call-graphs and structural indices.
        </p>
      </div>

      {notification && (
        <div
          className={`p-4 rounded-xl border text-xs flex items-center justify-between ${
            notification.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          <div className="flex items-center gap-2.5">
            <CheckCircle className="w-4 h-4 flex-shrink-0" />
            <span>{notification.message}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-slate-400 hover:text-slate-600 cursor-pointer font-bold px-1"
          >
            &times;
          </button>
        </div>
      )}

      {/* Ingestion Cards (Option 1 & Option 2) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Option 1: GitHub URL */}
        <Card>
          <CardHeader
            title="Connect via GitHub URL"
            subtitle="Clone and index public or accessible private Git repositories"
          />
          <CardContent>
            <form onSubmit={handleCloneGit} className="space-y-4">
              <div>
                <label htmlFor="repo-clone-url" className="text-xs font-medium text-slate-700 block mb-1">
                  GitHub Repository URL:
                </label>
                <input
                  id="repo-clone-url"
                  type="text"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/owner/repository"
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-indigo-600 font-mono"
                />
              </div>

              <Button
                type="submit"
                loading={loadingGit}
                disabled={!githubUrl.trim()}
                icon={<GitBranch className="w-3.5 h-3.5" />}
                className="w-full"
              >
                Clone & Index Repository
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Option 2: Upload ZIP */}
        <Card>
          <CardHeader
            title="Upload Codebase Archive (.ZIP)"
            subtitle="Ingest local source code directories across Python, JS, TS, Go, Java"
          />
          <CardContent>
            <form onSubmit={handleUploadZip} className="space-y-3">
              <label className="border-2 border-dashed border-slate-200 hover:border-indigo-400 rounded-xl p-3 flex flex-col items-center justify-center cursor-pointer bg-slate-50/50 hover:bg-slate-50 transition-colors">
                <FileArchive className="w-6 h-6 text-indigo-500 mb-1" />
                <span className="text-xs font-medium text-slate-700 text-center">
                  {zipFile ? zipFile.name : 'Click to select .zip archive'}
                </span>
                <span className="text-[10px] text-slate-400 mt-0.5">Max 100MB ZIP file</span>
                <input
                  type="file"
                  accept=".zip"
                  onChange={(e) => setZipFile(e.target.files?.[0] || null)}
                  className="hidden"
                />
              </label>

              <div>
                <input
                  type="text"
                  value={customRepoName}
                  onChange={(e) => setCustomRepoName(e.target.value)}
                  placeholder="Repository Slug (e.g. ecommerce-service)"
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-indigo-600 font-mono"
                />
              </div>

              <Button
                type="submit"
                loading={loadingZip}
                disabled={!zipFile}
                icon={<Upload className="w-3.5 h-3.5" />}
                className="w-full"
              >
                Upload & Ingest Archive
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>

      {/* Repositories Table */}
      <Card>
        <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-900">
              Indexed Repositories ({repositories.length})
            </h3>
          </div>

          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search repositories..."
              className="bg-white border border-slate-200 rounded-lg pl-8 pr-3 py-1 text-xs text-slate-800 focus:outline-indigo-600 w-56"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="saas-table">
            <thead>
              <tr>
                <th>Repository</th>
                <th>Source URL</th>
                <th>Language</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredRepos.map((repo) => {
                const isActive = activeRepoId === repo.repository_id
                return (
                  <tr key={repo.repository_id}>
                    <td>
                      <div className="flex items-center gap-2">
                        <FolderGit2 className="w-4 h-4 text-slate-400 flex-shrink-0" />
                        <div>
                          <span className="font-semibold text-slate-900 block">{repo.name}</span>
                          <span className="text-[11px] text-slate-400 font-mono">{repo.repository_id}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="text-xs text-slate-600 font-mono truncate max-w-xs block">
                        {repo.repository_url || 'Local codebase'}
                      </span>
                    </td>
                    <td>
                      <Badge variant="brand" size="sm">
                        {repo.language || 'Python'}
                      </Badge>
                    </td>
                    <td>
                      {isActive ? (
                        <Badge variant="success" size="sm" dot>
                          Active Workspace
                        </Badge>
                      ) : (
                        <span className="text-xs text-slate-400">Indexed</span>
                      )}
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        {!isActive ? (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onSelectRepo(repo.repository_id)}
                          >
                            Set Active
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => onNavigate('analysis')}
                          >
                            Analyse
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            onSelectRepo(repo.repository_id)
                            onNavigate('explorer')
                          }}
                          icon={<Code2 className="w-3.5 h-3.5" />}
                        >
                          Files
                        </Button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}

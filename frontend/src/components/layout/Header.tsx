import React from 'react'
import {
  FolderGit2,
  ExternalLink,
  ChevronRight,
  GitBranch,
} from 'lucide-react'
import type { ViewId } from './Sidebar'
import type { RepositoryItem } from '../../types/api'

interface HeaderProps {
  currentView: ViewId
  repositories: RepositoryItem[]
  activeRepoId: string
  onSelectRepo: (repoId: string) => void
  isOnline: boolean
}

export const Header: React.FC<HeaderProps> = ({
  currentView,
  repositories,
  activeRepoId,
  onSelectRepo,
  isOnline,
}) => {
  const viewTitles: Record<ViewId, { title: string; category: string }> = {
    overview: { title: 'Overview Dashboard', category: 'Workspace' },
    repositories: { title: 'Repository Management', category: 'Workspace' },
    analysis: { title: 'Change Impact Analysis', category: 'Workspace' },
    explorer: { title: 'Repository Code Explorer', category: 'Intelligence' },
    cicd: { title: 'CI/CD GitHub Integration', category: 'DevOps' },
    gate: { title: 'Policy Gate & Rollback', category: 'DevOps' },
    observability: { title: 'Prometheus Observability', category: 'Monitoring' },
  }

  const activeViewInfo = viewTitles[currentView] || { title: 'Dashboard', category: 'History-RAG' }

  return (
    <header className="h-14 bg-white border-b border-slate-200/80 px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Left: Breadcrumbs */}
      <div className="flex items-center gap-2 text-xs">
        <span className="text-slate-400 font-medium">{activeViewInfo.category}</span>
        <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
        <span className="text-slate-900 font-semibold">{activeViewInfo.title}</span>
      </div>

      {/* Right: Controls & Badges */}
      <div className="flex items-center gap-3">
        {/* Active Repository Selector */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-lg">
          <FolderGit2 className="w-3.5 h-3.5 text-indigo-600 flex-shrink-0" />
          <span className="text-[11px] font-medium text-slate-500 hidden sm:inline">Repo:</span>
          <select
            value={activeRepoId}
            onChange={(e) => onSelectRepo(e.target.value)}
            aria-label="Active Repository Selector"
            className="bg-transparent text-xs font-semibold text-slate-800 focus:outline-none cursor-pointer pr-1"
          >
            {repositories.map((r) => (
              <option key={r.repository_id} value={r.repository_id}>
                {r.name}
              </option>
            ))}
          </select>
        </div>

        {/* GitHub User Badge */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600 font-mono">
          <GitBranch className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-[11px]">AkanshaSrivastava17</span>
        </div>

        {/* Link to Classic Streamlit */}
        <a
          href="http://localhost:8501"
          target="_blank"
          rel="noreferrer"
          title="Open Streamlit interface in parallel"
          className="flex items-center gap-1 text-[11px] font-medium text-slate-600 hover:text-indigo-600 px-2.5 py-1 rounded-md hover:bg-slate-50 transition-colors"
        >
          <span>Streamlit</span>
          <ExternalLink className="w-3 h-3 text-slate-400" />
        </a>

        {/* Online Pill */}
        <div className="flex items-center gap-1 text-[11px] text-slate-500">
          <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-500' : 'bg-rose-500'}`} />
          <span className="hidden lg:inline">{isOnline ? 'Online' : 'Offline'}</span>
        </div>
      </div>
    </header>
  )
}

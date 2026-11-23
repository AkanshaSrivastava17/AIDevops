import React, { useState } from 'react'
import {
  FolderGit2,
  ExternalLink,
  ChevronRight,
  Layers,
  ChevronDown
} from 'lucide-react'
import type { ViewId } from './Sidebar'
import type { DemoPersona, Project } from '../../types/api'

interface HeaderProps {
  currentView: ViewId
  projects: Project[]
  activeProjectId: string
  onSelectProject: (projectId: string) => void
  repositories: Array<{ repository_id: string; name: string }>
  activeRepoId: string
  onSelectRepo: (repoId: string) => void
  isOnline: boolean
  personas: DemoPersona[]
  activePersona: DemoPersona | null
  onSwitchPersona: (personaId: string) => void
}

export const Header: React.FC<HeaderProps> = ({
  currentView,
  projects,
  activeProjectId,
  onSelectProject,
  repositories,
  activeRepoId,
  onSelectRepo,
  isOnline,
  personas,
  activePersona,
  onSwitchPersona,
}) => {
  const [isPersonaMenuOpen, setIsPersonaMenuOpen] = useState(false)

  const viewTitles: Record<ViewId, { title: string; category: string }> = {
    home: { title: 'Executive & Developer Dashboard', category: 'Overview' },
    ask: { title: 'Cited Q&A & Knowledge Map', category: '1. Learn' },
    explorer: { title: 'Code & Temporal File Explorer', category: '1. Learn' },
    requests: { title: 'Feature Requests & AI Clarity', category: '2. Plan' },
    brief: { title: 'Feature Brief & Impact Analysis', category: '2. Plan' },
    decisions: { title: 'Architectural Decision Log (ADRs)', category: '2. Plan' },
    tasks: { title: 'Task Board & Pre-PR Diff Check', category: '3. Build' },
    pipelines: { title: 'CI/CD Pipelines & Reproducible Gates', category: '4. Verify' },
    insights: { title: 'Value Dashboard & Retrospectives', category: '5. Insights' },
    admin: { title: 'Integrations & Audit Trail', category: 'Governance' },
    // Legacy aliases
    overview: { title: 'Overview Dashboard', category: 'Overview' },
    analysis: { title: 'Feature Requests & AI Clarity', category: '2. Plan' },
    repositories: { title: 'Repository Management', category: 'Governance' },
    cicd: { title: 'CI/CD Pipelines & Reproducible Gates', category: '4. Verify' },
    gate: { title: 'Policy Gate & Rollback', category: '4. Verify' },
    observability: { title: 'System Observability', category: 'Monitoring' },
  }

  const activeViewInfo = viewTitles[currentView] || { title: 'Dashboard', category: 'History-RAG' }

  const roleColors: Record<string, string> = {
    junior_developer: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    product_owner: 'bg-amber-50 text-amber-800 border-amber-200',
    tech_lead: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    qa_engineer: 'bg-purple-50 text-purple-700 border-purple-200',
    engineering_manager: 'bg-sky-50 text-sky-700 border-sky-200',
    admin: 'bg-rose-50 text-rose-700 border-rose-200',
  }

  return (
    <header className="h-14 bg-white border-b border-slate-200/80 px-4 md:px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Left: Breadcrumbs */}
      <div className="flex items-center gap-2 text-xs">
        <span className="text-slate-400 font-medium hidden sm:inline">{activeViewInfo.category}</span>
        <ChevronRight className="w-3.5 h-3.5 text-slate-300 hidden sm:inline" />
        <span className="text-slate-900 font-semibold">{activeViewInfo.title}</span>
      </div>

      {/* Right: Controls & Demo Role Switcher */}
      <div className="flex items-center gap-2.5">
        {/* Project Selector */}
        {projects.length > 0 && (
          <div className="hidden lg:flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-2 py-1 rounded-lg">
            <Layers className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={activeProjectId}
              onChange={(e) => onSelectProject(e.target.value)}
              aria-label="Active Project"
              className="bg-transparent text-[11px] font-semibold text-slate-700 focus:outline-none cursor-pointer pr-1"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Repository Selector */}
        <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-2 py-1 rounded-lg">
          <FolderGit2 className="w-3.5 h-3.5 text-indigo-600 flex-shrink-0" />
          <select
            value={activeRepoId}
            onChange={(e) => onSelectRepo(e.target.value)}
            aria-label="Active Repository"
            className="bg-transparent text-xs font-semibold text-slate-800 focus:outline-none cursor-pointer pr-1"
          >
            {repositories.map((r) => (
              <option key={r.repository_id} value={r.repository_id}>
                {r.name}
              </option>
            ))}
          </select>
        </div>

        {/* Demo Persona Switcher (Section 4 & 10.4) */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setIsPersonaMenuOpen(!isPersonaMenuOpen)}
            className="flex items-center gap-2 pl-2 pr-2.5 py-1 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors cursor-pointer text-xs"
          >
            <div className="w-5 h-5 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center text-[10px]">
              {activePersona ? activePersona.avatar : 'HR'}
            </div>
            <div className="hidden sm:flex flex-col text-left">
              <span className="font-semibold text-slate-800 leading-tight">
                {activePersona ? activePersona.name : 'Select Persona'}
              </span>
              <span className="text-[10px] text-slate-500 capitalize">
                {activePersona ? activePersona.role.replace('_', ' ') : 'Role'}
              </span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-0.5" />
          </button>

          {/* Persona Menu Dropdown */}
          {isPersonaMenuOpen && (
            <>
              <div
                className="fixed inset-0 z-30"
                onClick={() => setIsPersonaMenuOpen(false)}
              />
              <div className="absolute right-0 mt-1.5 w-72 rounded-xl bg-white shadow-xl border border-slate-200 z-40 py-1.5 animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="px-3 py-1.5 border-b border-slate-100 mb-1">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Switch Demo Persona
                  </p>
                  <p className="text-[11px] text-slate-500">
                    Test role-based views and actions
                  </p>
                </div>
                <div className="max-h-72 overflow-y-auto space-y-0.5 px-1">
                  {personas.map((p) => {
                    const isSelected = activePersona?.id === p.id
                    const badgeClass = roleColors[p.role] || 'bg-slate-100 text-slate-700'
                    return (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => {
                          onSwitchPersona(p.id)
                          setIsPersonaMenuOpen(false)
                        }}
                        className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left transition-colors cursor-pointer ${
                          isSelected
                            ? 'bg-indigo-50/80 text-indigo-900 font-semibold'
                            : 'hover:bg-slate-50 text-slate-700'
                        }`}
                      >
                        <div className="w-7 h-7 rounded-full bg-slate-200 text-slate-800 font-bold flex items-center justify-center text-xs shrink-0">
                          {p.avatar}
                        </div>
                        <div className="flex-1 truncate">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-medium text-slate-900 truncate">
                              {p.name}
                            </span>
                            <span
                              className={`text-[9px] font-mono px-1.5 py-0.2 rounded border font-medium ${badgeClass}`}
                            >
                              {p.role.replace('_', ' ')}
                            </span>
                          </div>
                          <p className="text-[10px] text-slate-500 truncate">{p.title}</p>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Streamlit Parallel Interface */}
        <a
          href="http://localhost:8501"
          target="_blank"
          rel="noreferrer"
          title="Open Streamlit view in parallel"
          className="hidden md:flex items-center gap-1 text-[11px] font-medium text-slate-600 hover:text-indigo-600 px-2 py-1 rounded-md hover:bg-slate-50 transition-colors"
        >
          <span>Streamlit</span>
          <ExternalLink className="w-3 h-3 text-slate-400" />
        </a>

        {/* Live Status indicator */}
        <div className="flex items-center gap-1.5 pl-1 text-[11px] text-slate-500">
          <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-500' : 'bg-rose-500'}`} />
        </div>
      </div>
    </header>
  )
}

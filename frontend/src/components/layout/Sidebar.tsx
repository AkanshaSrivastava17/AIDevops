import React from 'react'
import {
  LayoutDashboard,
  FolderGit2,
  Search,
  Code2,
  GitPullRequest,
  ShieldCheck,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  GitFork,
} from 'lucide-react'

export type ViewId =
  | 'overview'
  | 'repositories'
  | 'analysis'
  | 'explorer'
  | 'cicd'
  | 'gate'
  | 'observability'

interface SidebarProps {
  currentView: ViewId
  onSelectView: (view: ViewId) => void
  isCollapsed: boolean
  onToggleCollapse: () => void
  isOnline: boolean
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onSelectView,
  isCollapsed,
  onToggleCollapse,
  isOnline,
}) => {
  const sections = [
    {
      group: 'WORKSPACE',
      items: [
        { id: 'overview' as ViewId, label: 'Overview', icon: LayoutDashboard },
        { id: 'repositories' as ViewId, label: 'Repositories', icon: FolderGit2 },
        { id: 'analysis' as ViewId, label: 'Change Impact', icon: Search },
      ],
    },
    {
      group: 'INTELLIGENCE',
      items: [
        { id: 'explorer' as ViewId, label: 'Code Explorer', icon: Code2 },
      ],
    },
    {
      group: 'DEVOPS',
      items: [
        { id: 'cicd' as ViewId, label: 'CI/CD Integration', icon: GitPullRequest },
        { id: 'gate' as ViewId, label: 'Policy Gate & Rollback', icon: ShieldCheck },
      ],
    },
    {
      group: 'MONITORING',
      items: [
        { id: 'observability' as ViewId, label: 'Observability', icon: BarChart3 },
      ],
    },
  ]

  return (
    <aside
      className={`bg-white border-r border-slate-200/90 flex flex-col flex-shrink-0 transition-all duration-200 z-30 select-none ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-14 border-b border-slate-200/80 flex items-center justify-between px-4">
        {!isCollapsed ? (
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-xs shadow-indigo-600/30 flex-shrink-0">
              <GitFork className="w-4 h-4 text-white" />
            </div>
            <div className="truncate">
              <h1 className="font-semibold text-xs text-slate-900 tracking-tight flex items-center gap-1.5">
                <span>History-RAG</span>
                <span className="text-[10px] font-mono font-medium px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700 border border-indigo-100">
                  v2.0
                </span>
              </h1>
              <p className="text-[10px] text-slate-500 truncate">DevOps Intelligence</p>
            </div>
          </div>
        ) : (
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-xs mx-auto">
            <GitFork className="w-4 h-4 text-white" />
          </div>
        )}

        {!isCollapsed && (
          <button
            onClick={onToggleCollapse}
            title="Collapse sidebar"
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-5">
        {sections.map((sec) => (
          <div key={sec.group} className="space-y-1">
            {!isCollapsed && (
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-2 block mb-1.5">
                {sec.group}
              </span>
            )}
            {sec.items.map((item) => {
              const Icon = item.icon
              const isActive = currentView === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectView(item.id)}
                  title={isCollapsed ? item.label : undefined}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  } ${isCollapsed ? 'justify-center px-0' : ''}`}
                >
                  <Icon
                    className={`w-4 h-4 flex-shrink-0 ${
                      isActive ? 'text-indigo-600' : 'text-slate-400 group-hover:text-slate-600'
                    }`}
                  />
                  {!isCollapsed && <span className="truncate">{item.label}</span>}
                </button>
              )
            })}
          </div>
        ))}
      </nav>

      {/* Footer Connectivity & Collapse button */}
      <div className="p-3 border-t border-slate-200/80 bg-slate-50/50 flex items-center justify-between">
        {!isCollapsed ? (
          <div className="flex items-center gap-2 text-xs text-slate-600">
            <span
              className={`w-2 h-2 rounded-full flex-shrink-0 ${
                isOnline ? 'bg-emerald-500 ring-2 ring-emerald-100' : 'bg-amber-500 ring-2 ring-amber-100'
              }`}
            />
            <span className="text-[11px] font-medium text-slate-600 truncate">
              {isOnline ? 'API Connected' : 'API Reconnecting'}
            </span>
          </div>
        ) : (
          <span
            title={isOnline ? 'Backend Connected' : 'Backend Reconnecting'}
            className={`w-2 h-2 rounded-full mx-auto ${
              isOnline ? 'bg-emerald-500 ring-2 ring-emerald-100' : 'bg-amber-500 ring-2 ring-amber-100'
            }`}
          />
        )}

        {isCollapsed && (
          <button
            onClick={onToggleCollapse}
            title="Expand sidebar"
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors cursor-pointer mt-2 mx-auto block"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </aside>
  )
}

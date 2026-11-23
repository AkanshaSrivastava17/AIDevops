import React from 'react'
import {
  Home,
  MessageSquareText,
  Code2,
  FileSpreadsheet,
  FileCode2,
  BookmarkCheck,
  CheckSquare,
  ShieldCheck,
  TrendingUp,
  Settings,
  ChevronLeft,
  ChevronRight,
  GitFork,
  Radio
} from 'lucide-react'

export type ViewId =
  | 'home'
  | 'ask'
  | 'explorer'
  | 'requests'
  | 'brief'
  | 'decisions'
  | 'tasks'
  | 'pipelines'
  | 'insights'
  | 'admin'
  // Legacy aliases
  | 'overview'
  | 'analysis'
  | 'repositories'
  | 'cicd'
  | 'gate'
  | 'observability'

interface NavItem {
  id: ViewId
  label: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string
  activeParam?: string
}

interface NavSection {
  group: string
  items: NavItem[]
}

interface SidebarProps {
  currentView: ViewId
  onSelectView: (view: ViewId) => void
  isCollapsed: boolean
  onToggleCollapse: () => void
  isOnline: boolean
  activeRequestId?: string
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onSelectView,
  isCollapsed,
  onToggleCollapse,
  isOnline,
  activeRequestId,
}) => {
  const sections: NavSection[] = [
    {
      group: 'OVERVIEW',
      items: [
        { id: 'home' as ViewId, label: 'Dashboard', icon: Home, badge: 'Role' },
      ],
    },
    {
      group: '1. LEARN',
      items: [
        { id: 'ask' as ViewId, label: 'Ask the Repo', icon: MessageSquareText },
        { id: 'explorer' as ViewId, label: 'Code Explorer', icon: Code2 },
      ],
    },
    {
      group: '2. PLAN',
      items: [
        { id: 'requests' as ViewId, label: 'Feature Requests', icon: FileSpreadsheet },
        { id: 'brief' as ViewId, label: 'Feature Brief', icon: FileCode2, activeParam: activeRequestId },
        { id: 'decisions' as ViewId, label: 'Decision Log', icon: BookmarkCheck },
      ],
    },
    {
      group: '3. BUILD',
      items: [
        { id: 'tasks' as ViewId, label: 'My Tasks & Pre-PR', icon: CheckSquare },
      ],
    },
    {
      group: '4. VERIFY',
      items: [
        { id: 'pipelines' as ViewId, label: 'Pipelines & Gate', icon: ShieldCheck },
      ],
    },
    {
      group: '5. INSIGHTS',
      items: [
        { id: 'insights' as ViewId, label: 'Value & Retros', icon: TrendingUp },
      ],
    },
    {
      group: 'ADMINISTRATION',
      items: [
        { id: 'admin' as ViewId, label: 'Admin & Integrations', icon: Settings },
      ],
    },
  ]

  // Map legacy views to active selection
  const normalizedActiveView: ViewId =
    currentView === 'overview'
      ? 'home'
      : currentView === 'analysis'
      ? 'requests'
      : currentView === 'cicd' || currentView === 'gate'
      ? 'pipelines'
      : currentView === 'observability' || currentView === 'repositories'
      ? 'admin'
      : currentView

  return (
    <aside
      className={`bg-white border-r border-slate-200/90 flex flex-col flex-shrink-0 transition-all duration-200 z-30 select-none ${
        isCollapsed ? 'w-16' : 'w-60'
      }`}
    >
      {/* Brand Header */}
      <div className="h-14 border-b border-slate-200/80 flex items-center justify-between px-3.5">
        {!isCollapsed ? (
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-xs shadow-indigo-600/30 flex-shrink-0">
              <GitFork className="w-4 h-4 text-white" />
            </div>
            <div className="truncate">
              <h1 className="font-semibold text-xs text-slate-900 tracking-tight flex items-center gap-1.5">
                <span>History-RAG</span>
                <span className="text-[10px] font-mono font-medium px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700 border border-indigo-100">
                  v2.2
                </span>
              </h1>
              <p className="text-[10px] text-slate-500 truncate">Engineering Memory</p>
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
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            title="Collapse sidebar"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-4">
        {sections.map((sec) => (
          <div key={sec.group} className="space-y-0.5">
            {!isCollapsed && (
              <div className="px-2.5 py-1 text-[10px] font-bold text-slate-400 tracking-wider">
                {sec.group}
              </div>
            )}
            {sec.items.map((item) => {
              const Icon = item.icon
              const isActive = normalizedActiveView === item.id

              return (
                <button
                  key={item.id}
                  onClick={() => onSelectView(item.id)}
                  title={isCollapsed ? item.label : undefined}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium transition-all group ${
                    isActive
                      ? 'bg-indigo-50/90 text-indigo-700 font-semibold shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                  }`}
                >
                  <Icon
                    className={`w-4 h-4 flex-shrink-0 transition-colors ${
                      isActive ? 'text-indigo-600' : 'text-slate-400 group-hover:text-slate-600'
                    }`}
                  />
                  {!isCollapsed && (
                    <span className="truncate flex-1 text-left">{item.label}</span>
                  )}
                  {!isCollapsed && item.badge && (
                    <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-slate-100 text-slate-500">
                      {item.badge}
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        ))}
      </div>

      {/* Footer System Status */}
      <div className="p-3 border-t border-slate-200/80 bg-slate-50/50">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 overflow-hidden">
            <Radio className={`w-3.5 h-3.5 ${isOnline ? 'text-emerald-500 animate-pulse' : 'text-rose-500'}`} />
            {!isCollapsed && (
              <span className="text-[11px] text-slate-600 font-medium truncate">
                {isOnline ? 'Live Intelligence' : 'Offline'}
              </span>
            )}
          </div>
          {isCollapsed && (
            <button
              onClick={onToggleCollapse}
              className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors mx-auto"
              title="Expand sidebar"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </aside>
  )
}

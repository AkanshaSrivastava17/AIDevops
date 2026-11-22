import { useState, useEffect } from 'react'
import { Sidebar, type ViewId } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'
import { OverviewView } from './views/OverviewView'
import { RepositoriesView } from './views/RepositoriesView'
import { ChangeAnalysisView } from './views/ChangeAnalysisView'
import { ExplorerView } from './views/ExplorerView'
import { CicdView } from './views/CicdView'
import { PolicyGateView } from './views/PolicyGateView'
import { ObservabilityView } from './views/ObservabilityView'
import { fetchHealth, fetchRepositories } from './services/api'
import type { RepositoryItem } from './types/api'

export function App() {
  const [currentView, setCurrentView] = useState<ViewId>('overview')
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isOnline, setIsOnline] = useState(true)
  const [repositories, setRepositories] = useState<RepositoryItem[]>([])
  const [activeRepoId, setActiveRepoId] = useState<string>('pycalculator')

  // Initial load
  useEffect(() => {
    const init = async () => {
      try {
        const [h, repos] = await Promise.all([
          fetchHealth().catch(() => null),
          fetchRepositories().catch(() => [] as RepositoryItem[]),
        ])
        setIsOnline(Boolean(h && h.status === 'healthy'))
        if (repos && repos.length > 0) {
          setRepositories(repos)
          setActiveRepoId((prev) => {
            if (!repos.find((r) => r.repository_id === prev)) {
              return repos[0].repository_id
            }
            return prev
          })
        }
      } catch {
        setIsOnline(false)
      }
    }
    init()

    const interval = setInterval(async () => {
      try {
        const h = await fetchHealth()
        setIsOnline(h.status === 'healthy')
      } catch {
        setIsOnline(false)
      }
    }, 10000)
    return () => clearInterval(interval)
  }, [])

  const activeRepo =
    repositories.find((r) => r.repository_id === activeRepoId) ||
    (repositories.length > 0 ? repositories[0] : null)

  const handleRepoAdded = (newRepo: RepositoryItem) => {
    setRepositories((prev) => [newRepo, ...prev.filter((r) => r.repository_id !== newRepo.repository_id)])
    setActiveRepoId(newRepo.repository_id)
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#F8FAFC] text-slate-900 font-sans">
      {/* SaaS Collapsible Sidebar */}
      <Sidebar
        currentView={currentView}
        onSelectView={setCurrentView}
        isCollapsed={isCollapsed}
        onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
        isOnline={isOnline}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Compact Header */}
        <Header
          currentView={currentView}
          repositories={repositories}
          activeRepoId={activeRepoId}
          onSelectRepo={setActiveRepoId}
          isOnline={isOnline}
        />

        {/* View Container */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 lg:p-10">
          {currentView === 'overview' && (
            <OverviewView
              repositories={repositories}
              activeRepo={activeRepo}
              onNavigate={setCurrentView}
            />
          )}

          {currentView === 'repositories' && (
            <RepositoriesView
              repositories={repositories}
              activeRepoId={activeRepoId}
              onSelectRepo={setActiveRepoId}
              onRepoAdded={handleRepoAdded}
              onNavigate={setCurrentView}
            />
          )}

          {currentView === 'analysis' && (
            <ChangeAnalysisView
              activeRepo={activeRepo}
              onNavigate={setCurrentView}
            />
          )}

          {currentView === 'explorer' && (
            <ExplorerView activeRepo={activeRepo} />
          )}

          {currentView === 'cicd' && (
            <CicdView activeRepo={activeRepo} />
          )}

          {currentView === 'gate' && (
            <PolicyGateView />
          )}

          {currentView === 'observability' && (
            <ObservabilityView />
          )}
        </main>
      </div>
    </div>
  )
}

export default App

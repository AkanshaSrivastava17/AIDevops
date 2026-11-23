import { useState, useEffect } from 'react'
import { Sidebar, type ViewId } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'

// Views
import { HomeView } from './views/HomeView'
import { AskRepoView } from './views/AskRepoView'
import { RequestsView } from './views/RequestsView'
import { FeatureBriefView } from './views/FeatureBriefView'
import { DecisionLogView } from './views/DecisionLogView'
import { TasksView } from './views/TasksView'
import { PipelinesView } from './views/PipelinesView'
import { InsightsView } from './views/InsightsView'
import { AdminView } from './views/AdminView'
import { ExplorerView } from './views/ExplorerView'

// API & Types
import {
  fetchHealth,
  fetchRepositories,
  fetchProjects,
  fetchPersonas,
  switchPersona,
  fetchRequests,
  fetchTasks,
  fetchPipelines,
  getActivePersonaId,
  setActivePersonaId
} from './services/api'
import type {
  DemoPersona,
  Project,
  FeatureRequest,
  Task,
  PipelineRun,
  RepositoryItem
} from './types/api'

export function App() {
  const [currentView, setCurrentView] = useState<ViewId>('home')
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isOnline, setIsOnline] = useState(true)

  // Platform State
  const [projects, setProjects] = useState<Project[]>([])
  const [activeProjectId, setActiveProjectId] = useState<string>('proj-platform-core')
  const [repositories, setRepositories] = useState<RepositoryItem[]>([])
  const [activeRepoId, setActiveRepoId] = useState<string>('netbox')

  // Auth & Demo Personas (Section 4 & 10.4)
  const [personas, setPersonas] = useState<DemoPersona[]>([])
  const [activePersona, setActivePersona] = useState<DemoPersona | null>(null)

  // Active Lifecycle Context
  const [activeRequestId, setActiveRequestId] = useState<string>('req-hr-101')
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [requests, setRequests] = useState<FeatureRequest[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [pipelines, setPipelines] = useState<PipelineRun[]>([])

  // Initial Load
  useEffect(() => {
    const initApp = async () => {
      try {
        const [h, repos, projs, pers] = await Promise.all([
          fetchHealth().catch(() => null),
          fetchRepositories().catch(() => []),
          fetchProjects().catch(() => []),
          fetchPersonas().catch(() => []),
        ])

        setIsOnline(Boolean(h && h.status === 'healthy'))

        if (repos && repos.length > 0) {
          setRepositories(repos)
        }

        if (projs && projs.length > 0) {
          setProjects(projs)
          setActiveProjectId(projs[0].id)
        }

        if (pers && pers.length > 0) {
          setPersonas(pers)
          const currentId = getActivePersonaId()
          const matched = pers.find((p) => p.id === currentId) || pers[2] // default to tech_lead
          setActivePersona(matched)
        }
      } catch (err) {
        console.error('Initialization error', err)
        setIsOnline(false)
      }
    }
    initApp()

    // Periodic Health Beacon
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

  // Load project-specific data (Requests, Tasks, Pipelines)
  useEffect(() => {
    if (activeProjectId) {
      loadProjectData()
    }
  }, [activeProjectId, activeRepoId])

  const loadProjectData = async () => {
    try {
      const [reqs, tsk, pl] = await Promise.all([
        fetchRequests(activeProjectId).catch(() => []),
        fetchTasks().catch(() => []),
        fetchPipelines({ repoId: activeRepoId }).catch(() => []),
      ])
      setRequests(reqs)
      setTasks(tsk)
      setPipelines(pl)

      if (reqs.length > 0 && !activeRequestId) {
        setActiveRequestId(reqs[0].id)
      }
    } catch (err) {
      console.error('Failed to load project data', err)
    }
  }

  // Persona Switch Handler
  const handleSwitchPersona = async (personaId: string) => {
    try {
      await switchPersona(personaId)
      setActivePersonaId(personaId)
      const matched = personas.find((p) => p.id === personaId)
      if (matched) {
        setActivePersona(matched)
      }
      // Refresh current view data under new identity
      loadProjectData()
    } catch (err) {
      console.error('Failed to switch persona', err)
    }
  }

  // Cross-view navigation helper
  const handleNavigate = (view: ViewId, param?: string) => {
    if (view === 'brief' && param) {
      setActiveRequestId(param)
    }
    if (view === 'tasks' && param) {
      setSelectedTaskId(param)
    }
    setCurrentView(view)
  }

  const activeRepo =
    repositories.find((r) => r.repository_id === activeRepoId) ||
    (repositories.length > 0 ? repositories[0] : null)

  return (
    <div className="flex h-screen overflow-hidden bg-[#F8FAFC] text-slate-900 font-sans">
      {/* 8-Stage Lifecycle Navigation Sidebar */}
      <Sidebar
        currentView={currentView}
        onSelectView={setCurrentView}
        isCollapsed={isCollapsed}
        onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
        isOnline={isOnline}
        activeRequestId={activeRequestId}
      />

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Global SaaS Header with Project & Repo Selectors and Demo Role Switcher */}
        <Header
          currentView={currentView}
          projects={projects}
          activeProjectId={activeProjectId}
          onSelectProject={setActiveProjectId}
          repositories={repositories}
          activeRepoId={activeRepoId}
          onSelectRepo={setActiveRepoId}
          isOnline={isOnline}
          personas={personas}
          activePersona={activePersona}
          onSwitchPersona={handleSwitchPersona}
        />

        {/* View Body */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          {/* 1. Home / Executive & Developer Dashboard */}
          {(currentView === 'home' || currentView === 'overview') && (
            <HomeView
              onNavigate={handleNavigate}
              activePersona={activePersona}
              activeProject={projects.find((p) => p.id === activeProjectId) || null}
              requests={requests}
              tasks={tasks}
              pipelines={pipelines}
              onOpenContextPack={(taskId) => handleNavigate('tasks', taskId)}
            />
          )}

          {/* 2. Ask the Repo (Cited Q&A) */}
          {currentView === 'ask' && (
            <AskRepoView
              activeRepoId={activeRepoId}
              activeProjectId={activeProjectId}
              activePersona={activePersona}
            />
          )}

          {/* 3. Repo Code Explorer */}
          {currentView === 'explorer' && (
            <ExplorerView activeRepo={activeRepo} />
          )}

          {/* 4. Feature Requests & AI Clarity Assistant */}
          {(currentView === 'requests' || currentView === 'analysis') && (
            <RequestsView
              activeProjectId={activeProjectId}
              activeRepoId={activeRepoId}
              activePersona={activePersona}
              onOpenBrief={(reqId) => handleNavigate('brief', reqId)}
            />
          )}

          {/* 5. Feature Brief & Impact Analysis */}
          {currentView === 'brief' && (
            <FeatureBriefView
              requestId={activeRequestId}
              activePersona={activePersona}
              onTasksCreated={() => {
                loadProjectData()
                setCurrentView('tasks')
              }}
              onNavigateToDecisions={() => setCurrentView('decisions')}
            />
          )}

          {/* 6. Architectural Decision Log (ADRs) */}
          {currentView === 'decisions' && (
            <DecisionLogView
              activeProjectId={activeProjectId}
              activePersona={activePersona}
              onOpenBrief={(reqId) => handleNavigate('brief', reqId)}
            />
          )}

          {/* 7. My Tasks & Pre-PR Diff Check */}
          {currentView === 'tasks' && (
            <TasksView
              activeProjectId={activeProjectId}
              activePersona={activePersona}
              onOpenBrief={(reqId) => handleNavigate('brief', reqId)}
              selectedTaskId={selectedTaskId}
            />
          )}

          {/* 8. CI/CD Pipelines & Policy Gates */}
          {(currentView === 'pipelines' || currentView === 'cicd' || currentView === 'gate') && (
            <PipelinesView
              activeRepoId={activeRepoId}
              activePersona={activePersona}
            />
          )}

          {/* 9. Value Dashboard & Retrospectives */}
          {currentView === 'insights' && (
            <InsightsView
              activeProjectId={activeProjectId}
              activePersona={activePersona}
            />
          )}

          {/* 10. Admin & Governance */}
          {(currentView === 'admin' || currentView === 'repositories' || currentView === 'observability') && (
            <AdminView activePersona={activePersona} />
          )}
        </main>
      </div>
    </div>
  )
}
export default App

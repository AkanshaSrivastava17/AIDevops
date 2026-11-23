import React from 'react'
import {
  Sparkles,
  CheckSquare,
  TrendingUp,
  MessageSquareText,
  FileCode2,
  ArrowRight,
  Clock
} from 'lucide-react'
import type { ViewId } from '../components/layout/Sidebar'
import type { DemoPersona, Project, FeatureRequest, Task, PipelineRun } from '../types/api'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

interface HomeViewProps {
  onNavigate: (view: ViewId, param?: string) => void
  activePersona: DemoPersona | null
  activeProject: Project | null
  requests: FeatureRequest[]
  tasks: Task[]
  pipelines: PipelineRun[]
  onOpenContextPack?: (taskId: string) => void
}

export const HomeView: React.FC<HomeViewProps> = ({
  onNavigate,
  activePersona,
  activeProject,
  requests,
  tasks,
  pipelines,
  onOpenContextPack,
}) => {
  const role = activePersona?.role || 'tech_lead'

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-2xl p-6 sm:p-8 shadow-xl relative overflow-hidden border border-slate-800">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold mb-3 border border-indigo-400/30">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Engineering Intelligence • {activeProject?.name || 'Platform Core'}</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Welcome back, {activePersona ? activePersona.name : 'Engineer'}
          </h2>
          <p className="mt-2 text-sm text-slate-300 leading-relaxed">
            {role === 'junior_developer' &&
              'Access repository ground-truth, explore task context packs, and run Pre-PR diff checks before raising pull requests.'}
            {role === 'tech_lead' &&
              'Synthesize and approve Feature Briefs, review architectural decisions, inspect Pre-PR scope drift, and verify pipeline gates.'}
            {role === 'product_owner' &&
              'Log feature requests with AI Clarity Assistant, review impact analysis and test recommendations, and track feature cycle times.'}
            {role === 'qa_engineer' &&
              'Review recommended-test coverage, inspect gate evaluation snapshots, audit candidate tests, and record verifiable overrides.'}
            {role === 'engineering_manager' &&
              'Track the 4 Core Value questions, evaluate planning effort reduction, and audit escaped defects across all feature releases.'}
            {role === 'admin' &&
              'Manage repository indexing, configure GitHub webhooks, audit RBAC permissions, and inspect system telemetry.'}
          </p>

          <div className="flex flex-wrap items-center gap-3 mt-5">
            <Button
              variant="primary"
              size="sm"
              icon={<MessageSquareText className="w-4 h-4" />}
              onClick={() => onNavigate('ask')}
            >
              Ask the Repo
            </Button>
            <Button
              variant="secondary"
              size="sm"
              icon={<FileCode2 className="w-4 h-4" />}
              onClick={() => onNavigate('requests')}
            >
              Feature Requests ({requests.length})
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-slate-300 hover:text-white"
              icon={<TrendingUp className="w-4 h-4" />}
              onClick={() => onNavigate('insights')}
            >
              Value Dashboard
            </Button>
          </div>
        </div>

        {/* Ambient background decoration */}
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-radial from-indigo-500/10 to-transparent pointer-events-none" />
      </div>

      {/* Role-Specific Dashboard Perspectives (Section 8.1) */}
      {role === 'junior_developer' && (
        <JuniorDevSection
          tasks={tasks}
          onNavigate={onNavigate}
          onOpenContextPack={onOpenContextPack}
        />
      )}

      {role === 'tech_lead' && (
        <TechLeadSection
          onNavigate={onNavigate}
        />
      )}

      {role === 'product_owner' && (
        <ProductOwnerSection
          onNavigate={onNavigate}
        />
      )}

      {role === 'qa_engineer' && (
        <QAEngineerSection
          onNavigate={onNavigate}
        />
      )}

      {role === 'engineering_manager' && (
        <EngineeringManagerSection
          onNavigate={onNavigate}
        />
      )}

      {role === 'admin' && (
        <AdminSection
          onNavigate={onNavigate}
        />
      )}

      {/* Quick Access Lifecycle Grid */}
      <div>
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3">
          Engineering Memory Lifecycle (8 Stages)
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card
            hoverable
            className="p-4 cursor-pointer"
            onClick={() => onNavigate('ask')}
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center font-bold">
                1
              </div>
              <div>
                <h4 className="text-xs font-semibold text-slate-900">Learn</h4>
                <p className="text-[11px] text-slate-500">Ask the Repo Cited Q&A</p>
              </div>
            </div>
          </Card>

          <Card
            hoverable
            className="p-4 cursor-pointer"
            onClick={() => onNavigate('requests')}
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
                2
              </div>
              <div>
                <h4 className="text-xs font-semibold text-slate-900">Plan</h4>
                <p className="text-[11px] text-slate-500">Log Request & Feature Brief</p>
              </div>
            </div>
          </Card>

          <Card
            hoverable
            className="p-4 cursor-pointer"
            onClick={() => onNavigate('tasks')}
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
                3
              </div>
              <div>
                <h4 className="text-xs font-semibold text-slate-900">Build</h4>
                <p className="text-[11px] text-slate-500">Context Packs & Pre-PR Diff</p>
              </div>
            </div>
          </Card>

          <Card
            hoverable
            className="p-4 cursor-pointer"
            onClick={() => onNavigate('pipelines')}
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center font-bold">
                4
              </div>
              <div>
                <h4 className="text-xs font-semibold text-slate-900">Verify</h4>
                <p className="text-[11px] text-slate-500">CI/CD Gate & Test Coverage ({pipelines.length} runs)</p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// 1. Junior Developer Perspective
// ---------------------------------------------------------------------------

const JuniorDevSection: React.FC<{
  tasks: Task[]
  onNavigate: (view: ViewId, param?: string) => void
  onOpenContextPack?: (taskId: string) => void
}> = ({ tasks, onNavigate, onOpenContextPack }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <CheckSquare className="w-4 h-4 text-emerald-600" />
            <span>My Assigned Tasks</span>
          </h3>
          <Button variant="ghost" size="sm" onClick={() => onNavigate('tasks')}>
            View All ({tasks.length})
          </Button>
        </div>

        <div className="space-y-3">
          {tasks.slice(0, 3).map((task) => (
            <div
              key={task.id}
              className="p-4 rounded-xl bg-white border border-slate-200 hover:border-indigo-300 shadow-2xs transition-all flex items-start justify-between gap-4"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                    {task.task_key}
                  </span>
                  <Badge variant={task.status === 'Done' ? 'success' : task.status === 'In Progress' ? 'brand' : 'neutral'} size="sm">
                    {task.status}
                  </Badge>
                  <span className="text-[11px] text-slate-400 font-mono">comp: {task.component}</span>
                </div>
                <h4 className="text-sm font-semibold text-slate-900">{task.title}</h4>
                <p className="text-xs text-slate-500 line-clamp-1">{task.description}</p>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onOpenContextPack ? onOpenContextPack(task.id) : onNavigate('tasks')}
              >
                Context Pack
              </Button>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-500" />
          <span>Quick Ask Prompts</span>
        </h3>
        <div className="space-y-2">
          {[
            'Where is the VRF model defined in NetBox?',
            'What were the most frequent bugs in IPAM tenancy?',
            'Show me the regression test suite for interface containment',
          ].map((prompt, i) => (
            <button
              key={i}
              type="button"
              onClick={() => onNavigate('ask')}
              className="w-full text-left p-3 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-xs text-slate-700 hover:text-indigo-600 transition-colors flex items-center justify-between"
            >
              <span className="truncate pr-2">{prompt}</span>
              <ArrowRight className="w-3.5 h-3.5 shrink-0 text-slate-400" />
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// 2. Tech Lead Perspective
// ---------------------------------------------------------------------------

const TechLeadSection: React.FC<{
  onNavigate: (view: ViewId, param?: string) => void
}> = ({ onNavigate }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card className="p-5 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase text-slate-400">Feature Planning</span>
          <Badge variant="brand" size="sm">Action Required</Badge>
        </div>
        <div>
          <h4 className="text-base font-bold text-slate-900">VRF IP Containment Validation</h4>
          <p className="text-xs text-slate-500 mt-1">Request HR-101 • Approved Brief v1</p>
        </div>
        <p className="text-xs text-slate-600 line-clamp-2">
          Decomposed into 3 tasks with dedicated IPAM service-layer architecture.
        </p>
        <Button
          variant="secondary"
          size="sm"
          className="w-full"
          onClick={() => onNavigate('brief', 'req-hr-101')}
        >
          Inspect Feature Brief
        </Button>
      </Card>

      <Card className="p-5 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase text-slate-400">Architectural Decisions</span>
          <Badge variant="success" size="sm">Active</Badge>
        </div>
        <div>
          <h4 className="text-base font-bold text-slate-900">DEC-018: Service Layer vs Model Clean</h4>
          <p className="text-xs text-slate-500 mt-1">Prevents recurring transaction deadlocks in bulk API syncs</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Clock className="w-3.5 h-3.5" />
          <span>Decided by Marcus Vance</span>
        </div>
        <Button
          variant="secondary"
          size="sm"
          className="w-full"
          onClick={() => onNavigate('decisions')}
        >
          View Decision Log
        </Button>
      </Card>

      <Card className="p-5 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase text-slate-400">CI/CD Gate Health</span>
          <Badge variant="success" size="sm">
            Approved
          </Badge>
        </div>
        <div>
          <h4 className="text-base font-bold text-slate-900">Latest Gate Snapshot</h4>
          <p className="text-xs text-slate-500 mt-1">Commit a7f92b4c • NetBox develop</p>
        </div>
        <p className="text-xs text-slate-600">
          14 recommended tests matched • 0 blocking regressions.
        </p>
        <Button
          variant="secondary"
          size="sm"
          className="w-full"
          onClick={() => onNavigate('pipelines')}
        >
          Inspect Gate & Coverage
        </Button>
      </Card>
    </div>
  )
}

// ---------------------------------------------------------------------------
// 3. Product Owner Perspective
// ---------------------------------------------------------------------------

const ProductOwnerSection: React.FC<{
  onNavigate: (view: ViewId, param?: string) => void
}> = ({ onNavigate }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card className="p-5 space-y-3">
        <span className="text-xs font-bold uppercase text-slate-400">AI Clarity Assistant</span>
        <div className="text-2xl font-bold text-indigo-600">88.5%</div>
        <p className="text-xs text-slate-500">Average clarity score on logged feature criteria</p>
        <Button variant="secondary" size="sm" onClick={() => onNavigate('requests')}>
          Log New Request
        </Button>
      </Card>

      <Card className="p-5 space-y-3">
        <span className="text-xs font-bold uppercase text-slate-400">Scope Discipline</span>
        <div className="text-2xl font-bold text-emerald-600">35.0%</div>
        <p className="text-xs text-slate-500">Unplanned scope reduction after Brief synthesis</p>
        <Button variant="secondary" size="sm" onClick={() => onNavigate('insights')}>
          View Retrospectives
        </Button>
      </Card>

      <Card className="p-5 space-y-3">
        <span className="text-xs font-bold uppercase text-slate-400">Planning Velocity</span>
        <div className="text-2xl font-bold text-slate-900">1.8 hrs</div>
        <p className="text-xs text-slate-500">Average time from request logged to approved brief</p>
        <Button variant="secondary" size="sm" onClick={() => onNavigate('requests')}>
          Manage Backlog
        </Button>
      </Card>
    </div>
  )
}

// ---------------------------------------------------------------------------
// 4. QA Engineer Perspective
// ---------------------------------------------------------------------------

const QAEngineerSection: React.FC<{
  onNavigate: (view: ViewId, param?: string) => void
}> = ({ onNavigate }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card className="p-5 space-y-3">
        <span className="text-xs font-bold uppercase text-slate-400">Recommended Test Share</span>
        <div className="text-2xl font-bold text-indigo-600">3.1%</div>
        <p className="text-xs text-slate-500">14 of 450 tests executed while catching 91.8% of regressions</p>
        <Button variant="secondary" size="sm" onClick={() => onNavigate('pipelines')}>
          Inspect Coverage
        </Button>
      </Card>

      <Card className="p-5 space-y-3">
        <span className="text-xs font-bold uppercase text-slate-400">Test Precision</span>
        <div className="text-2xl font-bold text-emerald-600">80.2%</div>
        <p className="text-xs text-slate-500">Targeted test relevance accuracy against real historical churn</p>
        <Button variant="secondary" size="sm" onClick={() => onNavigate('insights')}>
          View Test Metrics
        </Button>
      </Card>

      <Card className="p-5 space-y-3">
        <span className="text-xs font-bold uppercase text-slate-400">Gate Verification</span>
        <div className="text-2xl font-bold text-slate-900">100%</div>
        <p className="text-xs text-slate-500">Gates backed by reproducible commit snapshots</p>
        <Button variant="secondary" size="sm" onClick={() => onNavigate('pipelines')}>
          Gate Controls
        </Button>
      </Card>
    </div>
  )
}

// ---------------------------------------------------------------------------
// 5. Engineering Manager Perspective
// ---------------------------------------------------------------------------

const EngineeringManagerSection: React.FC<{
  onNavigate: (view: ViewId, param?: string) => void
}> = ({ onNavigate }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card hoverable className="p-4 space-y-2 cursor-pointer" onClick={() => onNavigate('insights')}>
        <span className="text-[10px] font-bold uppercase text-slate-400">Q1. Early Risk</span>
        <div className="text-xl font-bold text-emerald-600">92% Flagged</div>
        <p className="text-[11px] text-slate-500">Affected components flagged before coding</p>
      </Card>
      <Card hoverable className="p-4 space-y-2 cursor-pointer" onClick={() => onNavigate('insights')}>
        <span className="text-[10px] font-bold uppercase text-slate-400">Q2. Testing Efficiency</span>
        <div className="text-xl font-bold text-indigo-600">96.9% Reduced</div>
        <p className="text-[11px] text-slate-500">Fewer regression tests executed per PR</p>
      </Card>
      <Card hoverable className="p-4 space-y-2 cursor-pointer" onClick={() => onNavigate('insights')}>
        <span className="text-[10px] font-bold uppercase text-slate-400">Q3. Effort Reduction</span>
        <div className="text-xl font-bold text-purple-600">2.4h Average</div>
        <p className="text-[11px] text-slate-500">Average feature planning cycle time</p>
      </Card>
      <Card hoverable className="p-4 space-y-2 cursor-pointer" onClick={() => onNavigate('insights')}>
        <span className="text-[10px] font-bold uppercase text-slate-400">Q4. Release Quality</span>
        <div className="text-xl font-bold text-sky-600">0 Escaped</div>
        <p className="text-[11px] text-slate-500">Production rollbacks in monitored repos</p>
      </Card>
    </div>
  )
}

// ---------------------------------------------------------------------------
// 6. Admin Perspective
// ---------------------------------------------------------------------------

const AdminSection: React.FC<{
  onNavigate: (view: ViewId, param?: string) => void
}> = ({ onNavigate }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card className="p-5 space-y-3">
        <span className="text-xs font-bold uppercase text-slate-400">Repositories</span>
        <div className="text-2xl font-bold text-slate-900">3 Connected</div>
        <p className="text-xs text-slate-500">NetBox (IPAM), PyCalculator, FastAPI Gateway</p>
        <Button variant="secondary" size="sm" onClick={() => onNavigate('admin')}>
          Manage Repositories
        </Button>
      </Card>

      <Card className="p-5 space-y-3">
        <span className="text-xs font-bold uppercase text-slate-400">Audit Trail</span>
        <div className="text-2xl font-bold text-indigo-600">Append-Only</div>
        <p className="text-xs text-slate-500">Full tamper-evident governance ledger</p>
        <Button variant="secondary" size="sm" onClick={() => onNavigate('admin')}>
          Inspect Audit Logs
        </Button>
      </Card>

      <Card className="p-5 space-y-3">
        <span className="text-xs font-bold uppercase text-slate-400">CI/CD Webhooks</span>
        <div className="text-2xl font-bold text-emerald-600">Active</div>
        <p className="text-xs text-slate-500">GitHub push & pull_request event delivery</p>
        <Button variant="secondary" size="sm" onClick={() => onNavigate('admin')}>
          Webhook Settings
        </Button>
      </Card>
    </div>
  )
}

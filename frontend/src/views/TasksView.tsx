import React, { useState, useEffect } from 'react'
import {
  Search,
  GitPullRequest,
  AlertTriangle,
  CheckCircle2
} from 'lucide-react'
import type { Task, TaskContextPack, PrePRCheckResult, DemoPersona } from '../types/api'
import {
  fetchTasks,
  updateTaskStatus,
  fetchTaskContextPack,
  runPrePrCheck
} from '../services/api'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Drawer } from '../components/ui/Drawer'
import { Modal } from '../components/ui/Modal'

interface TasksViewProps {
  activeProjectId: string
  activePersona: DemoPersona | null
  onOpenBrief?: (requestId: string) => void
  selectedTaskId?: string | null
}

const COLUMNS: Array<{ id: Task['status']; label: string; color: string }> = [
  { id: 'Todo', label: 'To Do', color: 'bg-slate-100 text-slate-700' },
  { id: 'In Progress', label: 'In Progress', color: 'bg-indigo-50 text-indigo-700 border-indigo-200' },
  { id: 'In Review', label: 'In Review', color: 'bg-amber-50 text-amber-800 border-amber-200' },
  { id: 'Testing', label: 'Testing', color: 'bg-purple-50 text-purple-700 border-purple-200' },
  { id: 'Done', label: 'Done', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
]

export const TasksView: React.FC<TasksViewProps> = ({
  activeProjectId,
  activePersona,
  onOpenBrief,
  selectedTaskId,
}) => {
  const [tasks, setTasks] = useState<Task[]>([])
  const [filterMode, setFilterMode] = useState<'my' | 'team'>('team')
  const [searchQuery, setSearchQuery] = useState('')

  // Context Pack Drawer State
  const [activeTask, setActiveTask] = useState<Task | null>(null)
  const [contextPack, setContextPack] = useState<TaskContextPack | null>(null)
  const [isLoadingPack, setIsLoadingPack] = useState(false)

  // Pre-PR Check Modal State
  const [isPrePrOpen, setIsPrePrOpen] = useState(false)
  const [prePrTask, setPrePrTask] = useState<Task | null>(null)
  const [diffText, setDiffText] = useState('')
  const [isCheckingPrePr, setIsCheckingPrePr] = useState(false)
  const [prePrResult, setPrePrResult] = useState<PrePRCheckResult | null>(null)

  useEffect(() => {
    loadTasks()
  }, [activeProjectId])

  useEffect(() => {
    if (selectedTaskId && tasks.length > 0) {
      const t = tasks.find((item) => item.id === selectedTaskId || item.task_key === selectedTaskId)
      if (t) handleOpenContextPack(t)
    }
  }, [selectedTaskId, tasks])

  const loadTasks = async () => {
    try {
      const data = await fetchTasks()
      setTasks(data)
    } catch (err) {
      console.error('Failed to load tasks', err)
    }
  }

  // Open Context Pack Drawer (Section 7.5 & 8.5)
  const handleOpenContextPack = async (task: Task) => {
    setActiveTask(task)
    setIsLoadingPack(true)
    try {
      const pack = await fetchTaskContextPack(task.id)
      setContextPack(pack)
    } catch (err) {
      console.error('Failed to load task context pack', err)
    } finally {
      setIsLoadingPack(false)
    }
  }

  // Open Pre-PR Check Modal
  const handleOpenPrePr = (task: Task) => {
    setPrePrTask(task)
    // Pre-populate with realistic mock git diff for developer convenience
    setDiffText(`diff --git a/netbox/ipam/validators.py b/netbox/ipam/validators.py
new file mode 100644
index 0000000..f8a29b1
--- /dev/null
+++ b/netbox/ipam/validators.py
@@ -0,0 +1,18 @@
+from django.core.exceptions import ValidationError
+import netaddr
+
+class VrfContainmentValidator:
+    """Validates that interface IP falls strictly inside tenant VRF CIDR bounds."""
+    def __init__(self, vrf):
+        self.vrf = vrf
+
+    def validate_ip_containment(self, ip_address):
+        ip = netaddr.IPNetwork(ip_address)
+        for prefix in self.vrf.prefixes.all():
+            if ip in netaddr.IPNetwork(prefix.prefix):
+                return True
+        raise ValidationError(f"IP {ip_address} violates VRF {self.vrf.name} containment boundary.")
`)
    setPrePrResult(null)
    setIsPrePrOpen(true)
  }

  const handleRunPrePr = async () => {
    if (!prePrTask || !diffText.trim() || isCheckingPrePr) return
    setIsCheckingPrePr(true)
    try {
      const res = await runPrePrCheck(prePrTask.id, diffText, prePrTask.branch_name)
      setPrePrResult(res)
    } catch (err) {
      console.error('Pre-PR check failed', err)
    } finally {
      setIsCheckingPrePr(false)
    }
  }

  const handleStatusChange = async (taskId: string, newStatus: Task['status']) => {
    try {
      await updateTaskStatus(taskId, newStatus)
      await loadTasks()
    } catch (err) {
      console.error('Failed to update task status', err)
    }
  }

  const filteredTasks = tasks.filter((t) => {
    const matchesFilter = filterMode === 'team' || t.assignee_id === activePersona?.id
    const matchesSearch =
      t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.task_key.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.component.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesFilter && matchesSearch
  })

  return (
    <div className="space-y-6">
      {/* Top Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1 max-w-lg">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search tasks, TASK-xxx, components..."
              className="w-full bg-white border border-slate-200 pl-9 pr-3 py-2 rounded-lg text-xs text-slate-900 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex items-center p-1 bg-slate-100 rounded-lg text-xs font-medium">
            <button
              type="button"
              onClick={() => setFilterMode('my')}
              className={`px-3 py-1 rounded-md transition-colors ${
                filterMode === 'my' ? 'bg-white text-slate-900 shadow-2xs font-bold' : 'text-slate-600'
              }`}
            >
              My Tasks
            </button>
            <button
              type="button"
              onClick={() => setFilterMode('team')}
              className={`px-3 py-1 rounded-md transition-colors ${
                filterMode === 'team' ? 'bg-white text-slate-900 shadow-2xs font-bold' : 'text-slate-600'
              }`}
            >
              Team Board
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="brand" size="sm">
            Grounded in Feature Briefs
          </Badge>
        </div>
      </div>

      {/* Kanban Board Columns (Section 8.5) */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 overflow-x-auto min-h-[580px]">
        {COLUMNS.map((col) => {
          const colTasks = filteredTasks.filter((t) => t.status === col.id)

          return (
            <div
              key={col.id}
              className="bg-slate-50/80 border border-slate-200/90 rounded-xl p-3 flex flex-col h-full min-w-[220px]"
            >
              {/* Column Header */}
              <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-200 text-xs">
                <span className="font-bold text-slate-800">{col.label}</span>
                <span className="font-mono text-[11px] font-bold text-slate-500 bg-white border border-slate-200 px-1.5 py-0.2 rounded-full">
                  {colTasks.length}
                </span>
              </div>

              {/* Tasks in Column */}
              <div className="space-y-3 flex-1 overflow-y-auto">
                {colTasks.map((task) => (
                  <div
                    key={task.id}
                    onClick={() => handleOpenContextPack(task)}
                    className="p-3.5 bg-white border border-slate-200 hover:border-indigo-300 rounded-lg shadow-2xs space-y-2.5 cursor-pointer transition-all hover:shadow-xs group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[11px] font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.2 rounded">
                        {task.task_key}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400">
                        comp: <strong>{task.component}</strong>
                      </span>
                    </div>

                    <h4 className="text-xs font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors line-clamp-2">
                      {task.title}
                    </h4>

                    {task.depends_on && task.depends_on.length > 0 && (
                      <div className="text-[10px] text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded">
                        Depends on: {task.depends_on.join(', ')}
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-[11px] text-slate-500">
                      <div className="flex items-center gap-1.5">
                        <div className="w-5 h-5 rounded-full bg-slate-200 text-slate-700 font-bold flex items-center justify-center text-[9px]">
                          {task.assignee_name ? task.assignee_name.slice(0, 2).toUpperCase() : 'MV'}
                        </div>
                        <span className="truncate max-w-[80px]">
                          {task.assignee_name?.split(' ')[0] || 'Unassigned'}
                        </span>
                      </div>

                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleOpenPrePr(task)
                          }}
                          className="text-[10px] font-bold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2 py-0.5 rounded"
                          title="Run Pre-PR Diff Check"
                        >
                          Pre-PR
                        </button>
                      </div>
                    </div>
                  </div>
                ))}

                {colTasks.length === 0 && (
                  <div className="text-center py-8 text-slate-400 text-xs italic">
                    No tasks
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Task Context Pack Drawer (Section 7.5 & 8.5) */}
      <Drawer
        isOpen={Boolean(activeTask)}
        onClose={() => setActiveTask(null)}
        title={activeTask ? `${activeTask.task_key}: Context Pack` : 'Task Context Pack'}
        subtitle={`Ground-truth developer guidance for component '${activeTask?.component}'`}
        width="xl"
        footer={
          activeTask && (
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">Status:</span>
                <select
                  value={activeTask.status}
                  onChange={(e) => handleStatusChange(activeTask.id, e.target.value as any)}
                  className="bg-white border border-slate-200 px-2 py-1 rounded text-xs font-semibold text-slate-800"
                >
                  <option value="Todo">Todo</option>
                  <option value="In Progress">In Progress</option>
                  <option value="In Review">In Review</option>
                  <option value="Testing">Testing</option>
                  <option value="Done">Done</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                {onOpenBrief && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      onOpenBrief(activeTask.request_id)
                      setActiveTask(null)
                    }}
                  >
                    Feature Brief
                  </Button>
                )}
                <Button
                  variant="primary"
                  size="sm"
                  icon={<GitPullRequest className="w-3.5 h-3.5" />}
                  onClick={() => handleOpenPrePr(activeTask)}
                >
                  Run Pre-PR Check
                </Button>
              </div>
            </div>
          )
        }
      >
        {isLoadingPack ? (
          <div className="py-12 text-center text-slate-400 text-xs">
            Synthesizing task context pack from engineering memory...
          </div>
        ) : contextPack ? (
          <div className="space-y-4 text-xs">
            {/* Task Summary */}
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
              <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider">
                Task Objective
              </span>
              <p className="text-slate-800 font-medium">{contextPack.task_description}</p>
            </div>

            {/* Acceptance Criteria */}
            {contextPack.acceptance_criteria.length > 0 && (
              <div className="space-y-1.5">
                <span className="font-bold text-slate-900 block">Acceptance Criteria</span>
                <div className="space-y-1">
                  {contextPack.acceptance_criteria.map((crit, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-slate-700 bg-white p-2 rounded border border-slate-200">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                      <span>{crit}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Relevant Files to Touch */}
            <div className="space-y-1.5">
              <span className="font-bold text-slate-900 block">Key Component Files to Touch</span>
              <div className="space-y-1">
                {contextPack.relevant_files.map((file, i) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-slate-50 rounded border border-slate-200 font-mono text-[11px]">
                    <span className="text-slate-800">{file.path}</span>
                    {file.similarity && (
                      <span className="text-emerald-700 font-bold bg-emerald-50 px-1.5 py-0.2 rounded">
                        {(file.similarity * 100).toFixed(0)}% Match
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Known Pitfalls to Avoid */}
            {contextPack.known_pitfalls.length > 0 && (
              <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg space-y-1.5">
                <span className="text-[10px] font-bold uppercase text-amber-800 tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Known Architectural Pitfalls
                </span>
                <ul className="space-y-1 text-amber-900">
                  {contextPack.known_pitfalls.map((pitfall, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="font-bold">•</span>
                      <span>{pitfall}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Architectural Decisions to Respect */}
            {contextPack.related_decisions.length > 0 && (
              <div className="space-y-1.5">
                <span className="font-bold text-slate-900 block">Architectural Decisions to Respect (ADRs)</span>
                <div className="space-y-2">
                  {contextPack.related_decisions.map((dec) => (
                    <div key={dec.id} className="p-2.5 bg-purple-50/50 border border-purple-200 rounded-lg space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-purple-900">{dec.id.toUpperCase()}</span>
                        <Badge variant="brand" size="sm">Active Consensus</Badge>
                      </div>
                      <p className="font-semibold text-slate-900">{dec.title}</p>
                      <p className="text-slate-600 text-[11px]">{dec.rationale}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommended Tests */}
            {contextPack.recommended_tests.length > 0 && (
              <div className="space-y-1.5">
                <span className="font-bold text-slate-900 block">Recommended Regression Test Suites</span>
                <div className="space-y-1">
                  {contextPack.recommended_tests.map((t, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-sky-50/60 border border-sky-100 rounded text-[11px]">
                      <span className="font-mono text-slate-800">{t.test_file}</span>
                      <span className="text-sky-800 font-bold">{((t.score || 0.85) * 100).toFixed(0)}% Relevance</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Suggested Reviewers */}
            {contextPack.suggested_reviewers.length > 0 && (
              <div className="space-y-1.5">
                <span className="font-bold text-slate-900 block">Suggested Reviewers</span>
                <div className="grid grid-cols-2 gap-2">
                  {contextPack.suggested_reviewers.map((rev) => (
                    <div key={rev.id} className="p-2 bg-white border border-slate-200 rounded-lg flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-slate-200 font-bold flex items-center justify-center text-[10px]">
                        {rev.avatar}
                      </div>
                      <div className="truncate">
                        <p className="font-semibold text-slate-800 truncate">{rev.name}</p>
                        <p className="text-[10px] text-slate-400">{rev.prior_modifications_count} prior PRs</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}
      </Drawer>

      {/* Pre-PR Check Modal (Section 7.5 & 8.5) */}
      <Modal
        isOpen={isPrePrOpen}
        onClose={() => setIsPrePrOpen(false)}
        title={`Pre-PR Check for ${prePrTask?.task_key || 'Task'}`}
        subtitle="Verifies proposed diff against planned components and flags unexpected scope drift before merge."
        maxWidth="2xl"
        footer={
          <div className="flex items-center justify-between w-full">
            <span className="text-[11px] text-slate-400">
              Compares against approved brief components
            </span>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={() => setIsPrePrOpen(false)}>
                Close
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleRunPrePr}
                loading={isCheckingPrePr}
                disabled={!diffText.trim()}
              >
                Run Verification
              </Button>
            </div>
          </div>
        }
      >
        <div className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-800 mb-1">
              Git Diff Text or Changed Files List
            </label>
            <textarea
              rows={8}
              value={diffText}
              onChange={(e) => setDiffText(e.target.value)}
              placeholder="Paste git diff --cached or changed files..."
              className="w-full font-mono bg-slate-900 text-slate-100 p-3 rounded-lg text-[11px] focus:outline-none"
            />
          </div>

          {/* Pre-PR Verification Results */}
          {prePrResult && (
            <div
              className={`p-4 rounded-xl border space-y-3 animate-in fade-in duration-150 ${
                prePrResult.check_passed
                  ? 'bg-emerald-50/50 border-emerald-200'
                  : 'bg-amber-50/60 border-amber-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {prePrResult.check_passed ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-amber-600" />
                  )}
                  <span className="font-bold text-sm text-slate-900">
                    {prePrResult.check_passed ? 'Pre-PR Check Passed' : 'Scope Drift / Warnings Detected'}
                  </span>
                </div>
                <Badge variant={prePrResult.check_passed ? 'success' : 'warning'} size="sm">
                  {prePrResult.check_passed ? 'Ready for PR' : 'Review Required'}
                </Badge>
              </div>

              <p className="text-slate-700 text-xs">{prePrResult.summary}</p>

              <div className="grid grid-cols-2 gap-3 text-[11px]">
                <div className="p-2.5 bg-white rounded border border-slate-200">
                  <span className="font-bold text-slate-700 block mb-1">Planned Components Touched</span>
                  <div className="flex flex-wrap gap-1">
                    {prePrResult.planned_components.map((c) => (
                      <span key={c} className="font-mono bg-slate-100 px-1.5 py-0.2 rounded text-slate-800">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-2.5 bg-white rounded border border-slate-200">
                  <span className="font-bold text-amber-800 block mb-1">Unplanned Scope Drift</span>
                  {prePrResult.unplanned_components.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {prePrResult.unplanned_components.map((c) => (
                        <span key={c} className="font-mono bg-rose-50 text-rose-800 border border-rose-200 px-1.5 py-0.2 rounded">
                          ⚠ {c}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-slate-400 italic">None (0 scope drift)</span>
                  )}
                </div>
              </div>

              {/* Missing Recommended Tests */}
              {prePrResult.missing_recommended_tests.length > 0 && (
                <div className="p-2.5 bg-white rounded border border-amber-200 text-[11px] space-y-1">
                  <span className="font-bold text-amber-900 block">Missing Recommended Tests</span>
                  {prePrResult.missing_recommended_tests.map((t) => (
                    <div key={t} className="font-mono text-amber-800">
                      • {t}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}

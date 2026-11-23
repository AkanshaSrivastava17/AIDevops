import React, { useState, useEffect } from 'react'
import {
  FileCode2,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  TestTube,
  CheckSquare,
  Layers,
  Sparkles,
  Download,
  Presentation,
  GitCompare,
  Plus
} from 'lucide-react'
import type { BriefVersion, BriefDiff, DemoPersona } from '../types/api'
import {
  fetchBriefVersions,
  generateBrief,
  approveBrief,
  createTasksFromBrief,
  fetchBriefDiff,
  exportBriefMarkdown,
  createDecision
} from '../services/api'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'
import { Drawer } from '../components/ui/Drawer'
import { RoleGuard } from '../components/ui/RoleGuard'
import { VersionDiff } from '../components/ui/VersionDiff'

interface FeatureBriefViewProps {
  requestId: string
  activePersona: DemoPersona | null
  onTasksCreated?: () => void
  onNavigateToDecisions?: () => void
}

export const FeatureBriefView: React.FC<FeatureBriefViewProps> = ({
  requestId,
  activePersona,
  onTasksCreated,
  onNavigateToDecisions,
}) => {
  const [briefs, setBriefs] = useState<BriefVersion[]>([])
  const [selectedVersionIndex, setSelectedVersionIndex] = useState<number>(0)
  const [isLoading, setIsLoading] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isApproving, setIsApproving] = useState(false)
  const [isCreatingTasks, setIsCreatingTasks] = useState(false)
  const [isDiffOpen, setIsDiffOpen] = useState(false)
  const [diffData, setDiffData] = useState<BriefDiff | null>(null)
  const [isMeetingMode, setIsMeetingMode] = useState(false)

  // Decision Modal
  const [isDecisionModalOpen, setIsDecisionModalOpen] = useState(false)
  const [decisionTitle, setDecisionTitle] = useState('')
  const [decisionRationale, setDecisionRationale] = useState('')

  useEffect(() => {
    if (requestId) {
      loadBriefs()
    }
  }, [requestId])

  const loadBriefs = async () => {
    setIsLoading(true)
    try {
      const data = await fetchBriefVersions(requestId)
      setBriefs(data)
      if (data.length > 0) {
        setSelectedVersionIndex(0)
      }
    } catch (err) {
      console.error('Failed to load briefs', err)
    } finally {
      setIsLoading(false)
    }
  }

  const currentBrief = briefs[selectedVersionIndex] || null

  // 1. Generate / Synthesize Brief
  const handleRegenerateBrief = async () => {
    setIsGenerating(true)
    try {
      await generateBrief(requestId)
      await loadBriefs()
    } catch (err) {
      console.error('Failed to generate brief', err)
    } finally {
      setIsGenerating(false)
    }
  }

  // 2. Approve Brief
  const handleApproveBrief = async () => {
    if (!currentBrief || isApproving) return
    setIsApproving(true)
    try {
      await approveBrief(currentBrief.id)
      await loadBriefs()
    } catch (err) {
      console.error('Failed to approve brief', err)
    } finally {
      setIsApproving(false)
    }
  }

  // 3. Decompose & Create Tasks
  const handleCreateTasks = async () => {
    if (!currentBrief || isCreatingTasks) return
    setIsCreatingTasks(true)
    try {
      await createTasksFromBrief(requestId, currentBrief.id)
      onTasksCreated?.()
    } catch (err) {
      console.error('Failed to create tasks', err)
    } finally {
      setIsCreatingTasks(false)
    }
  }

  // 4. Record Decision
  const handleOpenDecisionModal = () => {
    if (currentBrief) {
      const recOption = currentBrief.options.find((o) => o.name === currentBrief.recommended_option) || currentBrief.options[0]
      setDecisionTitle(`Architectural Decision for ${requestId}`)
      setDecisionRationale(
        recOption
          ? `Adopted ${recOption.name}: ${recOption.description}. Tradeoffs: ${recOption.cons?.join(', ')}`
          : 'Grounded in Feature Brief analysis'
      )
    }
    setIsDecisionModalOpen(true)
  }

  const handleRecordDecision = async () => {
    if (!currentBrief) return
    try {
      await createDecision({
        title: decisionTitle,
        context: currentBrief.restated_requirement,
        rationale: decisionRationale,
        request_id: requestId,
        brief_version_id: currentBrief.id,
      })
      setIsDecisionModalOpen(false)
      onNavigateToDecisions?.()
    } catch (err) {
      console.error('Failed to record decision', err)
    }
  }

  // 5. Version Diff
  const handleOpenDiff = async () => {
    if (briefs.length < 2) return
    try {
      const vA = briefs[1].version
      const vB = briefs[0].version
      const diff = await fetchBriefDiff(requestId, vA, vB)
      setDiffData(diff)
      setIsDiffOpen(true)
    } catch (err) {
      console.error('Failed to fetch brief diff', err)
    }
  }

  // 6. Export Markdown
  const handleExportMarkdown = async () => {
    try {
      const md = await exportBriefMarkdown(requestId)
      const blob = new Blob([md], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `FeatureBrief-${requestId}.md`
      a.click()
    } catch (err) {
      console.error('Failed to export brief', err)
    }
  }

  if (isLoading && briefs.length === 0) {
    return (
      <div className="p-12 text-center text-slate-400 text-xs">
        Synthesizing Feature Brief from repository ground-truth...
      </div>
    )
  }

  if (!currentBrief) {
    return (
      <Card className="p-8 text-center space-y-4">
        <FileCode2 className="w-12 h-12 text-indigo-400 mx-auto" />
        <h3 className="text-base font-bold text-slate-900">No Feature Brief Generated Yet</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          Synthesize an evidence-backed Feature Brief for {requestId}. History-RAG will compute affected components, identify historical precedents, evaluate tradeoffs, and propose tasks.
        </p>
        <Button
          variant="primary"
          size="md"
          loading={isGenerating}
          onClick={handleRegenerateBrief}
          icon={<Sparkles className="w-4 h-4" />}
        >
          Synthesize Feature Brief
        </Button>
      </Card>
    )
  }

  const role = activePersona?.role || 'junior_developer'
  const isApproved = currentBrief.status === 'Approved'

  return (
    <div className="space-y-6">
      {/* 1. Flagship Summary Bar (Section 8.4) */}
      <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-2xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                {requestId.replace('req-', 'HR-').toUpperCase()}
              </span>
              <Badge variant={isApproved ? 'success' : 'brand'} size="sm">
                Brief v{currentBrief.version} • {currentBrief.status}
              </Badge>
              {currentBrief.approved_by && (
                <span className="text-[11px] text-slate-500">
                  Approved by <strong>{currentBrief.approved_by}</strong>
                </span>
              )}
            </div>
            <h2 className="text-lg font-bold text-slate-900">
              {currentBrief.restated_requirement || 'Feature Brief Specification'}
            </h2>
          </div>

          {/* Action Toolbar */}
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            {briefs.length > 1 && (
              <Button
                variant="secondary"
                size="sm"
                icon={<GitCompare className="w-3.5 h-3.5" />}
                onClick={handleOpenDiff}
              >
                Compare Diff
              </Button>
            )}

            <Button
              variant="secondary"
              size="sm"
              icon={<Presentation className="w-3.5 h-3.5 text-indigo-600" />}
              onClick={() => setIsMeetingMode(!isMeetingMode)}
            >
              {isMeetingMode ? 'Exit Meeting Mode' : 'Meeting Mode'}
            </Button>

            <Button
              variant="secondary"
              size="sm"
              icon={<Download className="w-3.5 h-3.5" />}
              onClick={handleExportMarkdown}
            >
              Export
            </Button>

            {/* RoleGuard: Tech Lead can approve */}
            {!isApproved && (
              <RoleGuard
                currentRole={role}
                allowedRoles={['tech_lead', 'admin']}
                disableOnly
                tooltip="Only Tech Leads or Admins can formally approve Feature Briefs"
              >
                <Button
                  variant="primary"
                  size="sm"
                  loading={isApproving}
                  onClick={handleApproveBrief}
                  icon={<CheckCircle2 className="w-3.5 h-3.5" />}
                >
                  Approve Brief
                </Button>
              </RoleGuard>
            )}

            <RoleGuard
              currentRole={role}
              allowedRoles={['tech_lead', 'product_owner', 'admin']}
              disableOnly
            >
              <Button
                variant="secondary"
                size="sm"
                loading={isCreatingTasks}
                onClick={handleCreateTasks}
                icon={<Plus className="w-3.5 h-3.5" />}
              >
                Decompose Tasks
              </Button>
            </RoleGuard>

            <RoleGuard
              currentRole={role}
              allowedRoles={['tech_lead', 'admin']}
              disableOnly
            >
              <Button
                variant="secondary"
                size="sm"
                onClick={handleOpenDecisionModal}
                icon={<ShieldCheck className="w-3.5 h-3.5 text-purple-600" />}
              >
                Record ADR
              </Button>
            </RoleGuard>
          </div>
        </div>

        {/* Evidence Strength Meter Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-100 text-xs">
          <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
            <span className="text-slate-500">Component Identification:</span>
            <Badge variant="success" size="sm">
              {currentBrief.evidence_strength?.component_identification || 'High'} Strength
            </Badge>
          </div>
          <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
            <span className="text-slate-500">Historical Precedents:</span>
            <Badge variant="success" size="sm">
              {currentBrief.evidence_strength?.historical_precedent || 'High'} Confidence
            </Badge>
          </div>
          <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
            <span className="text-slate-500">Test Recommendation Score:</span>
            <Badge variant="brand" size="sm">
              {((currentBrief.overall_confidence || 0.91) * 100).toFixed(0)}% Precision
            </Badge>
          </div>
        </div>
      </div>

      {/* 2. Impact Analysis Table with Evidence Drill-down */}
      <Card className="p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-600" />
              <span>Affected Components & Impact Scoring</span>
            </h3>
            <p className="text-xs text-slate-500">
              Computed across semantic relevance, static dependency graph, and historical co-change churn.
            </p>
          </div>
          <Badge variant={currentBrief.overall_impact_level === 'HIGH' ? 'error' : 'warning'} size="sm">
            {currentBrief.overall_impact_level} Impact
          </Badge>
        </div>

        <div className="divide-y divide-slate-100 text-xs">
          {currentBrief.affected_components.map((comp) => (
            <div key={comp.component} className="py-3 flex items-start justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-slate-900 text-sm">
                    {comp.component}
                  </span>
                  <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded text-[11px]">
                    Impact Score: {(comp.score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="text-slate-600">
                  {comp.reasons?.map((r, i) => (
                    <div key={i} className="flex items-center gap-1.5 text-[11px] text-slate-500">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </div>

              <Button
                variant="ghost"
                size="sm"
                onClick={() => {}}
                className="text-indigo-600 hover:text-indigo-800 text-[11px]"
              >
                Inspect Drilldown
              </Button>
            </div>
          ))}
        </div>
      </Card>

      {/* 3. Implementation Options & Tradeoffs */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-600" />
          <span>Implementation Options & Architecture Tradeoffs</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {currentBrief.options.map((opt, i) => {
            const isRecommended = opt.name === currentBrief.recommended_option || (opt as any).is_recommended
            return (
              <div
                key={i}
                className={`p-5 rounded-xl border transition-all space-y-3 text-xs ${
                  isRecommended
                    ? 'bg-indigo-50/40 border-indigo-300 shadow-2xs'
                    : 'bg-white border-slate-200'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <h4 className="font-bold text-slate-900 text-sm">{opt.name}</h4>
                  {isRecommended && (
                    <Badge variant="brand" size="sm">
                      Recommended
                    </Badge>
                  )}
                </div>

                <p className="text-slate-600 leading-relaxed">{opt.description}</p>

                <div className="grid grid-cols-2 gap-2 text-[11px] py-2 border-y border-slate-100">
                  <div>
                    <span className="text-slate-400">Estimated Effort:</span>{' '}
                    <strong className="text-slate-700">{opt.effort}</strong>
                  </div>
                  <div>
                    <span className="text-slate-400">Risk Level:</span>{' '}
                    <strong className="text-slate-700">{opt.risk}</strong>
                  </div>
                </div>

                <div className="space-y-2">
                  {opt.pros && opt.pros.length > 0 && (
                    <div>
                      <span className="font-bold text-emerald-700 text-[10px] uppercase tracking-wider block mb-1">
                        Architectural Advantages
                      </span>
                      <ul className="space-y-1">
                        {opt.pros.map((p, idx) => (
                          <li key={idx} className="flex items-center gap-1.5 text-slate-700">
                            <span className="text-emerald-500 font-bold">✓</span>
                            <span>{p}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {opt.cons && opt.cons.length > 0 && (
                    <div>
                      <span className="font-bold text-amber-700 text-[10px] uppercase tracking-wider block mb-1">
                        Tradeoffs Accepted
                      </span>
                      <ul className="space-y-1">
                        {opt.cons.map((c, idx) => (
                          <li key={idx} className="flex items-center gap-1.5 text-slate-600">
                            <span className="text-amber-500 font-bold">⚠</span>
                            <span>{c}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* 4. Task Decomposition & Proposed Work */}
      <Card className="p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <CheckSquare className="w-4 h-4 text-emerald-600" />
              <span>Proposed Task Decomposition</span>
            </h3>
            <p className="text-xs text-slate-500">
              Concrete architectural slices ready for developer assignment with Context Packs.
            </p>
          </div>
          <span className="text-xs font-mono font-bold text-slate-500">
            {currentBrief.proposed_tasks.length} Slices
          </span>
        </div>

        <div className="space-y-2 text-xs">
          {currentBrief.proposed_tasks.map((task, i) => (
            <div
              key={i}
              className="p-3 bg-slate-50 rounded-lg border border-slate-200/80 flex items-center justify-between gap-4"
            >
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-indigo-700 bg-white px-2 py-0.5 rounded border border-slate-200">
                    {task.task_key || `TASK-${101 + i}`}
                  </span>
                  <span className="font-semibold text-slate-900">{task.title}</span>
                  <span className="text-[10px] font-mono text-slate-400">comp: {task.component}</span>
                </div>
                <p className="text-slate-500 text-[11px]">{task.description}</p>
              </div>
              <span className="text-[11px] font-medium text-slate-500 bg-white px-2 py-1 rounded border border-slate-200 shrink-0">
                Suggested Role: {task.suggested_assignee_role?.replace('_', ' ') || 'Developer'}
              </span>
            </div>
          ))}
        </div>
      </Card>

      {/* 5. Recommended Tests & Review Flags */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Recommended Tests */}
        <Card className="p-5 space-y-3 text-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h4 className="font-bold text-slate-900 flex items-center gap-2">
              <TestTube className="w-4 h-4 text-sky-500" />
              <span>Recommended Regression Tests</span>
            </h4>
            <span className="text-[11px] font-mono text-slate-400">
              {currentBrief.recommended_tests.length} Suites
            </span>
          </div>

          <div className="space-y-2">
            {currentBrief.recommended_tests.map((test, i) => (
              <div
                key={i}
                className="p-2.5 bg-sky-50/50 border border-sky-100 rounded-lg flex items-center justify-between"
              >
                <div>
                  <span className="font-mono font-bold text-slate-800">{test.test_file}</span>
                  {test.test_name && (
                    <span className="font-mono text-slate-500 text-[11px] block">
                      ::{test.test_name}
                    </span>
                  )}
                </div>
                <span className="text-emerald-700 font-bold bg-emerald-50 px-1.5 py-0.5 rounded text-[11px]">
                  {((test.score || 0.94) * 100).toFixed(0)}% Relevance
                </span>
              </div>
            ))}
          </div>
        </Card>

        {/* Review Flags */}
        <Card className="p-5 space-y-3 text-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h4 className="font-bold text-slate-900 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <span>Architectural Review Flags</span>
            </h4>
            <span className="text-[11px] font-mono text-slate-400">
              {currentBrief.review_flags.length} Warnings
            </span>
          </div>

          <div className="space-y-2">
            {currentBrief.review_flags.map((flag, i) => (
              <div
                key={i}
                className="p-2.5 bg-amber-50/60 border border-amber-200/70 rounded-lg space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-amber-900">{flag.category || 'Warning'}</span>
                  <span className="text-[10px] font-mono text-amber-700 bg-amber-100 px-1.5 py-0.2 rounded">
                    {flag.target}
                  </span>
                </div>
                <p className="text-amber-800 text-[11px]">{flag.message}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* 6. Reproducibility & Audit Metadata Panel (Section 7.2) */}
      <Card className="p-4 bg-slate-50 border border-slate-200 text-xs space-y-2">
        <span className="font-bold text-slate-400 text-[10px] uppercase tracking-wider block">
          Reproducibility Metadata & Ground-Truth Stamp
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px]">
          <div>
            <span className="text-slate-500 block">Commit SHA</span>
            <span className="font-mono font-bold text-slate-800">
              {currentBrief.reproducibility?.repository_commit_sha || 'a7f92b4c'}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Snapshot ID</span>
            <span className="font-mono text-slate-700">
              {currentBrief.reproducibility?.index_snapshot_id || 'snap-netbox'}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Scoring Engine</span>
            <span className="font-mono text-slate-700">
              {currentBrief.reproducibility?.scoring_version || 'v2.2-enterprise'}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Timestamp</span>
            <span className="font-mono text-slate-700">
              {currentBrief.generated_at ? new Date(currentBrief.generated_at).toLocaleString() : 'Recent'}
            </span>
          </div>
        </div>
      </Card>

      {/* Diff Drawer */}
      <Drawer
        isOpen={isDiffOpen}
        onClose={() => setIsDiffOpen(false)}
        title="Brief Version Comparison"
        subtitle={`Comparing architectural evolution for ${requestId}`}
        width="xl"
      >
        {diffData ? (
          <VersionDiff diff={diffData} />
        ) : (
          <div className="text-center py-12 text-slate-400">Loading version diff...</div>
        )}
      </Drawer>

      {/* Record ADR Modal */}
      <Modal
        isOpen={isDecisionModalOpen}
        onClose={() => setIsDecisionModalOpen(false)}
        title="Record Architectural Decision (ADR)"
        subtitle="Links this decision record directly to the Feature Brief and affected code paths."
        maxWidth="lg"
        footer={
          <div className="flex items-center justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={() => setIsDecisionModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleRecordDecision}>
              Record Decision
            </Button>
          </div>
        }
      >
        <div className="space-y-3 text-xs">
          <div>
            <label className="block font-semibold text-slate-800 mb-1">Decision Title</label>
            <input
              type="text"
              value={decisionTitle}
              onChange={(e) => setDecisionTitle(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs focus:bg-white focus:outline-none"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-800 mb-1">Architectural Rationale & Tradeoffs</label>
            <textarea
              rows={4}
              value={decisionRationale}
              onChange={(e) => setDecisionRationale(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs focus:bg-white focus:outline-none"
            />
          </div>
        </div>
      </Modal>
    </div>
  )
}

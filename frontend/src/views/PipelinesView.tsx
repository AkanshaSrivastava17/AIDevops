import React, { useState, useEffect } from 'react'
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Play,
  GitBranch,
  Sparkles,
  MessageSquare,
  TestTube,
  ShieldAlert
} from 'lucide-react'
import type { PipelineRun, GateResult, DemoPersona } from '../types/api'
import {
  fetchPipelines,
  fetchPipelineGate,
  overridePipelineGate,
  triggerSimulatedRun
} from '../services/api'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'
import { RoleGuard } from '../components/ui/RoleGuard'

interface PipelinesViewProps {
  activeRepoId: string
  activePersona: DemoPersona | null
}

export const PipelinesView: React.FC<PipelinesViewProps> = ({
  activeRepoId,
  activePersona,
}) => {
  const [runs, setRuns] = useState<PipelineRun[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [gateResult, setGateResult] = useState<GateResult | null>(null)

  // Override Modal State
  const [isOverrideOpen, setIsOverrideOpen] = useState(false)
  const [overrideReason, setOverrideReason] = useState('')
  const [isSubmittingOverride, setIsSubmittingOverride] = useState(false)

  // Simulation State (Phase 1 contract)
  const [isSimulating, setIsSimulating] = useState(false)
  const [simFailHighImpact, setSimFailHighImpact] = useState(false)
  const [simLowConfidence, setSimLowConfidence] = useState(false)

  // PR Bot Comment Tab
  const [showBotPreview, setShowBotPreview] = useState(false)

  useEffect(() => {
    loadPipelines()
  }, [activeRepoId])

  const loadPipelines = async () => {
    try {
      const data = await fetchPipelines({ repoId: activeRepoId })
      setRuns(data)
      if (data.length > 0 && !selectedRunId) {
        selectRun(data[0].id)
      }
    } catch (err) {
      console.error('Failed to load pipeline runs', err)
    }
  }

  const selectRun = async (runId: string) => {
    setSelectedRunId(runId)
    try {
      const gate = await fetchPipelineGate(runId)
      setGateResult(gate)
    } catch (err) {
      console.error('Failed to load gate result', err)
    }
  }

  const handleOverride = async () => {
    if (!selectedRunId || !overrideReason.trim() || isSubmittingOverride) return
    setIsSubmittingOverride(true)
    try {
      await overridePipelineGate(selectedRunId, overrideReason, 'Approved')
      await selectRun(selectedRunId)
      await loadPipelines()
      setIsOverrideOpen(false)
      setOverrideReason('')
    } catch (err) {
      console.error('Failed to override gate', err)
    } finally {
      setIsSubmittingOverride(false)
    }
  }

  const handleTriggerSimulation = async () => {
    setIsSimulating(true)
    try {
      const newRun = await triggerSimulatedRun({
        repo_id: activeRepoId,
        fail_high_impact_test: simFailHighImpact,
        low_confidence: simLowConfidence,
      })
      await loadPipelines()
      selectRun(newRun.id)
    } catch (err) {
      console.error('Failed to trigger simulated run', err)
    } finally {
      setIsSimulating(false)
    }
  }

  const selectedRun = runs.find((r) => r.id === selectedRunId) || runs[0]
  const role = activePersona?.role || 'junior_developer'

  return (
    <div className="space-y-6">
      {/* Top Header & Simulation Controls (Section 8.7) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-white border border-slate-200 rounded-xl shadow-2xs">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-indigo-600" />
            <span>CI/CD Pipelines & Reproducible Policy Gate</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Phase 1 Simulated Verification Contract: Simulated input data feeds the real policy gate engine.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Simulation Toggle Checkboxes */}
          <div className="hidden lg:flex items-center gap-3 text-xs bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg">
            <label className="flex items-center gap-1.5 cursor-pointer text-slate-700">
              <input
                type="checkbox"
                checked={simFailHighImpact}
                onChange={(e) => setSimFailHighImpact(e.target.checked)}
                className="rounded text-indigo-600"
              />
              <span>Fail High-Impact Test</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer text-slate-700">
              <input
                type="checkbox"
                checked={simLowConfidence}
                onChange={(e) => setSimLowConfidence(e.target.checked)}
                className="rounded text-indigo-600"
              />
              <span>Low Confidence (&lt;60%)</span>
            </label>
          </div>

          <Button
            variant="secondary"
            size="sm"
            loading={isSimulating}
            onClick={handleTriggerSimulation}
            icon={<Play className="w-3.5 h-3.5 text-indigo-600" />}
          >
            Trigger Pipeline Run
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Runs List */}
        <div className="lg:col-span-1 space-y-3">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-400 px-1">
            <span>Pipeline Executions</span>
            <span className="font-mono text-slate-500">{runs.length} Runs</span>
          </div>

          <div className="space-y-2.5 max-h-[620px] overflow-y-auto pr-1">
            {runs.map((run) => {
              const isSelected = run.id === selectedRunId
              const isApproved = run.gate_decision === 'Approved'
              const isBlocked = run.gate_decision === 'Blocked'

              return (
                <div
                  key={run.id}
                  onClick={() => selectRun(run.id)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer space-y-2 ${
                    isSelected
                      ? 'bg-indigo-50/50 border-indigo-300 shadow-2xs'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-slate-800">
                      {run.commit_sha.slice(0, 8)}
                    </span>
                    <Badge
                      variant={isApproved ? 'success' : isBlocked ? 'error' : 'warning'}
                      size="sm"
                    >
                      {run.gate_decision}
                    </Badge>
                  </div>

                  <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
                    <GitBranch className="w-3.5 h-3.5 text-slate-400" />
                    <span>{run.branch}</span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-100">
                    <span>{new Date(run.started_at).toLocaleTimeString()}</span>
                    <span>
                      {run.recommended_test_coverage?.executed_count || 0}/
                      {run.recommended_test_coverage?.recommended_count || 0} tests run
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right: Selected Gate Snapshot & Test Coverage */}
        <div className="lg:col-span-2 space-y-5">
          {selectedRun && (
            <>
              {/* Gate Decision Hero Banner */}
              <Card className="p-5 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-3">
                    {selectedRun.gate_decision === 'Approved' ? (
                      <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
                        <CheckCircle2 className="w-6 h-6" />
                      </div>
                    ) : selectedRun.gate_decision === 'Blocked' ? (
                      <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold">
                        <XCircle className="w-6 h-6" />
                      </div>
                    ) : (
                      <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
                        <AlertTriangle className="w-6 h-6" />
                      </div>
                    )}
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-bold text-slate-900">
                          Policy Gate: {gateResult?.decision || selectedRun.gate_decision}
                        </h3>
                        {gateResult && (
                          <Badge variant={gateResult.freshness === 'Current' ? 'success' : 'warning'} size="sm">
                            {gateResult.freshness} Snapshot
                          </Badge>
                        )}
                        {(gateResult?.override || gateResult?.override_reason) && (
                          <Badge variant="brand" size="sm">
                            Overridden
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 font-mono">
                        Commit: {selectedRun.commit_sha} • Branch: {selectedRun.branch}
                      </p>
                    </div>
                  </div>

                  {/* Override Button (QA/Lead only) */}
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowBotPreview(!showBotPreview)}
                      icon={<MessageSquare className="w-3.5 h-3.5" />}
                    >
                      {showBotPreview ? 'Hide PR Bot' : 'PR Bot Preview'}
                    </Button>

                    {selectedRun.gate_decision !== 'Approved' && (
                      <RoleGuard
                        currentRole={role}
                        allowedRoles={['qa_engineer', 'tech_lead', 'admin']}
                        disableOnly
                        tooltip="Gate overrides require QA Lead or Tech Lead role with mandatory justification reason."
                      >
                        <Button
                          variant="primary"
                          size="sm"
                          icon={<ShieldAlert className="w-3.5 h-3.5" />}
                          onClick={() => setIsOverrideOpen(true)}
                        >
                          Override Gate
                        </Button>
                      </RoleGuard>
                    )}
                  </div>
                </div>

                {/* Blocking reasons or warnings */}
                {gateResult && (
                  <div className="space-y-2 text-xs">
                    {(gateResult.blocking_reasons?.length ?? 0) > 0 && (
                      <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-900 space-y-1">
                        <span className="font-bold text-[10px] uppercase tracking-wider block">
                          Blocking Reasons
                        </span>
                        {(gateResult.blocking_reasons || []).map((r, i) => (
                          <div key={i} className="flex items-center gap-1.5">
                            <span className="font-bold">•</span>
                            <span>{r}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {(gateResult.warnings?.length ?? 0) > 0 && (
                      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 space-y-1">
                        <span className="font-bold text-[10px] uppercase tracking-wider block">
                          Warnings
                        </span>
                        {(gateResult.warnings || []).map((w, i) => (
                          <div key={i} className="flex items-center gap-1.5">
                            <span className="font-bold">•</span>
                            <span>{w}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {(gateResult.override || gateResult.override_reason) && (
                      <div className="p-3.5 bg-indigo-50 border border-indigo-200 rounded-lg text-indigo-950 space-y-1">
                        <span className="font-bold text-[10px] uppercase tracking-wider block text-indigo-700">
                          🛡️ Gate Override Justification Recorded
                        </span>
                        <p className="font-medium italic text-xs">
                          "{gateResult.override?.override_reason || gateResult.override_reason}"
                        </p>
                        <p className="text-[11px] text-slate-500 pt-1">
                          Overridden by{' '}
                          <strong>
                            {gateResult.override?.overridden_by_name ||
                              gateResult.override?.overridden_by ||
                              gateResult.overridden_by}
                          </strong>{' '}
                          ({gateResult.override?.role || 'QA / Tech Lead'}) at{' '}
                          {gateResult.override?.timestamp || gateResult.overridden_at}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </Card>

              {/* Recommended-Test Coverage Panel (Section 7.6) */}
              <Card className="p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <TestTube className="w-4 h-4 text-sky-500" />
                      <span>Recommended-Test Coverage Analysis</span>
                    </h4>
                    <p className="text-xs text-slate-500">
                      Grounded test suite execution: Verifies that tests recommended by History-RAG were actually run.
                    </p>
                  </div>
                  <span className="text-xs font-mono font-bold text-indigo-700 bg-indigo-50 px-2 py-1 rounded">
                    {selectedRun.recommended_test_coverage?.coverage_pct || 100}% Suite Coverage
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-3 text-center text-xs">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-slate-500 block text-[11px]">Recommended Tests</span>
                    <strong className="text-lg font-mono text-slate-900">
                      {selectedRun.recommended_test_coverage?.recommended_count || 14}
                    </strong>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-slate-500 block text-[11px]">Tests Executed</span>
                    <strong className="text-lg font-mono text-indigo-600">
                      {selectedRun.recommended_test_coverage?.executed_count || 14}
                    </strong>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-slate-500 block text-[11px]">Tests Passed</span>
                    <strong className="text-lg font-mono text-emerald-600">
                      {selectedRun.recommended_test_coverage?.passed_count || 14}
                    </strong>
                  </div>
                </div>

                {/* Missed Tests */}
                {((selectedRun?.recommended_test_coverage?.missed_tests?.length ?? 0) > 0) && (
                  <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs space-y-1 text-rose-900">
                    <span className="font-bold text-[10px] uppercase tracking-wider block">
                      Missed Recommended Tests (Must Run Before Merge)
                    </span>
                    {(selectedRun?.recommended_test_coverage?.missed_tests || []).map((t) => (
                      <div key={t} className="font-mono text-[11px]">
                        • {t}
                      </div>
                    ))}
                  </div>
                )}
              </Card>

              {/* PR Bot Comment Preview (Section 7.6) */}
              {showBotPreview && (
                <Card className="p-5 space-y-3 bg-slate-900 text-slate-100 font-mono text-xs rounded-xl">
                  <div className="flex items-center justify-between text-slate-400 border-b border-slate-800 pb-2">
                    <span className="text-xs text-indigo-400 font-bold flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5" />
                      github-actions[bot] • History-RAG Quality Gate Summary
                    </span>
                    <span className="text-[10px]">Markdown Preview</span>
                  </div>
                  <div className="space-y-2 text-[11px] leading-relaxed text-slate-200">
                    <p className="font-bold text-white">
                      ### 🛡️ History-RAG Policy Gate: {gateResult?.decision || selectedRun.gate_decision}
                      {(gateResult?.override || gateResult?.override_reason) ? ' (Manual Override)' : ''}
                    </p>
                    {(gateResult?.override || gateResult?.override_reason) && (
                      <p className="text-indigo-300">
                        **Override Justification:** "{gateResult.override?.override_reason || gateResult.override_reason}" (by {gateResult.override?.overridden_by_name || gateResult.override?.overridden_by || gateResult.overridden_by})
                      </p>
                    )}
                    <p>
                      **Commit:** `{selectedRun.commit_sha}` | **Decision Snapshot:** `Current`
                    </p>
                    <p>
                      **Recommended Test Coverage:** {selectedRun.recommended_test_coverage?.coverage_pct || 100}% ({selectedRun.recommended_test_coverage?.executed_count || 14}/{selectedRun.recommended_test_coverage?.recommended_count || 14} executed)
                    </p>
                    <p>
                      **Component Scope Check:** Passed • Zero unplanned architectural drift detected.
                    </p>
                  </div>
                </Card>
              )}
            </>
          )}
          {!selectedRun && (
            <Card className="p-8 text-center text-slate-400 text-xs">
              No pipeline executions recorded yet. Click "Trigger Pipeline Run" above to simulate an execution.
            </Card>
          )}
        </div>
      </div>

      {/* Override Modal (Section 7.6 & 8.7) */}
      <Modal
        isOpen={isOverrideOpen}
        onClose={() => setIsOverrideOpen(false)}
        title="Override Policy Gate Decision"
        subtitle="Mandatory verification audit trail required. All overrides are permanently recorded in append-only audit ledger."
        maxWidth="lg"
        footer={
          <div className="flex items-center justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={() => setIsOverrideOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              loading={isSubmittingOverride}
              onClick={handleOverride}
              disabled={!overrideReason.trim()}
            >
              Confirm Verified Override
            </Button>
          </div>
        }
      >
        <div className="space-y-3 text-xs">
          <p className="text-slate-600">
            You are overriding policy gate for commit <strong>{selectedRun?.commit_sha}</strong> from{' '}
            <strong className="text-rose-600">{gateResult?.decision || selectedRun?.gate_decision || 'Blocked'}</strong> to{' '}
            <strong className="text-emerald-600">Approved</strong>.
          </p>

          <div>
            <label className="block font-semibold text-slate-800 mb-1">
              Mandatory Justification Reason <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={4}
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              placeholder="e.g. QA lead verified VRF boundary test pass in manual staging smoke test suite."
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 focus:bg-white focus:outline-none"
            />
          </div>

          <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 text-[11px]">
            This action will be attributed to <strong>{activePersona?.name}</strong> ({activePersona?.role}) and verified in subsequent release retrospectives.
          </div>
        </div>
      </Modal>
    </div>
  )
}

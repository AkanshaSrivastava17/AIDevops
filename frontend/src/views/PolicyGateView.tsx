import React, { useState, useEffect } from 'react'
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  Bot,
} from 'lucide-react'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { evaluateGate, fetchDeployments, triggerRollback } from '../services/api'
import type {
  GateEvaluationResponse,
  DeploymentLedgerResponse,
  RollbackResponse,
} from '../types/api'

export const PolicyGateView: React.FC = () => {
  const [impactLevel, setImpactLevel] = useState<'LOW' | 'MEDIUM' | 'HIGH'>('LOW')
  const [confidence, setConfidence] = useState(0.9)
  const [testsPassed, setTestsPassed] = useState(15)
  const [testsFailed, setTestsFailed] = useState(0)
  const [blockOnHighImpact, setBlockOnHighImpact] = useState(true)
  const [loadingGate, setLoadingGate] = useState(false)
  const [gateResult, setGateResult] = useState<GateEvaluationResponse | null>(null)
  const [gateError, setGateError] = useState<string | null>(null)

  // Deployments ledger & Rollback
  const [ledger, setLedger] = useState<DeploymentLedgerResponse | null>(null)
  const [rollbackConfirm, setRollbackConfirm] = useState(false)
  const [loadingRollback, setLoadingRollback] = useState(false)
  const [rollbackResult, setRollbackResult] = useState<RollbackResponse | null>(null)
  const [rollbackError, setRollbackError] = useState<string | null>(null)

  const loadLedger = async () => {
    try {
      const data = await fetchDeployments()
      setLedger(data)
    } catch {
      // Ignored if initial ledger empty
    }
  }

  useEffect(() => {
    loadLedger()
  }, [])

  const handleEvaluateGate = async (e?: React.FormEvent | React.MouseEvent) => {
    if (e && typeof e.preventDefault === 'function') {
      e.preventDefault()
    }
    setLoadingGate(true)
    setGateError(null)
    try {
      const data = await evaluateGate({
        change_analysis: {
          impact_level: impactLevel,
          confidence: confidence,
          affected_components: [{ component: 'core', score: 0.85 }],
        },
        test_results: {
          status: testsFailed === 0 ? 'PASS' : 'FAIL',
          total: testsPassed + testsFailed,
          passed: testsPassed,
          failed: testsFailed,
          skipped: 0,
        },
        qa_health_status: { status: 'healthy' },
        block_on_high_impact: blockOnHighImpact,
        min_confidence: 0.6,
      })
      setGateResult(data)
    } catch (err: unknown) {
      setGateError(err instanceof Error ? err.message : 'Gate evaluation failed')
    } finally {
      setLoadingGate(false)
    }
  }

  const handleTriggerRollback = async () => {
    setLoadingRollback(true)
    setRollbackError(null)
    try {
      const res = await triggerRollback({
        failed_image: 'historyrag:candidate',
        reason: 'QA health check regression detected',
        environment: 'qa',
      })
      setRollbackResult(res)
      setRollbackConfirm(false)
      loadLedger()
    } catch (err: unknown) {
      setRollbackError(err instanceof Error ? err.message : 'Rollback failed')
    } finally {
      setLoadingRollback(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Title */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-indigo-600" />
          CI/CD Policy Gate & Deployment Manager
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Evaluate whether proposed code changes satisfy enterprise safety gates, and manage zero-downtime rollbacks when candidate deployments fail staging health checks.
        </p>
      </div>

      {gateError && <ErrorBanner message={gateError} />}
      {rollbackError && <ErrorBanner message={rollbackError} />}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Policy Evaluation Form */}
        <div className="lg:col-span-6 space-y-6">
          <Card>
            <CardHeader
              title="Evaluate CI/CD Policy Gate"
              subtitle="Test pipeline gate decision given impact severity, test results, and QA status"
            />
            <CardContent>
              <form onSubmit={handleEvaluateGate} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-medium text-slate-700 block mb-1">
                      Change Impact Level:
                    </label>
                    <select
                      value={impactLevel}
                      onChange={(e) => setImpactLevel(e.target.value as 'LOW' | 'MEDIUM' | 'HIGH')}
                      className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-indigo-600"
                    >
                      <option value="LOW">LOW Impact</option>
                      <option value="MEDIUM">MEDIUM Impact</option>
                      <option value="HIGH">HIGH Impact</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="ai-confidence-input" className="text-xs font-medium text-slate-700 block mb-1">
                      AI Confidence: {(confidence * 100).toFixed(0)}%
                    </label>
                    <input
                      id="ai-confidence-input"
                      type="range"
                      min={0.3}
                      max={1.0}
                      step={0.05}
                      value={confidence}
                      onChange={(e) => setConfidence(Number(e.target.value))}
                      className="w-full accent-indigo-600 mt-2"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="gate-tests-passed-input" className="text-xs font-medium text-slate-700 block mb-1">
                      Tests Passed:
                    </label>
                    <input
                      id="gate-tests-passed-input"
                      type="number"
                      value={testsPassed}
                      onChange={(e) => setTestsPassed(Number(e.target.value))}
                      className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-emerald-700 font-mono font-semibold"
                    />
                  </div>

                  <div>
                    <label htmlFor="gate-tests-failed-input" className="text-xs font-medium text-slate-700 block mb-1">
                      Tests Failed:
                    </label>
                    <input
                      id="gate-tests-failed-input"
                      type="number"
                      value={testsFailed}
                      onChange={(e) => setTestsFailed(Number(e.target.value))}
                      className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-rose-700 font-mono font-semibold"
                    />
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-100">
                  <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={blockOnHighImpact}
                      onChange={(e) => setBlockOnHighImpact(e.target.checked)}
                      className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span>Strict Mode: Automatically block on HIGH impact changes</span>
                  </label>
                </div>

                <div className="pt-2">
                  <Button
                    type="submit"
                    onClick={(e) => handleEvaluateGate(e)}
                    loading={loadingGate}
                    icon={<ShieldCheck className="w-4 h-4" />}
                    className="w-full cursor-pointer"
                  >
                    Evaluate Policy Gate
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Rollback & Deployment Controls */}
          <Card>
            <CardHeader
              title="Deployment Health & Automated Rollback"
              subtitle="Current container deployment state in QA staging"
            />
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">CURRENT IMAGE</span>
                  <span className="font-semibold text-slate-800 truncate block mt-0.5">
                    {ledger?.current_deployed_image || 'historyrag:v1.0.0-stable'}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">KNOWN GOOD POINTER</span>
                  <span className="font-semibold text-emerald-700 truncate block mt-0.5">
                    {ledger?.known_good_image || 'historyrag:v1.0.0-stable'}
                  </span>
                </div>
              </div>

              {!rollbackConfirm ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setRollbackConfirm(true)}
                  icon={<RotateCcw className="w-3.5 h-3.5 text-rose-600" />}
                  className="w-full border-slate-200 text-slate-700 hover:border-rose-300 hover:text-rose-700"
                >
                  Trigger Emergency Image Rollback
                </Button>
              ) : (
                <div className="p-4 rounded-xl border border-rose-200 bg-rose-50/70 space-y-3">
                  <div className="flex items-center gap-2 text-rose-900 text-xs font-bold">
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                    <span>Confirm zero-downtime container rollback?</span>
                  </div>
                  <p className="text-[11px] text-rose-700 leading-relaxed">
                    This will immediately restore the known-good image pointer ({ledger?.known_good_image || 'historyrag:v1.0.0-stable'}) into the QA environment.
                  </p>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="danger"
                      loading={loadingRollback}
                      onClick={handleTriggerRollback}
                    >
                      Confirm Rollback
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setRollbackConfirm(false)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}

              {rollbackResult && (
                <div className="p-3 rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-800 text-xs font-mono space-y-1">
                  <div className="font-bold flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Rollback Executed: {rollbackResult.status}</span>
                  </div>
                  <p className="text-[11px]">{rollbackResult.message}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: Decision Output & Bot Review */}
        <div className="lg:col-span-6 space-y-6">
          <Card className="h-full flex flex-col">
            <CardHeader
              title="Gate Evaluation Outcome"
              subtitle="Decision computed by AdvancedCIDCGate"
            />
            <CardContent className="flex-1 space-y-5">
              {gateResult ? (
                <div className="space-y-4">
                  {/* Big Decision Banner */}
                  <div
                    className={`p-4 rounded-xl border flex items-center justify-between ${
                      gateResult.decision === 'APPROVED'
                        ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                        : gateResult.decision === 'WARNING'
                        ? 'bg-amber-50 border-amber-200 text-amber-900'
                        : 'bg-rose-50 border-rose-200 text-rose-900'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {gateResult.decision === 'APPROVED' ? (
                        <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0" />
                      ) : gateResult.decision === 'WARNING' ? (
                        <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0" />
                      ) : (
                        <XCircle className="w-6 h-6 text-rose-600 flex-shrink-0" />
                      )}
                      <div>
                        <span className="font-bold text-sm block">
                          Gate Decision: {gateResult.decision === 'APPROVED' ? 'APPROVED (Merge Safe)' : gateResult.decision === 'WARNING' ? 'WARNING (Review Required)' : 'BLOCKED'}
                        </span>
                        <span className="text-xs opacity-90">
                          {gateResult.summary || (gateResult.decision === 'APPROVED' ? 'All policy criteria satisfied' : 'Policy gate blocked merge')}
                        </span>
                      </div>
                    </div>
                    <Badge
                      variant={gateResult.decision === 'APPROVED' ? 'success' : gateResult.decision === 'WARNING' ? 'warning' : 'error'}
                      size="sm"
                    >
                      {gateResult.decision}
                    </Badge>
                  </div>

                  {/* Violations */}
                  {((gateResult.violations || gateResult.blocking_reasons || [])).length > 0 && (
                    <div className="space-y-2">
                      <span className="text-xs font-semibold text-rose-800 uppercase tracking-wider block">
                        Policy Violations ({(gateResult.violations || gateResult.blocking_reasons || []).length})
                      </span>
                      <ul className="space-y-1">
                        {(gateResult.violations || gateResult.blocking_reasons || []).map((v, i) => (
                          <li
                            key={i}
                            className="p-2 rounded bg-rose-50 text-rose-800 text-xs font-mono flex items-center gap-2"
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                            <span>{v}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Recommendations / Warnings */}
                  {((gateResult.recommendations || gateResult.warnings || [])).length > 0 && (
                    <div className="space-y-2">
                      <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider block">
                        Recommendations &amp; Warnings
                      </span>
                      <ul className="space-y-1">
                        {(gateResult.recommendations || gateResult.warnings || []).map((r, i) => (
                          <li
                            key={i}
                            className="p-2 rounded bg-slate-50 text-slate-700 text-xs flex items-center gap-2"
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Bot Comment Preview */}
                  <div className="pt-2 border-t border-slate-100">
                    <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider block mb-2 flex items-center gap-1.5">
                      <Bot className="w-3.5 h-3.5 text-indigo-600" />
                      github-actions[bot] Live PR Comment Preview
                    </span>
                    <div className="p-4 rounded-xl bg-slate-900 text-slate-200 text-xs font-mono space-y-2">
                      <p className="font-bold text-white">## 🧠 History-RAG AI Change-Impact Analysis</p>
                      <table className="w-full text-left text-xs border border-slate-800">
                        <tbody>
                          <tr className="border-b border-slate-800">
                            <td className="p-1.5 text-slate-400">Impact Level</td>
                            <td className="p-1.5 font-bold text-indigo-400">{impactLevel}</td>
                          </tr>
                          <tr className="border-b border-slate-800">
                            <td className="p-1.5 text-slate-400">AI Confidence</td>
                            <td className="p-1.5 font-bold">{(confidence * 100).toFixed(0)}%</td>
                          </tr>
                          <tr>
                            <td className="p-1.5 text-slate-400">Policy Gate Decision</td>
                            <td className="p-1.5 font-bold text-emerald-400">
                              {gateResult.decision === 'APPROVED' ? '✅ APPROVED (Merge Safe)' : '❌ BLOCKED'}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400">
                  <ShieldCheck className="w-10 h-10 text-slate-300 mb-2" />
                  <p className="text-xs font-medium text-slate-600">No active evaluation</p>
                  <p className="text-[11px] text-slate-400 mt-1 max-w-xs">
                    Select impact level and test counts on the left, then click &ldquo;Evaluate Policy Gate&rdquo;.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

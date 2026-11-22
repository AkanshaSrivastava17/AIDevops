import React, { useState, useEffect, useRef } from 'react'
import {
  Search,
  GitCommit,
  ChevronDown,
  ChevronUp,
  FileCode,
  ArrowRight,
} from 'lucide-react'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { analyzeChange } from '../services/api'
import type { AnalyzeChangeResponse, RepositoryItem } from '../types/api'
import type { ViewId } from '../components/layout/Sidebar'

interface ChangeAnalysisViewProps {
  activeRepo: RepositoryItem | null
  onNavigate: (view: ViewId) => void
}

export const ChangeAnalysisView: React.FC<ChangeAnalysisViewProps> = ({
  activeRepo,
  onNavigate,
}) => {
  const [inputTab, setInputTab] = useState<'text' | 'diff'>('text')
  const [changeText, setChangeText] = useState('')
  const [systemMode, setSystemMode] = useState('History-RAG')
  const [topKTests, setTopKTests] = useState(5)
  const [generateCandidateTests, setGenerateCandidateTests] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AnalyzeChangeResponse | null>(null)
  const [expandedEvidence, setExpandedEvidence] = useState(true)
  const resultsRef = useRef<HTMLDivElement>(null)

  // Scroll to results when analysis completes
  useEffect(() => {
    if (result && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [result])

  // Pre-load realistic sample text when repo switches
  useEffect(() => {
    if (activeRepo?.repository_id === 'pycalculator') {
      setChangeText(
        inputTab === 'text'
          ? 'In calculator.py, add a zero-division check to divide() to prevent crashes when denominator is 0.'
          : `diff --git a/calculator.py b/calculator.py
--- a/calculator.py
+++ b/calculator.py
@@ -14,5 +14,8 @@ def divide(a, b):
+    if b == 0:
+        raise ValueError("Cannot divide by zero")
     return a / b`
      )
    } else {
      setChangeText(
        inputTab === 'text'
          ? 'In netbox/ipam/models.py, validate prefix hierarchy to prevent duplicate subnet allocation across VRFs.'
          : `diff --git a/netbox/ipam/models.py b/netbox/ipam/models.py
--- a/netbox/ipam/models.py
+++ b/netbox/ipam/models.py
@@ -142,6 +142,12 @@ class Prefix(PrimaryModel):
     def clean(self):
         super().clean()
+        if self.vrf and self.prefix.version == 4:
+            overlapping = Prefix.objects.filter(vrf=self.vrf, prefix__net_contains=self.prefix)
+            if overlapping.exists():
+                raise ValidationError({'prefix': 'Prefix conflicts with existing VRF hierarchy.'})`
      )
    }
  }, [activeRepo, inputTab])

  const handleRunAnalysis = async (e?: React.FormEvent | React.MouseEvent) => {
    if (e && typeof e.preventDefault === 'function') {
      e.preventDefault()
    }
    if (!activeRepo) {
      setError('Please select an active repository first.')
      return
    }
    if (!changeText.trim()) {
      setError('Please enter a code change description or git diff.')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const data = await analyzeChange({
        repository_id: activeRepo.repository_id,
        proposed_change: changeText,
        system_mode: systemMode,
        top_k_tests: topKTests,
        generate_candidate_tests: generateCandidateTests,
      })
      setResult(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const getSeverityBadge = (level: string) => {
    switch (level) {
      case 'HIGH':
        return <Badge variant="error" dot>HIGH IMPACT (Review Required)</Badge>
      case 'MEDIUM':
        return <Badge variant="warning" dot>MEDIUM IMPACT (Tests Required)</Badge>
      default:
        return <Badge variant="success" dot>LOW IMPACT (Safe to Merge)</Badge>
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Title */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Search className="w-5 h-5 text-indigo-600" />
          Change Impact Analysis
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Understand what could break before you merge your code. History-RAG combines Tree-Sitter AST syntax trees with historical commit and issue co-changes.
        </p>
      </div>

      {error && <ErrorBanner message={error} onRetry={() => setError(null)} />}

      {/* Target Repo Banner */}
      <div className="p-4 rounded-xl bg-white border border-slate-200/90 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500 font-medium">Selected Repository:</span>
          <strong className="text-slate-900 font-semibold">{activeRepo?.name || 'None'}</strong>
          <Badge variant="brand" size="sm">
            {activeRepo?.language || 'Polyglot'}
          </Badge>
        </div>
        <Button
          size="sm"
          variant="outline"
          onClick={() => onNavigate('repositories')}
        >
          Change Repository
        </Button>
      </div>

      {/* Main Analysis Form */}
      <Card>
        <CardHeader
          title="Input Proposed Code Change"
          subtitle="Describe the scenario in plain English or paste a standard git diff patch"
        />
        <CardContent>
          <form onSubmit={handleRunAnalysis} className="space-y-4">
            {/* Input Mode Toggle */}
            <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-lg w-fit text-xs font-medium">
              <button
                type="button"
                onClick={() => setInputTab('text')}
                className={`px-3 py-1 rounded-md transition-all cursor-pointer ${
                  inputTab === 'text'
                    ? 'bg-white text-slate-900 shadow-xs font-semibold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Plain English Intent
              </button>
              <button
                type="button"
                onClick={() => setInputTab('diff')}
                className={`px-3 py-1 rounded-md transition-all cursor-pointer ${
                  inputTab === 'diff'
                    ? 'bg-white text-slate-900 shadow-xs font-semibold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Git Diff / Unified Patch
              </button>
            </div>

            {/* Textarea */}
            <div>
              <label htmlFor="change-text-area" className="text-xs font-medium text-slate-700 block mb-1">
                {inputTab === 'text' ? 'Change Description:' : 'Unified Diff:'}
              </label>
              <textarea
                id="change-text-area"
                value={changeText}
                onChange={(e) => setChangeText(e.target.value)}
                rows={6}
                placeholder={
                  inputTab === 'text'
                    ? 'e.g. In calculator.py, add zero-division check in divide() to handle 0 denominator.'
                    : 'diff --git a/file.py b/file.py...'
                }
                className="w-full bg-slate-50/50 border border-slate-300 rounded-lg p-3 text-xs font-mono text-slate-900 focus:bg-white focus:outline-indigo-600 leading-relaxed"
              />
            </div>

            {/* Options Row */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t border-slate-100">
              {/* System Mode */}
              <div>
                <label className="text-xs font-medium text-slate-700 block mb-1">
                  System Mode:
                </label>
                <select
                  value={systemMode}
                  onChange={(e) => setSystemMode(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-indigo-600"
                >
                  <option value="History-RAG">History-RAG (Hybrid + Tree-Sitter)</option>
                  <option value="Semantic-only">Code-RAG (Semantic Vector Only)</option>
                  <option value="History-RAG + Graph">History-RAG + Knowledge Graph</option>
                  <option value="LLM-only">LLM-only Baseline</option>
                </select>
                <span className="text-[10px] text-slate-400 mt-0.5 block">
                  {systemMode === 'History-RAG'
                    ? 'Historical commits + AST graph'
                    : systemMode === 'Semantic-only'
                    ? 'Dense vector search on code'
                    : systemMode === 'History-RAG + Graph'
                    ? 'Multi-hop relationship paths'
                    : 'Direct LLM reasoning'}
                </span>
              </div>

              {/* Number of recommended tests */}
              <div>
                <label htmlFor="top-k-tests-input" className="text-xs font-medium text-slate-700 block mb-1">
                  Max Recommended Tests:
                </label>
                <input
                  id="top-k-tests-input"
                  type="number"
                  min={1}
                  max={15}
                  value={topKTests}
                  onChange={(e) => setTopKTests(Number(e.target.value))}
                  className="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-indigo-600 font-mono"
                />
                <span className="text-[10px] text-slate-400 mt-0.5 block">
                  Top regression tests to rank
                </span>
              </div>

              {/* Candidate test synthesis toggle */}
              <div className="flex flex-col justify-center">
                <label className="flex items-center gap-2 text-xs font-medium text-slate-700 cursor-pointer pt-3">
                  <input
                    type="checkbox"
                    checked={generateCandidateTests}
                    onChange={(e) => setGenerateCandidateTests(e.target.checked)}
                    className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span>Synthesize Candidate Tests</span>
                </label>
                <span className="text-[10px] text-slate-400 ml-5 block">
                  Generate new test cases via AI
                </span>
              </div>
            </div>

            {/* Submit button */}
            <div className="pt-2">
              <Button
                type="submit"
                onClick={(e) => handleRunAnalysis(e)}
                loading={loading}
                disabled={!changeText.trim()}
                icon={<Search className="w-4 h-4" />}
                className="w-full sm:w-auto px-6 cursor-pointer"
              >
                Analyse Change Impact
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Results Presentation */}
      {result && (
        <div ref={resultsRef} className="space-y-6 pt-2">
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Impact Analysis Report
          </h3>

          {/* A. Overall Impact Summary */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <span className="text-xs text-slate-500 block">Overall Severity</span>
                <div className="mt-2">{getSeverityBadge(result.impact_level)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <span className="text-xs text-slate-500 block">AI Confidence Score</span>
                <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
                  {(result.confidence * 100).toFixed(0)}%
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <span className="text-xs text-slate-500 block">Affected Components</span>
                <div className="text-2xl font-bold font-mono text-indigo-600 mt-1">
                  {result.affected_components.length}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <span className="text-xs text-slate-500 block">Recommended Tests</span>
                <div className="text-2xl font-bold font-mono text-emerald-600 mt-1">
                  {result.recommended_tests.length}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* B. Affected Components Table */}
          <Card>
            <CardHeader
              title="1. Affected Components & Risk Breakdown"
              subtitle="Ranked by deterministic Evidence Scoring Engine based on AST and co-change weights"
            />
            <div className="overflow-x-auto">
              <table className="saas-table">
                <thead>
                  <tr>
                    <th>Component</th>
                    <th>Impact Score</th>
                    <th>Severity</th>
                    <th>Reason / Heuristic</th>
                  </tr>
                </thead>
                <tbody>
                  {(result.affected_components || []).map((c, idx) => (
                    <tr key={c.component || idx}>
                      <td>
                        <span className="font-semibold text-slate-900 font-mono text-xs">
                          {c.component}
                        </span>
                      </td>
                      <td>
                        <span className="font-mono text-xs font-bold text-slate-700">
                          {(c.score ?? 0).toFixed(2)}
                        </span>
                      </td>
                      <td>
                        <Badge
                          variant={(c.score ?? 0) > 0.6 ? 'error' : (c.score ?? 0) > 0.3 ? 'warning' : 'success'}
                          size="sm"
                        >
                          {(c.score ?? 0) > 0.6 ? 'HIGH' : (c.score ?? 0) > 0.3 ? 'MEDIUM' : 'LOW'}
                        </Badge>
                      </td>
                      <td className="text-slate-600 text-xs">
                        {c.reasons && c.reasons.length > 0
                          ? c.reasons.join(', ')
                          : c.reason || 'Identified via co-change correlation and AST import links.'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* C. Recommended Existing Tests */}
          <Card>
            <CardHeader
              title="2. Recommended Regression Tests"
              subtitle="Top test suites historically associated with modified components and call graphs"
            />
            {result.recommended_tests.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="saas-table">
                  <thead>
                    <tr>
                      <th>Test File</th>
                      <th>Test Name</th>
                      <th>Component</th>
                      <th>Relevance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(result.recommended_tests || []).map((t, idx) => (
                      <tr key={idx}>
                        <td className="font-mono text-xs text-slate-900 font-semibold">
                          {t.test_file}
                        </td>
                        <td className="font-mono text-xs text-indigo-700">
                          {t.test_name || (t.test_file ? t.test_file.split('/').pop() : 'test_unit')}
                        </td>
                        <td>
                          <Badge variant="neutral" size="sm">
                            {t.component || activeRepo?.name || 'core'}
                          </Badge>
                        </td>
                        <td>
                          <span className="text-xs font-mono font-bold text-emerald-700">
                            {((t.relevance_score ?? t.score ?? 0) * 100).toFixed(0)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-6 text-center text-xs text-slate-500">
                No matching regression tests found for this change in the repository index.
              </div>
            )}
          </Card>

          {/* D. AI-Generated Candidate Tests (if generated) */}
          {result.candidate_tests && result.candidate_tests.length > 0 && (
            <Card>
              <CardHeader
                title="3. Synthesized Candidate Tests"
                subtitle="Automatically generated unit test snippets to fill coverage gaps for modified scenarios"
              />
              <CardContent className="space-y-4">
                {result.candidate_tests.map((ct, idx) => (
                  <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono font-bold text-slate-900 flex items-center gap-1.5">
                        <FileCode className="w-4 h-4 text-indigo-600" />
                        {ct.test_name}
                      </span>
                      <Badge variant={ct.ast_valid ? 'success' : 'warning'} size="sm">
                        {ct.ast_valid ? 'AST Syntax Valid' : 'Syntax Warning'}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-500">{ct.rationale}</p>
                    <pre className="p-3 bg-white border border-slate-200 rounded-lg text-xs font-mono text-slate-800 overflow-x-auto leading-relaxed">
                      {ct.test_code}
                    </pre>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* E. Historical Evidence Timeline */}
          <Card>
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h4 className="text-sm font-semibold text-slate-900">
                  4. Grounded Historical Evidence ({result.historical_evidence.length})
                </h4>
                <p className="text-xs text-slate-500">
                  Historical commits, issues, and PRs retrieved from repository memory
                </p>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setExpandedEvidence(!expandedEvidence)}
                icon={expandedEvidence ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              >
                {expandedEvidence ? 'Collapse' : 'Expand'}
              </Button>
            </div>

            {expandedEvidence && (
              <div className="divide-y divide-slate-100">
                {(result.historical_evidence || []).map((ev, idx) => (
                  <div key={idx} className="p-4 flex items-start gap-3 hover:bg-slate-50/50 transition-colors">
                    <div className="p-1.5 rounded-md bg-indigo-50 text-indigo-600 flex-shrink-0 mt-0.5">
                      <GitCommit className="w-3.5 h-3.5" />
                    </div>
                    <div className="flex-1 min-w-0 space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-slate-900">
                          {ev.id}
                        </span>
                        <Badge variant="neutral" size="sm">
                          {(ev.source_type || (ev.id?.startsWith('commit') ? 'commit' : ev.id?.startsWith('issue') ? 'issue' : ev.id?.startsWith('pr') ? 'pr' : 'evidence')).toUpperCase()}
                        </Badge>
                        <span className="text-[11px] text-slate-400 font-mono">
                          Similarity: {((ev.similarity ?? 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-xs text-slate-700 leading-relaxed font-mono">
                        {ev.message || ev.title || 'Historical entry'}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* F. Next Steps: CI/CD CTA */}
          <div className="p-5 rounded-xl border border-indigo-100 bg-indigo-50/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h4 className="text-sm font-bold text-indigo-950">
                Ready to protect your repository with this gate?
              </h4>
              <p className="text-xs text-indigo-800/80 mt-0.5">
                Install the 1-Click CI/CD GitHub Action to run this evaluation automatically on every Pull Request.
              </p>
            </div>
            <Button
              size="sm"
              onClick={() => onNavigate('cicd')}
              icon={<ArrowRight className="w-3.5 h-3.5" />}
            >
              Configure CI/CD Integration
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

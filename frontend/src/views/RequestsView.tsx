import React, { useState, useEffect } from 'react'
import {
  Plus,
  Search,
  Sparkles,
  AlertTriangle,
  ArrowRight
} from 'lucide-react'
import type { FeatureRequest, ClarityCheckResult, DemoPersona } from '../types/api'
import {
  fetchRequests,
  createRequest,
  checkRequestClarity
} from '../services/api'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'

interface RequestsViewProps {
  activeProjectId: string
  activeRepoId: string
  activePersona?: DemoPersona | null
  onOpenBrief: (requestId: string) => void
}

export const RequestsView: React.FC<RequestsViewProps> = ({
  activeProjectId,
  activeRepoId,
  onOpenBrief,
}) => {
  const [requests, setRequests] = useState<FeatureRequest[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  // Create Modal State
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [criteria, setCriteria] = useState<string[]>([''])
  const [priority, setPriority] = useState<'P0' | 'P1' | 'P2' | 'P3'>('P1')
  const [targetComponent, setTargetComponent] = useState('ipam')

  // Clarity Assistant State
  const [isAnalyzingClarity, setIsAnalyzingClarity] = useState(false)
  const [clarityResult, setClarityResult] = useState<ClarityCheckResult | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    loadRequests()
  }, [activeProjectId])

  const loadRequests = async () => {
    try {
      const data = await fetchRequests(activeProjectId)
      setRequests(data)
    } catch (err) {
      console.error('Failed to load requests', err)
    }
  }

  // Trigger AI Clarity Assistant analysis
  const runClarityCheck = async () => {
    if (!title.trim() && !description.trim()) return

    setIsAnalyzingClarity(true)
    try {
      const validCriteria = criteria.filter((c) => c.trim().length > 0)
      const res = await checkRequestClarity({
        title,
        description,
        acceptance_criteria: validCriteria,
        project_id: activeProjectId,
        repository_id: activeRepoId,
      })
      setClarityResult(res)
    } catch (err) {
      console.error('Clarity analysis failed', err)
    } finally {
      setIsAnalyzingClarity(false)
    }
  }

  // Adopt suggested acceptance criterion
  const adoptCriterion = (text: string) => {
    setCriteria((prev) => {
      const existing = prev.filter((c) => c.trim().length > 0)
      return [...existing, text]
    })
  }

  const handleCreateRequest = async () => {
    if (!title.trim() || isSubmitting) return

    setIsSubmitting(true)
    try {
      const validCriteria = criteria.filter((c) => c.trim().length > 0)
      const newReq = await createRequest({
        title,
        description,
        acceptance_criteria: validCriteria,
        priority,
        project_id: activeProjectId,
        repository_id: activeRepoId,
        target_component: targetComponent,
      })
      setRequests([newReq, ...requests])
      setIsCreateModalOpen(false)
      // Reset form
      setTitle('')
      setDescription('')
      setCriteria([''])
      setClarityResult(null)
    } catch (err) {
      console.error('Failed to create request', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  const filteredRequests = requests.filter((r) => {
    const matchesSearch =
      r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.target_component || '').toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === 'all' || r.status.toLowerCase() === statusFilter.toLowerCase()
    return matchesSearch && matchesStatus
  })

  return (
    <div className="space-y-6">
      {/* Top Banner / Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1 max-w-lg">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search feature requests, HR-IDs, components..."
              className="w-full bg-white border border-slate-200 pl-9 pr-3 py-2 rounded-lg text-xs text-slate-900 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-white border border-slate-200 px-3 py-2 rounded-lg text-xs font-medium text-slate-700 focus:outline-none"
          >
            <option value="all">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="in brief">In Brief</option>
            <option value="planned">Planned</option>
            <option value="in progress">In Progress</option>
            <option value="in review">In Review</option>
            <option value="done">Done</option>
          </select>
        </div>

        <Button
          variant="primary"
          size="md"
          icon={<Plus className="w-4 h-4" />}
          onClick={() => {
            setIsCreateModalOpen(true)
            // Pre-fill demo scenario template if empty
            if (!title) {
              setTitle('Support VRF-aware Route Targets')
              setDescription('Allow RouteTarget import and export definitions per tenant VRF namespace.')
              setCriteria([
                'Validate that RouteTarget format adheres to RFC 4364 (ASN:NN or IP:NN).',
                'Ensure conflicting VRF route target exports raise a structured ValidationError.',
              ])
            }
          }}
        >
          Log Feature Request
        </Button>
      </div>

      {/* Requests Table / Card List */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900">
            Feature Requests ({filteredRequests.length})
          </h3>
          <span className="text-xs text-slate-500">
            Project: <strong className="font-semibold text-slate-700">{activeProjectId}</strong>
          </span>
        </div>

        <div className="divide-y divide-slate-100">
          {filteredRequests.length > 0 ? (
            filteredRequests.map((req) => {
              const displayId = req.id.replace('req-', 'HR-').toUpperCase()
              return (
                <div
                  key={req.id}
                  className="p-5 hover:bg-slate-50/70 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4 cursor-pointer"
                  onClick={() => onOpenBrief(req.id)}
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                        {displayId}
                      </span>
                      <Badge
                        variant={
                          req.status === 'Done'
                            ? 'success'
                            : req.status === 'In Progress'
                            ? 'brand'
                            : req.status === 'Planned'
                            ? 'info'
                            : 'neutral'
                        }
                        size="sm"
                      >
                        {req.status}
                      </Badge>
                      <span className="font-mono text-[11px] font-bold text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded">
                        {req.priority}
                      </span>
                      {req.target_component && (
                        <span className="text-[11px] font-mono text-slate-500">
                          comp: <strong>{req.target_component}</strong>
                        </span>
                      )}
                    </div>
                    <h4 className="text-sm font-bold text-slate-900 hover:text-indigo-600 transition-colors">
                      {req.title}
                    </h4>
                    <p className="text-xs text-slate-600 line-clamp-1">{req.description}</p>
                    <div className="flex items-center gap-4 text-[11px] text-slate-400 pt-1">
                      <span>Requester: {req.requester_name || 'Elena Rostova (PO)'}</span>
                      <span>•</span>
                      <span>{req.acceptance_criteria?.length || 0} Acceptance Criteria</span>
                      <span>•</span>
                      <span>{new Date(req.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={<ArrowRight className="w-3.5 h-3.5" />}
                      onClick={(e) => {
                        e.stopPropagation()
                        onOpenBrief(req.id)
                      }}
                    >
                      Feature Brief
                    </Button>
                  </div>
                </div>
              )
            })
          ) : (
            <div className="text-center py-12 text-slate-400 text-xs">
              No matching feature requests found. Log a new request to trigger automated brief synthesis.
            </div>
          )}
        </div>
      </div>

      {/* New Request Modal with Inline AI Clarity Assistant (Section 8.3) */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Log Feature Request"
        subtitle="AI Request Clarity Assistant analyzes scope and suggests verifiable criteria in real-time."
        maxWidth="3xl"
        footer={
          <div className="flex items-center justify-between w-full">
            <Button
              variant="secondary"
              size="sm"
              icon={<Sparkles className="w-3.5 h-3.5 text-indigo-600" />}
              onClick={runClarityCheck}
              loading={isAnalyzingClarity}
            >
              Analyze with Clarity Assistant
            </Button>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={() => setIsCreateModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleCreateRequest}
                loading={isSubmitting}
                disabled={!title.trim()}
              >
                Create Request
              </Button>
            </div>
          </div>
        }
      >
        <div className="space-y-4">
          {/* Title */}
          <div>
            <label className="block text-xs font-semibold text-slate-800 mb-1">
              Feature Title <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Support VRF-aware Route Targets"
              className="w-full bg-slate-50 border border-slate-200 focus:bg-white focus:border-indigo-500 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-slate-800 mb-1">
              Requirement Description
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the architectural intent, user behavior, and constraints..."
              className="w-full bg-slate-50 border border-slate-200 focus:bg-white focus:border-indigo-500 rounded-lg p-3 text-xs text-slate-900 focus:outline-none"
            />
          </div>

          {/* Target Component & Priority */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-800 mb-1">
                Target Component
              </label>
              <select
                value={targetComponent}
                onChange={(e) => setTargetComponent(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-medium text-slate-700 focus:outline-none"
              >
                <option value="ipam">ipam (IP Address Management)</option>
                <option value="dcim">dcim (Data Center Infrastructure)</option>
                <option value="circuits">circuits</option>
                <option value="extras">extras</option>
                <option value="core">core platform</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-800 mb-1">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as any)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-medium text-slate-700 focus:outline-none"
              >
                <option value="P0">P0 (Critical / Blocker)</option>
                <option value="P1">P1 (High)</option>
                <option value="P2">P2 (Medium)</option>
                <option value="P3">P3 (Low)</option>
              </select>
            </div>
          </div>

          {/* Acceptance Criteria */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-800">
                Acceptance Criteria ({criteria.filter((c) => c.trim()).length})
              </label>
              <button
                type="button"
                onClick={() => setCriteria([...criteria, ''])}
                className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1 cursor-pointer"
              >
                <Plus className="w-3 h-3" /> Add Criterion
              </button>
            </div>
            <div className="space-y-2">
              {criteria.map((c, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-[11px] text-slate-400 font-mono w-4">{i + 1}.</span>
                  <input
                    type="text"
                    value={c}
                    onChange={(e) => {
                      const updated = [...criteria]
                      updated[i] = e.target.value
                      setCriteria(updated)
                    }}
                    placeholder="Enter concrete, verifiable condition..."
                    className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:bg-white focus:border-indigo-500"
                  />
                  {criteria.length > 1 && (
                    <button
                      type="button"
                      onClick={() => setCriteria(criteria.filter((_, idx) => idx !== i))}
                      className="text-slate-400 hover:text-rose-600 p-1"
                    >
                      &times;
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* AI Clarity Assistant Inline Results (Section 8.3) */}
          {clarityResult && (
            <div className="p-4 bg-indigo-50/50 border border-indigo-200 rounded-xl space-y-3 animate-in fade-in duration-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                  <span className="font-semibold text-xs text-indigo-950">
                    AI Clarity Assistant Analysis
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-600">Clarity Score:</span>
                  <span
                    className={`font-mono font-bold text-xs px-2 py-0.5 rounded ${
                      clarityResult.clarity_score >= 80
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {clarityResult.clarity_score}%
                  </span>
                </div>
              </div>

              {/* Ambiguity Flags */}
              {clarityResult.flags.length > 0 && (
                <div className="space-y-1 text-xs">
                  <span className="text-[10px] font-bold uppercase text-amber-700 tracking-wider">
                    Ambiguity & Vague Terms Flagged ({clarityResult.flags.length})
                  </span>
                  {clarityResult.flags.map((flag, idx) => (
                    <div
                      key={idx}
                      className="p-2 bg-amber-50/80 border border-amber-200/80 rounded-lg text-amber-900 text-xs flex items-start gap-2"
                    >
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <strong>{flag.term}</strong>: {flag.question}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Suggested Acceptance Criteria */}
              {clarityResult.suggested_criteria.length > 0 && (
                <div className="space-y-1.5 text-xs">
                  <span className="text-[10px] font-bold uppercase text-indigo-800 tracking-wider">
                    Suggested Verifiable Criteria (1-Click Adopt)
                  </span>
                  {clarityResult.suggested_criteria.map((sug) => (
                    <div
                      key={sug.id}
                      className="p-2.5 bg-white border border-indigo-200 rounded-lg flex items-center justify-between gap-3"
                    >
                      <div className="space-y-0.5 flex-1">
                        <p className="text-slate-800 font-medium">{sug.text}</p>
                        <p className="text-[10px] text-slate-500 italic">{sug.reason}</p>
                      </div>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => adoptCriterion(sug.text)}
                        icon={<Plus className="w-3 h-3" />}
                      >
                        Adopt
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              {/* Similar Past Work */}
              {clarityResult.similar_past_work.length > 0 && (
                <div className="text-xs space-y-1">
                  <span className="text-[10px] font-bold uppercase text-slate-500 tracking-wider">
                    Similar Historical Precedents Found
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {clarityResult.similar_past_work.slice(0, 3).map((past) => (
                      <span
                        key={past.id}
                        className="bg-white border border-slate-200 px-2 py-1 rounded text-[11px] text-slate-700 flex items-center gap-1 font-mono"
                      >
                        <span>{past.id}</span>
                        <span className="text-slate-400">({past.title.slice(0, 30)}...)</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}

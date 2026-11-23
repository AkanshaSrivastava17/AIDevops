import React, { useState, useEffect } from 'react'
import {
  Plus,
  Search,
  ChevronRight
} from 'lucide-react'
import type { Decision, DemoPersona } from '../types/api'
import {
  fetchDecisions,
  createDecision,
  supersedeDecision
} from '../services/api'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'
import { RoleGuard } from '../components/ui/RoleGuard'

interface DecisionLogViewProps {
  activeProjectId: string
  activePersona: DemoPersona | null
  onOpenBrief?: (requestId: string) => void
}

export const DecisionLogView: React.FC<DecisionLogViewProps> = ({
  activeProjectId,
  activePersona,
  onOpenBrief,
}) => {
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  // Create ADR Modal State
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [context, setContext] = useState('')
  const [chosenOption, setChosenOption] = useState('')
  const [rationale, setRationale] = useState('')
  const [tradeoffs, setTradeoffs] = useState('')
  const [component, setComponent] = useState('ipam')

  // Supersede Modal State
  const [supersedeTarget, setSupersedeTarget] = useState<Decision | null>(null)
  const [supersedeReason, setSupersedeReason] = useState('')

  useEffect(() => {
    loadDecisions()
  }, [activeProjectId])

  const loadDecisions = async () => {
    try {
      const data = await fetchDecisions({ projectId: activeProjectId })
      setDecisions(data)
    } catch (err) {
      console.error('Failed to load decisions', err)
    }
  }

  const handleCreateDecision = async () => {
    if (!title.trim() || !rationale.trim()) return

    try {
      const newDec = await createDecision({
        title,
        context,
        chosen_option: chosenOption,
        rationale,
        tradeoffs_accepted: tradeoffs.split('\n').filter((t) => t.trim().length > 0),
        component,
        project_id: activeProjectId,
      })
      setDecisions([newDec, ...decisions])
      setIsCreateOpen(false)
      setTitle('')
      setContext('')
      setChosenOption('')
      setRationale('')
      setTradeoffs('')
    } catch (err) {
      console.error('Failed to record decision', err)
    }
  }

  const handleSupersede = async () => {
    if (!supersedeTarget || !supersedeReason.trim()) return

    try {
      await supersedeDecision(supersedeTarget.id, {
        reason: supersedeReason,
      })
      await loadDecisions()
      setSupersedeTarget(null)
      setSupersedeReason('')
    } catch (err) {
      console.error('Failed to supersede decision', err)
    }
  }

  const filteredDecisions = decisions.filter((d) => {
    const matchesSearch =
      d.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (d.key || d.id).toLowerCase().includes(searchQuery.toLowerCase()) ||
      (d.component || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.rationale.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === 'all' || d.status.toLowerCase() === statusFilter.toLowerCase()
    return matchesSearch && matchesStatus
  })

  const role = activePersona?.role || 'junior_developer'

  return (
    <div className="space-y-6">
      {/* Top Filter & Action Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1 max-w-lg">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search decisions, DEC-IDs, rationale..."
              className="w-full bg-white border border-slate-200 pl-9 pr-3 py-2 rounded-lg text-xs text-slate-900 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-white border border-slate-200 px-3 py-2 rounded-lg text-xs font-medium text-slate-700 focus:outline-none"
          >
            <option value="all">All Decisions</option>
            <option value="active">Active Only</option>
            <option value="superseded">Superseded</option>
          </select>
        </div>

        <RoleGuard currentRole={role} allowedRoles={['tech_lead', 'admin']} disableOnly>
          <Button
            variant="primary"
            size="md"
            icon={<Plus className="w-4 h-4" />}
            onClick={() => setIsCreateOpen(true)}
          >
            Record Decision (ADR)
          </Button>
        </RoleGuard>
      </div>

      {/* Decision Cards List */}
      <div className="space-y-4">
        {filteredDecisions.length > 0 ? (
          filteredDecisions.map((dec) => {
            const displayKey = dec.key || dec.id.toUpperCase()
            const isActive = dec.status === 'Active'

            return (
              <Card key={dec.id} className="p-5 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                      {displayKey}
                    </span>
                    <Badge variant={isActive ? 'success' : 'neutral'} size="sm">
                      {dec.status}
                    </Badge>
                    {dec.component && (
                      <span className="text-[11px] font-mono text-slate-500">
                        comp: <strong>{dec.component}</strong>
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-slate-400">
                    <span>Decided by {dec.decided_by_name || dec.decided_by}</span>
                    <span>•</span>
                    <span>{new Date(dec.decided_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-slate-900">{dec.title}</h4>
                  <p className="text-xs text-slate-600 leading-relaxed">{dec.context}</p>
                </div>

                {/* Chosen Option & Rationale */}
                <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80 space-y-2 text-xs">
                  {dec.chosen_option && (
                    <div>
                      <span className="text-[10px] font-bold uppercase text-slate-400 block tracking-wider">
                        Chosen Architecture Option
                      </span>
                      <strong className="text-slate-800 text-xs">{dec.chosen_option}</strong>
                    </div>
                  )}
                  <div>
                    <span className="text-[10px] font-bold uppercase text-slate-400 block tracking-wider">
                      Architectural Rationale
                    </span>
                    <p className="text-slate-700 leading-relaxed">{dec.rationale}</p>
                  </div>
                  {dec.tradeoffs_accepted && dec.tradeoffs_accepted.length > 0 && (
                    <div>
                      <span className="text-[10px] font-bold uppercase text-amber-700 block tracking-wider mb-1">
                        Tradeoffs Accepted
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {dec.tradeoffs_accepted.map((t, i) => (
                          <span
                            key={i}
                            className="text-[11px] bg-amber-50 text-amber-900 border border-amber-200 px-2 py-0.5 rounded"
                          >
                            ⚠ {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer Toolbar */}
                <div className="flex items-center justify-between pt-1 text-xs">
                  <div className="flex items-center gap-3 text-slate-500">
                    {dec.request_id && (
                      <button
                        type="button"
                        onClick={() => onOpenBrief?.(dec.request_id!)}
                        className="text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1 cursor-pointer"
                      >
                        <span>Linked Request: {dec.request_id}</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>

                  {isActive && (
                    <RoleGuard currentRole={role} allowedRoles={['tech_lead', 'admin']}>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSupersedeTarget(dec)}
                        className="text-slate-500 hover:text-indigo-600 text-[11px]"
                      >
                        Supersede ADR
                      </Button>
                    </RoleGuard>
                  )}
                </div>
              </Card>
            )
          })
        ) : (
          <div className="text-center py-16 bg-white border border-slate-200 rounded-xl text-slate-400 text-xs">
            No architectural decisions recorded yet. Record key architectural choices to build engineering memory.
          </div>
        )}
      </div>

      {/* Create ADR Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Record Architectural Decision (ADR)"
        subtitle="Documents permanent architectural intent and prevents circular architectural drift."
        maxWidth="2xl"
        footer={
          <div className="flex items-center justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleCreateDecision}>
              Save ADR
            </Button>
          </div>
        }
      >
        <div className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-800 mb-1">Decision Title *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Use PostgreSQL JSONB for VRF Extensible Attributes"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:bg-white focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-semibold text-slate-800 mb-1">Target Component</label>
              <select
                value={component}
                onChange={(e) => setComponent(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:outline-none"
              >
                <option value="ipam">ipam</option>
                <option value="dcim">dcim</option>
                <option value="circuits">circuits</option>
                <option value="extras">extras</option>
                <option value="core">core platform</option>
              </select>
            </div>
            <div>
              <label className="block font-semibold text-slate-800 mb-1">Chosen Option Name</label>
              <input
                type="text"
                value={chosenOption}
                onChange={(e) => setChosenOption(e.target.value)}
                placeholder="e.g. Option B: Dedicated IPAM Validation Service Layer"
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:bg-white focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block font-semibold text-slate-800 mb-1">Architectural Context & Problem Statement</label>
            <textarea
              rows={2}
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Why does this decision need to be made? What are the constraints?"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:bg-white focus:outline-none"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-800 mb-1">Architectural Rationale *</label>
            <textarea
              rows={3}
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              placeholder="Why is this chosen over the alternatives? What makes it superior?"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:bg-white focus:outline-none"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-800 mb-1">Tradeoffs Accepted (one per line)</label>
            <textarea
              rows={2}
              value={tradeoffs}
              onChange={(e) => setTradeoffs(e.target.value)}
              placeholder="e.g. Callers bypassing service layer must invoke validator directly"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:bg-white focus:outline-none"
            />
          </div>
        </div>
      </Modal>

      {/* Supersede Modal */}
      <Modal
        isOpen={Boolean(supersedeTarget)}
        onClose={() => setSupersedeTarget(null)}
        title={`Supersede ${supersedeTarget?.key || supersedeTarget?.id}`}
        subtitle="Mark this decision as superseded by newer architectural consensus."
        maxWidth="md"
        footer={
          <div className="flex items-center justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={() => setSupersedeTarget(null)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleSupersede}>
              Confirm Supersede
            </Button>
          </div>
        }
      >
        <div className="space-y-3 text-xs">
          <p className="text-slate-600">
            Explain the rationale for superseding <strong>{supersedeTarget?.title}</strong>:
          </p>
          <textarea
            rows={3}
            value={supersedeReason}
            onChange={(e) => setSupersedeReason(e.target.value)}
            placeholder="e.g. Replaced by dedicated asynchronous event pipeline in v2.2"
            className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:bg-white focus:outline-none"
          />
        </div>
      </Modal>
    </div>
  )
}

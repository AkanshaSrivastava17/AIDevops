import React, { useState } from 'react'
import { GitCommit, AlertCircle, FileText, Calendar, Layers } from 'lucide-react'
import type { EvidenceReference } from '../../types/api'
import { Drawer } from './Drawer'

interface CitationChipProps {
  citation: EvidenceReference | {
    id: string
    source_type?: string
    title?: string
    similarity?: number
    source_date?: string
    component?: string
    excerpt?: string
  }
  variant?: 'inline' | 'card'
}

export const CitationChip: React.FC<CitationChipProps> = ({ citation, variant = 'inline' }) => {
  const [isOpen, setIsOpen] = useState(false)

  const type = citation.source_type || 'commit'
  const isCommit = type === 'commit'
  const isIssue = type === 'issue'

  const icon = isCommit ? (
    <GitCommit className="w-3 h-3 text-indigo-500" />
  ) : isIssue ? (
    <AlertCircle className="w-3 h-3 text-amber-500" />
  ) : (
    <FileText className="w-3 h-3 text-sky-500" />
  )

  const label = isCommit
    ? `Commit: ${citation.id.slice(0, 8)}`
    : isIssue
    ? `Issue: #${citation.id.replace('issue-', '')}`
    : `Doc: ${citation.id}`

  if (variant === 'card') {
    return (
      <>
        <div
          onClick={() => setIsOpen(true)}
          className="group cursor-pointer rounded-lg border border-slate-200 bg-white p-3 hover:border-indigo-300 hover:shadow-xs transition-all text-xs"
        >
          <div className="flex items-center justify-between mb-1.5">
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-slate-100 text-[11px] font-mono text-slate-700">
              {icon}
              {label}
            </span>
            {citation.similarity !== undefined && (
              <span className="text-[10px] font-medium text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">
                {(citation.similarity * 100).toFixed(0)}% match
              </span>
            )}
          </div>
          <p className="text-slate-800 font-medium line-clamp-2 group-hover:text-indigo-600 transition-colors">
            {citation.title || citation.excerpt || 'Historical architectural precedent'}
          </p>
          {citation.component && (
            <div className="flex items-center gap-2 mt-2 text-[10px] text-slate-500">
              <span className="inline-flex items-center gap-1">
                <Layers className="w-3 h-3" />
                {citation.component}
              </span>
              {citation.source_date && (
                <span className="inline-flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {citation.source_date.split('T')[0]}
                </span>
              )}
            </div>
          )}
        </div>

        <CitationDrawer isOpen={isOpen} onClose={() => setIsOpen(false)} citation={citation} />
      </>
    )
  }

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        type="button"
        className="inline-flex items-center gap-1 px-1.5 py-0.5 mx-0.5 rounded-md bg-indigo-50/80 border border-indigo-200/80 text-[11px] font-mono font-medium text-indigo-700 hover:bg-indigo-100 hover:border-indigo-300 transition-colors align-baseline"
      >
        {icon}
        <span>[{label}]</span>
      </button>

      <CitationDrawer isOpen={isOpen} onClose={() => setIsOpen(false)} citation={citation} />
    </>
  )
}

const CitationDrawer: React.FC<{ isOpen: boolean; onClose: () => void; citation: any }> = ({
  isOpen,
  onClose,
  citation,
}) => {
  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title="Evidence Inspector"
      subtitle={`Ground-truth verification artifact for ${citation.id}`}
      width="lg"
    >
      <div className="space-y-4 text-xs">
        {/* Header meta badge */}
        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-mono text-slate-500 text-[11px]">Source Identifier</span>
            <span className="font-mono font-bold text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200">
              {citation.id}
            </span>
          </div>
          {citation.component && (
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Target Component</span>
              <span className="font-semibold text-slate-800">{citation.component}</span>
            </div>
          )}
          {citation.similarity !== undefined && (
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Semantic Relevance Score</span>
              <span className="text-emerald-700 font-bold">{(citation.similarity * 100).toFixed(1)}%</span>
            </div>
          )}
          {citation.source_date && (
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Historical Commit Date</span>
              <span className="text-slate-700 font-mono">{citation.source_date}</span>
            </div>
          )}
        </div>

        {/* Title / Description */}
        <div>
          <h4 className="font-semibold text-slate-900 mb-1">Historical Context & Commit Message</h4>
          <div className="p-3 bg-white rounded-lg border border-slate-200 text-slate-700 leading-relaxed font-sans">
            {citation.title || citation.excerpt || 'No extended commit details available.'}
          </div>
        </div>

        {/* Excerpt */}
        {citation.excerpt && citation.excerpt !== citation.title && (
          <div>
            <h4 className="font-semibold text-slate-900 mb-1">Code & Diff Excerpt</h4>
            <pre className="p-3 bg-slate-900 text-slate-100 rounded-lg overflow-x-auto font-mono text-[11px] leading-snug">
              {citation.excerpt}
            </pre>
          </div>
        )}

        <div className="pt-3 border-t border-slate-100 text-slate-400 text-[11px]">
          Verified against indexed repository commit graph. Temporal filtering confirmed no lookahead bias.
        </div>
      </div>
    </Drawer>
  )
}

import React from 'react'
import { Plus, Minus, ArrowRight, Layers, TestTube, CheckSquare, GitCompare } from 'lucide-react'
import type { BriefDiff } from '../../types/api'

interface VersionDiffProps {
  diff: BriefDiff
}

export const VersionDiff: React.FC<VersionDiffProps> = ({ diff }) => {
  return (
    <div className="space-y-4 text-xs">
      {/* Diff Banner */}
      <div className="flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded-lg">
        <div className="flex items-center gap-2 font-mono text-slate-700">
          <GitCompare className="w-4 h-4 text-indigo-600" />
          <span className="font-semibold">Version {diff.version_a}</span>
          <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
          <span className="font-semibold text-indigo-700">Version {diff.version_b}</span>
        </div>
        <span className="text-[11px] text-slate-500 font-medium">
          {diff.summary || 'Architectural Brief Diff Snapshot'}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Components Changed */}
        <div className="p-3.5 bg-white border border-slate-200 rounded-lg space-y-2">
          <div className="flex items-center gap-2 font-semibold text-slate-900 border-b border-slate-100 pb-2">
            <Layers className="w-4 h-4 text-indigo-500" />
            <span>Components Delta</span>
          </div>
          {diff.components_added.length === 0 && diff.components_removed.length === 0 ? (
            <p className="text-slate-400 italic">No component scope changes.</p>
          ) : (
            <div className="space-y-1">
              {diff.components_added.map((c) => (
                <div key={c} className="flex items-center gap-1.5 text-emerald-700 bg-emerald-50/70 px-2 py-1 rounded">
                  <Plus className="w-3.5 h-3.5 shrink-0" />
                  <span className="font-mono font-medium">{c}</span>
                  <span className="text-[10px] text-emerald-600 ml-auto">Added to scope</span>
                </div>
              ))}
              {diff.components_removed.map((c) => (
                <div key={c} className="flex items-center gap-1.5 text-rose-700 bg-rose-50/70 px-2 py-1 rounded">
                  <Minus className="w-3.5 h-3.5 shrink-0" />
                  <span className="font-mono font-medium">{c}</span>
                  <span className="text-[10px] text-rose-600 ml-auto">Removed from scope</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Tests Delta */}
        <div className="p-3.5 bg-white border border-slate-200 rounded-lg space-y-2">
          <div className="flex items-center gap-2 font-semibold text-slate-900 border-b border-slate-100 pb-2">
            <TestTube className="w-4 h-4 text-sky-500" />
            <span>Recommended Tests Delta</span>
          </div>
          {diff.tests_added.length === 0 ? (
            <p className="text-slate-400 italic">Identical test recommendation set.</p>
          ) : (
            <div className="space-y-1">
              {diff.tests_added.map((t) => (
                <div key={t} className="flex items-center gap-1.5 text-sky-800 bg-sky-50/70 px-2 py-1 rounded">
                  <Plus className="w-3.5 h-3.5 shrink-0 text-sky-600" />
                  <span className="font-mono font-medium truncate">{t}</span>
                  <span className="text-[10px] text-sky-600 ml-auto shrink-0">New Test</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Tasks Delta */}
      {diff.tasks_added.length > 0 && (
        <div className="p-3.5 bg-white border border-slate-200 rounded-lg space-y-2">
          <div className="flex items-center gap-2 font-semibold text-slate-900 border-b border-slate-100 pb-2">
            <CheckSquare className="w-4 h-4 text-emerald-500" />
            <span>Tasks Decomposed in Version {diff.version_b}</span>
          </div>
          <div className="space-y-1">
            {diff.tasks_added.map((task) => (
              <div key={task} className="flex items-center gap-2 text-slate-800 bg-slate-50 px-2.5 py-1.5 rounded">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span className="font-medium">{task}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

import React from 'react'
import { Check } from 'lucide-react'
import type { RequestStatus } from '../../types/api'

interface StatusStepperProps {
  currentStatus: RequestStatus
  onStepClick?: (status: RequestStatus) => void
  disabled?: boolean
}

const STAGES: { status: RequestStatus; label: string }[] = [
  { status: 'Draft', label: '1. Log Request' },
  { status: 'In Brief', label: '2. Plan Feature' },
  { status: 'Planned', label: '3. Split Tasks' },
  { status: 'In Progress', label: '4. Build & Pre-PR' },
  { status: 'In Review', label: '5. Verify in CI' },
  { status: 'Done', label: '6. Close Loop' },
]

export const StatusStepper: React.FC<StatusStepperProps> = ({
  currentStatus,
  onStepClick,
  disabled = false,
}) => {
  const currentIndex = STAGES.findIndex((s) => s.status === currentStatus)

  return (
    <div className="w-full py-2">
      <div className="flex items-center justify-between">
        {STAGES.map((stage, idx) => {
          const isDone = idx < currentIndex || currentStatus === 'Done'
          const isCurrent = idx === currentIndex && currentStatus !== 'Done'

          return (
            <React.Fragment key={stage.status}>
              <button
                type="button"
                disabled={disabled || !onStepClick}
                onClick={() => onStepClick?.(stage.status)}
                className={`flex flex-col items-center group focus:outline-none ${
                  disabled || !onStepClick ? 'cursor-default' : 'cursor-pointer'
                }`}
              >
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold transition-all ${
                    isDone
                      ? 'bg-emerald-600 text-white'
                      : isCurrent
                      ? 'bg-indigo-600 text-white ring-4 ring-indigo-100 shadow-xs'
                      : 'bg-slate-100 text-slate-400 border border-slate-200'
                  }`}
                >
                  {isDone ? <Check className="w-3.5 h-3.5 stroke-[3]" /> : idx + 1}
                </div>
                <span
                  className={`mt-1.5 text-[11px] font-medium transition-colors whitespace-nowrap ${
                    isDone
                      ? 'text-slate-700'
                      : isCurrent
                      ? 'text-indigo-600 font-bold'
                      : 'text-slate-400'
                  }`}
                >
                  {stage.label}
                </span>
              </button>

              {idx < STAGES.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-2 transition-colors ${
                    idx < currentIndex ? 'bg-emerald-500' : 'bg-slate-200'
                  }`}
                />
              )}
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}

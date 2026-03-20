import { useNavigate } from 'react-router-dom'
import { OnboardingAction } from '../api/frappe'

interface ChecklistWidgetProps {
  title: string
  completionPercent: number
  actions: OnboardingAction[]
  isLoading?: boolean
}

export function ChecklistWidget({ title, completionPercent, actions, isLoading }: ChecklistWidgetProps) {
  const navigate = useNavigate()

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-xl border">
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="space-y-3">
              <div className="h-3 bg-gray-200 rounded w-full"></div>
              <div className="h-3 bg-gray-200 rounded w-5/6"></div>
              <div className="h-3 bg-gray-200 rounded w-4/6"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const isComplete = completionPercent >= 100

  return (
    <div className="bg-white shadow rounded-xl border overflow-hidden">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-500">{title}</h3>
          <span className={`text-sm font-bold ${isComplete ? 'text-green-600' : 'text-indigo-600'}`}>
            {Math.round(completionPercent)}%
          </span>
        </div>
        
        {/* Progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
          <div
            className={`h-2 rounded-full transition-all ${
              isComplete ? 'bg-green-500' : 'bg-indigo-600'
            }`}
            style={{ width: `${Math.min(100, completionPercent)}%` }}
          ></div>
        </div>

        {/* Actions */}
        {actions.length === 0 ? (
          <div className="text-center py-4">
            <span className="text-green-600 font-medium text-sm">All set! You're ready to go.</span>
          </div>
        ) : (
          <div className="space-y-2">
            {actions.slice(0, 3).map((action, idx) => (
              <button
                key={action.action_key}
                onClick={() => {
                  const route = action.route.replace(/^\/frontend/, '')
                  navigate(route)
                }}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  idx === 0
                    ? 'bg-indigo-50 hover:bg-indigo-100 border border-indigo-200'
                    : 'bg-gray-50 hover:bg-gray-100'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium ${idx === 0 ? 'text-indigo-900' : 'text-gray-900'}`}>
                      {idx === 0 && (
                        <span className="inline-block mr-2 text-xs bg-indigo-600 text-white px-1.5 py-0.5 rounded">
                          Next
                        </span>
                      )}
                      {action.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5 truncate">{action.description}</p>
                  </div>
                  <svg className={`w-4 h-4 flex-shrink-0 ml-2 ${idx === 0 ? 'text-indigo-600' : 'text-gray-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ChecklistWidget

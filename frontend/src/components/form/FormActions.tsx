/**
 * FormActions - Save, Cancel, and action buttons for forms.
 */

import React from 'react'

interface FormActionsProps {
  isSaving: boolean
  isDirty: boolean
  onSave: () => void
  onCancel: () => void
  onBack?: () => void
  saveLabel?: string
  cancelLabel?: string
  backLabel?: string
  showSave?: boolean
  showCancel?: boolean
  showBack?: boolean
  additionalActions?: React.ReactNode
  saveDisabled?: boolean
}

export const FormActions: React.FC<FormActionsProps> = ({
  isSaving,
  isDirty,
  onSave,
  onCancel,
  onBack,
  saveLabel = 'Save',
  cancelLabel = 'Cancel',
  backLabel = 'Back',
  showSave = true,
  showCancel = true,
  showBack = false,
  additionalActions,
  saveDisabled = false,
}) => {
  return (
    <div className="flex items-center justify-between py-4 border-t border-gray-200 bg-gray-50 px-6">
      {/* Left side: Back button */}
      <div className="flex-shrink-0">
        {showBack && onBack && (
          <button
            type="button"
            onClick={onBack}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <svg
              className="w-4 h-4 mr-1.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            {backLabel}
          </button>
        )}
      </div>

      {/* Center: Additional actions */}
      {additionalActions && (
        <div className="flex items-center gap-2">
          {additionalActions}
        </div>
      )}

      {/* Right side: Cancel and Save */}
      <div className="flex items-center gap-3">
        {showCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isSaving}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {cancelLabel}
          </button>
        )}

        {showSave && (
          <button
            type="button"
            onClick={onSave}
            disabled={isSaving || (!isDirty && saveDisabled)}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Saving...
              </>
            ) : (
              saveLabel
            )}
          </button>
        )}
      </div>
    </div>
  )
}

// Compact action bar for inline forms
interface CompactActionsProps {
  isSaving: boolean
  onSave: () => void
  onCancel: () => void
  saveLabel?: string
  saveDisabled?: boolean
}

export const CompactActions: React.FC<CompactActionsProps> = ({
  isSaving,
  onSave,
  onCancel,
  saveLabel = 'Save',
  saveDisabled = false,
}) => {
  return (
    <div className="flex items-center justify-end gap-2">
      <button
        type="button"
        onClick={onCancel}
        disabled={isSaving}
        className="px-3 py-1.5 text-sm font-medium text-gray-700 hover:text-gray-900 disabled:opacity-50"
      >
        Cancel
      </button>
      <button
        type="button"
        onClick={onSave}
        disabled={isSaving || saveDisabled}
        className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isSaving ? (
          <>
            <svg
              className="animate-spin -ml-1 mr-1.5 h-4 w-4 text-white"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Saving...
          </>
        ) : (
          saveLabel
        )}
      </button>
    </div>
  )
}

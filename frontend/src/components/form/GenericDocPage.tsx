/**
 * GenericDocPage - Server-driven detail page for DocTypes.
 * 
 * This component uses the safe_list_api backend which normalizes all values
 * into safe renderable strings, preventing React runtime crashes.
 * 
 * Features:
 * - Server-driven detail rendering (no raw metadata interpretation)
 * - Safe value rendering (all values are pre-normalized by backend)
 * - Edit mode with form fields
 * - Save/Cancel/Delete actions
 * - Dirty state handling
 * - Permission handling
 * - Loading/error/empty states
 */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSafeDetail } from '../../features/safeList/useSafeDetail'
import { AppLayout, PageHeader, Content, Card, ErrorBanner, SuccessBanner } from '../ui'
import { DynamicErrorBoundary } from '../errors/DynamicPageErrorBoundary'
import { SafeDetailField } from '../../utils/renderValue'

interface GenericDocPageProps {
  /** DocType name (e.g., "QR Code Tag", "Owner Profile") */
  doctype: string
  
  /** Document name */
  name: string
  
  /** Custom title */
  title?: string
  
  /** On back navigation callback */
  onBack?: () => void
}

export function GenericDocPage({
  doctype,
  name,
  title,
  onBack
}: GenericDocPageProps) {
  const navigate = useNavigate()
  
  // Use safe detail hook (server-driven approach)
  const {
    schema,
    fields,
    displayValues,
    values,
    canWrite,
    canDelete,
    isLoading,
    isSaving,
    isDeleting,
    error,
    isPermissionError,
    refresh,
    updateDoc,
    deleteDoc
  } = useSafeDetail({
    doctype: doctype || null,
    name: name || null
  })

  // Edit mode state
  const [isEditing, setIsEditing] = useState(false)
  const [editedValues, setEditedValues] = useState<Record<string, any>>({})
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  // Determine page title
  const pageTitle = title || schema?.title || doctype

  // Reset edited values when values change
  useEffect(() => {
    setEditedValues(values)
  }, [values])

  // Clear messages when editing changes
  useEffect(() => {
    if (!isEditing) {
      setSaveError(null)
      setSaveSuccess(null)
    }
  }, [isEditing])

  // Check if form has changes
  const isDirty = JSON.stringify(editedValues) !== JSON.stringify(values)

  // Handle back navigation
  const handleBack = useCallback(() => {
    if (isDirty) {
      if (window.confirm('You have unsaved changes. Are you sure you want to leave?')) {
        if (onBack) {
          onBack()
        } else {
          navigate(`/list/${encodeURIComponent(doctype)}`)
        }
      }
    } else {
      if (onBack) {
        onBack()
      } else {
        navigate(`/list/${encodeURIComponent(doctype)}`)
      }
    }
  }, [isDirty, onBack, navigate, doctype])

  // Handle edit mode
  const handleEdit = () => {
    setEditedValues(values)
    setIsEditing(true)
    setSaveError(null)
    setSaveSuccess(null)
  }

  // Handle cancel edit
  const handleCancel = () => {
    setEditedValues(values)
    setIsEditing(false)
    setSaveError(null)
    setSaveSuccess(null)
  }

  // Handle field change
  const handleFieldChange = (fieldname: string, value: any) => {
    setEditedValues(prev => ({ ...prev, [fieldname]: value }))
  }

  // Handle save
  const handleSave = async () => {
    const result = await updateDoc(editedValues)
    
    if (result.success) {
      setSaveSuccess('Document saved successfully!')
      setIsEditing(false)
      setTimeout(() => setSaveSuccess(null), 3000)
    } else {
      setSaveError(result.error || 'Failed to save document')
    }
  }

  // Handle delete
  const handleDelete = async () => {
    const result = await deleteDoc()
    
    if (result.success) {
      navigate(`/list/${encodeURIComponent(doctype)}`)
    } else {
      setSaveError(result.error || 'Failed to delete document')
      setShowDeleteConfirm(false)
    }
  }

  // Handle permission error
  if (isPermissionError) {
    return (
      <AppLayout>
        <div className="mb-6">
          <div className="flex items-center">
            <button
              onClick={handleBack}
              className="mr-3 text-gray-400 hover:text-gray-600"
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <h1 className="text-2xl font-bold text-gray-900">{pageTitle}</h1>
          </div>
        </div>
        <Content>
          <Card>
            <div className="p-6">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Permission Denied</h3>
                  <div className="mt-2 text-sm text-red-700">
                    <p>You don't have permission to view this document.</p>
                    <p className="mt-1">Document: {name}</p>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </Content>
      </AppLayout>
    )
  }

  // Handle error
  if (error && !isEditing) {
    return (
      <AppLayout>
        <div className="mb-6">
          <div className="flex items-center">
            <button
              onClick={handleBack}
              className="mr-3 text-gray-400 hover:text-gray-600"
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <h1 className="text-2xl font-bold text-gray-900">{pageTitle}</h1>
          </div>
        </div>
        <Content>
          <ErrorBanner message={error} onRetry={refresh} />
        </Content>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={handleBack}
              className="mr-3 text-gray-400 hover:text-gray-600"
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{pageTitle}</h1>
              <p className="text-sm text-gray-500 mt-0.5">{name}</p>
            </div>
          </div>
          
          {/* Actions */}
          <div className="flex items-center gap-3">
            {isEditing ? (
              <>
                <button
                  onClick={handleCancel}
                  disabled={isSaving}
                  className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={isSaving || !isDirty}
                  className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  {isSaving ? 'Saving...' : 'Save'}
                </button>
              </>
            ) : (
              <>
                {canWrite && (
                  <button
                    onClick={handleEdit}
                    className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
                  >
                    <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Edit
                  </button>
                )}
                {canDelete && (
                  <button
                    onClick={() => setShowDeleteConfirm(true)}
                    className="inline-flex items-center px-3 py-2 text-sm font-medium text-red-600 bg-white border border-red-300 rounded-lg hover:bg-red-50"
                  >
                    <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    Delete
                  </button>
                )}
                <button
                  onClick={refresh}
                  disabled={isLoading}
                  className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                  <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh
                </button>
              </>
            )}
          </div>
        </div>
      </div>
      
      <Content>
        {/* Success/Error messages */}
        {saveSuccess && <SuccessBanner message={saveSuccess} onClose={() => setSaveSuccess(null)} />}
        {saveError && <ErrorBanner message={saveError} onClose={() => setSaveError(null)} />}
        
        {/* Delete confirmation modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md mx-4">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Delete Document</h3>
              <p className="text-sm text-gray-500 mb-4">
                Are you sure you want to delete this document? This action cannot be undone.
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50"
                >
                  {isDeleting ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            </div>
          </div>
        )}

        {isLoading ? (
          <DetailSkeleton />
        ) : (
          <DetailView
            fields={fields}
            displayValues={displayValues}
            editedValues={editedValues}
            isEditing={isEditing}
            onFieldChange={handleFieldChange}
          />
        )}
      </Content>
    </AppLayout>
  )
}

// Detail View - renders fields with optional edit mode
function DetailView({
  fields,
  displayValues,
  editedValues,
  isEditing,
  onFieldChange
}: {
  fields: SafeDetailField[]
  displayValues: Record<string, string>
  editedValues: Record<string, any>
  isEditing: boolean
  onFieldChange: (fieldname: string, value: any) => void
}) {
  if (fields.length === 0) {
    return (
      <Card>
        <div className="p-6 text-center text-gray-500">
          No fields configured for this document.
        </div>
      </Card>
    )
  }

  // Group fields by section (using read_only as a simple section indicator)
  const readOnlyFields = fields.filter(f => f.read_only)
  const editableFields = fields.filter(f => !f.read_only)

  return (
    <Card>
      <div className="divide-y divide-gray-200">
        {/* Editable fields */}
        {editableFields.length > 0 && (
          <div className="p-6">
            <h3 className="text-sm font-medium text-gray-900 mb-4">Details</h3>
            <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
              {editableFields.map((field) => (
                <div key={field.fieldname} className="sm:col-span-1">
                  <dt className="text-sm font-medium text-gray-500 mb-1">
                    {field.label}
                    {field.reqd && <span className="text-red-500 ml-1">*</span>}
                  </dt>
                  <dd className="mt-1">
                    {isEditing ? (
                      <FormField
                        field={field}
                        value={editedValues[field.fieldname]}
                        onChange={(value) => onFieldChange(field.fieldname, value)}
                      />
                    ) : (
                      <span className="text-sm text-gray-900">
                        {displayValues[field.fieldname] ?? '-'}
                      </span>
                    )}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        )}
        
        {/* Read-only fields */}
        {readOnlyFields.length > 0 && (
          <div className="p-6 bg-gray-50">
            <h3 className="text-sm font-medium text-gray-900 mb-4">System Information</h3>
            <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
              {readOnlyFields.map((field) => (
                <div key={field.fieldname} className="sm:col-span-1">
                  <dt className="text-sm font-medium text-gray-500">{field.label}</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {displayValues[field.fieldname] ?? '-'}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        )}
      </div>
    </Card>
  )
}

// Form field component for edit mode
function FormField({
  field,
  value,
  onChange
}: {
  field: SafeDetailField
  value: any
  onChange: (value: any) => void
}) {
  const baseClasses = "block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"

  switch (field.fieldtype) {
    case 'Check':
      return (
        <div className="flex items-center">
          <input
            type="checkbox"
            checked={!!value}
            onChange={(e) => onChange(e.target.checked ? 1 : 0)}
            className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
          />
          <span className="ml-2 text-sm text-gray-600">
            {value ? 'Yes' : 'No'}
          </span>
        </div>
      )
    
    case 'Select':
      return (
        <select
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          className={baseClasses}
        >
          <option value="">Select...</option>
          {(field.options_list || []).map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      )
    
    case 'Int':
    case 'Float':
    case 'Currency':
      return (
        <input
          type="number"
          value={value || ''}
          onChange={(e) => onChange(e.target.value ? parseFloat(e.target.value) : null)}
          className={baseClasses}
        />
      )
    
    case 'Date':
      return (
        <input
          type="date"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          className={baseClasses}
        />
      )
    
    case 'Datetime':
      return (
        <input
          type="datetime-local"
          value={value ? value.slice(0, 16) : ''}
          onChange={(e) => onChange(e.target.value)}
          className={baseClasses}
        />
      )
    
    case 'Text':
    case 'Small Text':
      return (
        <textarea
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          rows={3}
          className={baseClasses}
        />
      )
    
    case 'Long Text':
    case 'Text Editor':
      return (
        <textarea
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          rows={5}
          className={baseClasses}
        />
      )
    
    default:
      return (
        <input
          type="text"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          className={baseClasses}
        />
      )
  }
}

// Loading skeleton
function DetailSkeleton() {
  return (
    <Card>
      <div className="p-6 space-y-6">
        <div className="h-4 bg-gray-200 rounded w-1/4 animate-pulse"></div>
        <div className="grid grid-cols-2 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i}>
              <div className="h-3 bg-gray-200 rounded w-1/3 mb-2 animate-pulse"></div>
              <div className="h-4 bg-gray-200 rounded w-2/3 animate-pulse"></div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}

export default GenericDocPage

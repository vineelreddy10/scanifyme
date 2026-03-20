/**
 * GenericDocPage - Server-driven detail page for DocTypes.
 * 
 * This component uses the safe_list_api backend which normalizes all values
 * into safe renderable strings, preventing React runtime crashes.
 * 
 * Features:
 * - Server-driven detail rendering (no raw metadata interpretation)
 * - Safe value rendering (all values are pre-normalized by backend)
 * - Error boundary for crash protection
 * - Loading/error/empty states
 * - Permission handling
 */

import { useNavigate } from 'react-router-dom'
import { useSafeDetail } from '../../features/safeList/useSafeDetail'
import { AppLayout, PageHeader, Content, Card } from '../ui'
import { DynamicErrorBoundary } from '../errors/DynamicPageErrorBoundary'
import { 
  SafeDetailField,
  getBooleanClass,
  getLinkClass,
  getEmptyClass
} from '../../utils/renderValue'

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
    canWrite,
    isLoading,
    error,
    isPermissionError,
    refresh
  } = useSafeDetail({
    doctype: doctype || null,
    name: name || null
  })

  // Determine page title
  const pageTitle = title || schema?.title || doctype

  // Handle back navigation
  const handleBack = () => {
    if (onBack) {
      onBack()
    } else {
      navigate(`/list/${encodeURIComponent(doctype)}`)
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
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex">
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
        </Content>
      </AppLayout>
    )
  }

  // Handle error
  if (error) {
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
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error Loading Document</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                  <p className="mt-1">Document: {name}</p>
                </div>
                <button
                  onClick={refresh}
                  className="mt-3 text-sm text-red-600 hover:text-red-800 font-medium"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
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
            {canWrite && (
              <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
                Editable
              </span>
            )}
            <button
              onClick={refresh}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>
      
      <Content>
        {isLoading ? (
          <DetailSkeleton />
        ) : (
          <DetailView
            fields={fields}
            displayValues={displayValues}
          />
        )}
      </Content>
    </AppLayout>
  )
}

// Detail View - renders pre-normalized display values
function DetailView({
  fields,
  displayValues
}: {
  fields: SafeDetailField[]
  displayValues: Record<string, string>
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
                  <dt className="text-sm font-medium text-gray-500">{field.label}</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {renderFieldValue(field, displayValues[field.fieldname] ?? '-')}
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
                    {renderFieldValue(field, displayValues[field.fieldname] ?? '-')}
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

// Render a field value based on fieldtype
function renderFieldValue(field: SafeDetailField, displayValue: string): React.ReactNode {
  // Empty value
  if (displayValue === '-' || displayValue === '') {
    return <span className="text-gray-400">-</span>
  }
  
  // Boolean/Check field
  if (field.fieldtype === 'Check') {
    const isTrue = displayValue === 'Yes'
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getBooleanClass(isTrue)}`}>
        {displayValue}
      </span>
    )
  }
  
  // Link field
  if (field.fieldtype === 'Link') {
    return (
      <span className={getLinkClass()}>
        {displayValue}
      </span>
    )
  }
  
  // Default text display
  return <span>{displayValue}</span>
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

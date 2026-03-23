/**
 * GenericCreate - Page for creating new documents of any DocType.
 * 
 * This component provides a dynamic form for creating new documents
 * based on the doctype schema provided by the backend.
 */

import { useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useSafeCreate } from '../features/safeList/useSafeDetail'
import { AppLayout, PageHeader, Content, Card, ErrorBanner, SuccessBanner } from '../components/ui'
import { SafeDetailField } from '../utils/renderValue'

export default function GenericCreate() {
  const { doctype } = useParams<{ doctype: string }>()
  const navigate = useNavigate()
  
  const decodedDoctype = doctype ? decodeURIComponent(doctype) : ''
  
  const {
    schema,
    fields,
    canCreate,
    isLoading,
    isSaving,
    error,
    createDoc
  } = useSafeCreate(decodedDoctype || null)
  
  // Form state
  const [formValues, setFormValues] = useState<Record<string, any>>({})
  const [validationError, setValidationError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null)
  
  // Handle field change
  const handleFieldChange = (fieldname: string, value: any) => {
    setFormValues(prev => ({ ...prev, [fieldname]: value }))
    setValidationError(null)
  }
  
  // Handle back navigation
  const handleBack = () => {
    navigate(`/list/${encodeURIComponent(decodedDoctype)}`)
  }
  
  // Validate form
  const validateForm = useCallback(() => {
    for (const field of fields) {
      if (field.reqd && !formValues[field.fieldname]) {
        return `Required field '${field.label}' is missing`
      }
    }
    return null
  }, [fields, formValues])
  
  // Handle save
  const handleSave = async () => {
    // Validate
    const validation = validateForm()
    if (validation) {
      setValidationError(validation)
      return
    }
    
    // Create document
    const result = await createDoc(formValues)
    
    if (result.success) {
      setSaveSuccess('Document created successfully!')
      // Navigate to detail page after short delay
      setTimeout(() => {
        navigate(`/m/${encodeURIComponent(decodedDoctype)}/${encodeURIComponent(result.name || '')}`)
      }, 1500)
    } else {
      setValidationError(result.error || 'Failed to create document')
    }
  }
  
  // Handle cancel
  const handleCancel = () => {
    handleBack()
  }
  
  // Get page title
  const pageTitle = schema?.title || decodedDoctype || 'Create Document'
  
  // Handle loading state
  if (isLoading) {
    return (
      <AppLayout>
        <PageHeader title={`New ${pageTitle}`} />
        <Content>
          <Card>
            <div className="p-6 space-y-6">
              <div className="h-4 bg-gray-200 rounded w-1/4 animate-pulse"></div>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                {[...Array(6)].map((_, i) => (
                  <div key={i}>
                    <div className="h-3 bg-gray-200 rounded w-1/3 mb-2 animate-pulse"></div>
                    <div className="h-10 bg-gray-200 rounded animate-pulse"></div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </Content>
      </AppLayout>
    )
  }
  
  // Handle no permission
  if (!canCreate && !isLoading) {
    return (
      <AppLayout>
        <PageHeader title={`New ${pageTitle}`} />
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
                    <p>You don't have permission to create this type of document.</p>
                  </div>
                  <button
                    onClick={handleBack}
                    className="mt-4 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Go Back
                  </button>
                </div>
              </div>
            </div>
          </Card>
        </Content>
      </AppLayout>
    )
  }
  
  // Filter editable fields only (exclude read-only fields from creation form)
  const editableFields = fields.filter(f => !f.read_only)
  
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
              <h1 className="text-2xl font-bold text-gray-900">New {pageTitle}</h1>
              <p className="text-sm text-gray-500 mt-0.5">Create a new {pageTitle.toLowerCase()} record</p>
            </div>
          </div>
          
          {/* Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleCancel}
              disabled={isSaving}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || saveSuccess !== null}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {isSaving ? 'Creating...' : 'Create'}
            </button>
          </div>
        </div>
      </div>
      
      <Content>
        {/* Success/Error messages */}
        {saveSuccess && (
          <SuccessBanner message={saveSuccess} />
        )}
        {(validationError || error) && (
          <ErrorBanner message={validationError || error || ''} onClose={() => setValidationError(null)} />
        )}
        
        <Card>
          <div className="p-6">
            {editableFields.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <p>No fields available for creating this document.</p>
              </div>
            ) : (
              <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                {editableFields.map((field) => (
                  <div 
                    key={field.fieldname} 
                    className={`sm:col-span-1 ${field.fieldtype === 'Text Editor' || field.fieldtype === 'Long Text' ? 'sm:col-span-2' : ''}`}
                  >
                    <dt className="text-sm font-medium text-gray-700 mb-1">
                      {field.label}
                      {field.reqd && <span className="text-red-500 ml-1">*</span>}
                    </dt>
                    <dd className="mt-1">
                      <CreateFormField
                        field={field}
                        value={formValues[field.fieldname]}
                        onChange={(value) => handleFieldChange(field.fieldname, value)}
                      />
                    </dd>
                  </div>
                ))}
              </dl>
            )}
          </div>
        </Card>
      </Content>
    </AppLayout>
  )
}

// Form field component for create mode
function CreateFormField({
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
          value={value ? String(value).slice(0, 16) : ''}
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
          placeholder={`Enter ${field.label.toLowerCase()}...`}
        />
      )
    
    case 'Long Text':
    case 'Text Editor':
      return (
        <textarea
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          rows={6}
          className={baseClasses}
          placeholder={`Enter ${field.label.toLowerCase()}...`}
        />
      )
    
    default:
      return (
        <input
          type="text"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          className={baseClasses}
          placeholder={`Enter ${field.label.toLowerCase()}...`}
        />
      )
  }
}

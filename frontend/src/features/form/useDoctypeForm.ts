/**
 * useDoctypeForm - Hook for fetching and managing Frappe document forms.
 * 
 * Handles:
 * - Document fetching (GET via Frappe REST API v2)
 * - Form state management
 * - Dirty state tracking
 * - Save/Update operations (PUT via REST API)
 * - Validation
 * - Error handling
 */

import { useState, useCallback, useEffect } from 'react'

// Types
export interface DocField {
  fieldname: string
  label: string
  fieldtype: string
  options: string | null
  options_list?: string[]
  in_list_view: boolean
  in_standard_filter: boolean
  read_only: boolean
  reqd: boolean
}

export interface DocMeta {
  name: string
  label: string
  fields: DocField[]
  title_field: string | null
  sort_field: string
  sort_order: 'ASC' | 'DESC'
  editable_grid: boolean
}

export interface DocValues {
  [key: string]: unknown
}

export interface ValidationError {
  field: string
  message: string
}

export interface UseDoctypeFormOptions {
  doctype: string
  name?: string
  initialValues?: DocValues
  autosave?: boolean
  onSaveSuccess?: (doc: DocValues) => void
  onSaveError?: (error: string) => void
}

// API Functions
async function fetchDocument(doctype: string, name: string): Promise<DocValues> {
  const url = `/api/v2/document/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to fetch document' }))
    throw new Error(error.message || `Failed to fetch ${doctype} ${name}`)
  }

  const data = await response.json()
  return data.data || data
}

async function updateDocument(
  doctype: string,
  name: string,
  values: DocValues
): Promise<DocValues> {
  const url = `/api/v2/document/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`
  
  const csrfToken = typeof window !== 'undefined' ? (window as any).csrf_token : ''
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  
  if (csrfToken) {
    headers['X-Frappe-CSRF-Token'] = csrfToken
  }

  const response = await fetch(url, {
    method: 'PUT',
    headers,
    body: JSON.stringify(values),
    credentials: 'include',
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to update document' }))
    throw new Error(error.message || `Failed to update ${doctype} ${name}`)
  }

  const data = await response.json()
  return data.data || data
}

async function createDocument(
  doctype: string,
  values: DocValues
): Promise<DocValues> {
  const url = `/api/v2/document/${encodeURIComponent(doctype)}`
  
  const csrfToken = typeof window !== 'undefined' ? (window as any).csrf_token : ''
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  
  if (csrfToken) {
    headers['X-Frappe-CSRF-Token'] = csrfToken
  }

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(values),
    credentials: 'include',
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to create document' }))
    throw new Error(error.message || `Failed to create ${doctype}`)
  }

  const data = await response.json()
  return data.data || data
}

// Hook
export function useDoctypeForm(options: UseDoctypeFormOptions) {
  const { doctype, name, initialValues, autosave = false } = options

  // State
  const [doc, setDoc] = useState<DocValues | null>(null)
  const [initialDoc, setInitialDoc] = useState<DocValues | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([])

  // Check if form is dirty
  const isDirty = doc !== null && initialDoc !== null && 
    JSON.stringify(doc) !== JSON.stringify(initialDoc)

  // Load document
  const loadDoc = useCallback(async () => {
    if (!doctype || !name) {
      // New document mode - use initial values
      if (initialValues) {
        setDoc(initialValues)
        setInitialDoc(initialValues)
      }
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const docData = await fetchDocument(doctype, name)
      setDoc(docData)
      setInitialDoc({ ...docData })
    } catch (err: any) {
      console.error(`Failed to fetch ${doctype} ${name}:`, err)
      setError(err.message || 'Failed to load document')
    } finally {
      setIsLoading(false)
    }
  }, [doctype, name, initialValues])

  useEffect(() => {
    loadDoc()
  }, [loadDoc])

  // Update field value
  const updateField = useCallback((fieldname: string, value: unknown) => {
    setDoc(prev => {
      if (!prev) return { [fieldname]: value }
      return { ...prev, [fieldname]: value }
    })
    // Clear validation error for this field
    setValidationErrors(prev => prev.filter(e => e.field !== fieldname))
  }, [])

  // Reset to initial values
  const reset = useCallback(() => {
    if (initialDoc) {
      setDoc({ ...initialDoc })
      setValidationErrors([])
    }
  }, [initialDoc])

  // Validate form
  const validate = useCallback((values: DocValues, fields: DocField[]): ValidationError[] => {
    const errors: ValidationError[] = []

    for (const field of fields) {
      const value = values[field.fieldname]

      // Required check
      if (field.reqd && (value === null || value === undefined || value === '')) {
        errors.push({
          field: field.fieldname,
          message: `${field.label} is required`,
        })
      }

      // Type-specific validation
      if (value !== null && value !== undefined && value !== '') {
        switch (field.fieldtype) {
          case 'Int':
          case 'Float':
          case 'Currency':
            if (typeof value !== 'number' && isNaN(Number(value))) {
              errors.push({
                field: field.fieldname,
                message: `${field.label} must be a number`,
              })
            }
            break
          case 'Data':
            if (typeof value === 'string' && value.length > 140) {
              errors.push({
                field: field.fieldname,
                message: `${field.label} is too long (max 140 characters)`,
              })
            }
            break
        }
      }
    }

    return errors
  }, [])

  // Save document
  const save = useCallback(async (fields?: DocField[]): Promise<boolean> => {
    if (!doc) return false

    // Validate if fields provided
    if (fields && fields.length > 0) {
      const errors = validate(doc, fields)
      if (errors.length > 0) {
        setValidationErrors(errors)
        return false
      }
    }

    setIsSaving(true)
    setSaveError(null)

    try {
      let updatedDoc: DocValues

      if (name) {
        // Update existing document
        updatedDoc = await updateDocument(doctype, name, doc)
      } else {
        // Create new document
        updatedDoc = await createDocument(doctype, doc)
      }

      setDoc(updatedDoc)
      setInitialDoc({ ...updatedDoc })
      options.onSaveSuccess?.(updatedDoc)
      return true
    } catch (err: any) {
      console.error(`Failed to save ${doctype}:`, err)
      const errorMessage = err.message || 'Failed to save document'
      setSaveError(errorMessage)
      options.onSaveError?.(errorMessage)
      return false
    } finally {
      setIsSaving(false)
    }
  }, [doctype, name, doc, options])

  // Get validation error for a specific field
  const getFieldError = useCallback((fieldname: string): string | null => {
    const error = validationErrors.find(e => e.field === fieldname)
    return error?.message || null
  }, [validationErrors])

  // Clear all errors
  const clearErrors = useCallback(() => {
    setValidationErrors([])
    setSaveError(null)
  }, [])

  return {
    // Data
    doc,
    initialDoc,
    
    // State
    isLoading,
    isSaving,
    isDirty,
    error,
    saveError,
    validationErrors,
    
    // Actions
    updateField,
    reset,
    save,
    reload: loadDoc,
    clearErrors,
    getFieldError,
  }
}

// Helper to determine if a field should be editable
export function isFieldEditable(
  field: DocField,
  hasWritePermission: boolean = true
): boolean {
  // Read-only fields are never editable
  if (field.read_only) return false
  
  // Checkboxes and certain types can always be editable if not read-only
  const alwaysEditable = ['Check']
  if (alwaysEditable.includes(field.fieldtype)) return hasWritePermission
  
  // Default: editable if user has write permission
  return hasWritePermission
}

// Helper to get default value for a field type
export function getDefaultValue(field: DocField): unknown {
  switch (field.fieldtype) {
    case 'Check':
      return 0
    case 'Int':
    case 'Float':
    case 'Currency':
      return 0
    case 'Data':
    case 'Text':
    case 'Small Text':
    case 'Long Text':
      return ''
    case 'Select':
      // First option is usually the default
      if (field.options_list && field.options_list.length > 0) {
        // Skip empty first option if present
        return field.options_list[0] || ''
      }
      return ''
    default:
      return null
  }
}

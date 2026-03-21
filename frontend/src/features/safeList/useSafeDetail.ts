/**
 * useSafeDetail - Hook for fetching and managing safe detail data using server-driven approach.
 * 
 * This hook uses the safe_list_api backend which normalizes all values
 * into safe renderable strings, preventing React runtime crashes.
 * 
 * Supports:
 * - Reading document details
 * - Creating new documents
 * - Updating existing documents
 * - Deleting documents
 */

import { useState, useEffect, useCallback } from 'react'
import {
  SafeDetailSchema,
  SafeDetailDoc,
  SafeDetailField
} from '../../utils/renderValue'

interface UseSafeDetailOptions {
  doctype: string | null
  name: string | null
  enabled?: boolean
}

interface UseSafeDetailResult {
  schema: SafeDetailSchema | null
  doc: SafeDetailDoc | null
  fields: SafeDetailField[]
  displayValues: Record<string, string>
  values: Record<string, any>
  canWrite: boolean
  canDelete: boolean
  canCreate: boolean
  isLoading: boolean
  isSaving: boolean
  isDeleting: boolean
  error: string | null
  isPermissionError: boolean
  refresh: () => void
  createDoc: (values: Record<string, any>) => Promise<{ success: boolean; name?: string; error?: string }>
  updateDoc: (values: Record<string, any>) => Promise<{ success: boolean; name?: string; error?: string }>
  deleteDoc: () => Promise<{ success: boolean; error?: string }>
}

// Get CSRF token from window (set by Frappe during page load)
function getCSRFToken(): string {
  return typeof window !== 'undefined' ? (window as Window & { csrf_token?: string }).csrf_token || '' : ''
}

// API functions with CSRF token handling
async function fetchSafeDetailSchema(doctype: string): Promise<SafeDetailSchema> {
  const url = '/api/method/scanifyme.api.safe_list_api.get_safe_detail_schema'
  const csrfToken = getCSRFToken()
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  }
  
  if (csrfToken) {
    headers['X-Frappe-CSRF-Token'] = csrfToken
  }
  
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ doctype }),
    credentials: 'include'
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to fetch schema' }))
    throw new Error(error.message || `Failed to fetch schema for ${doctype}`)
  }

  const data = await response.json()
  return data.message as SafeDetailSchema
}

async function fetchSafeDetailDoc(doctype: string, name: string): Promise<SafeDetailDoc> {
  const url = '/api/method/scanifyme.api.safe_list_api.get_safe_detail_doc'
  const csrfToken = getCSRFToken()
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  }
  
  if (csrfToken) {
    headers['X-Frappe-CSRF-Token'] = csrfToken
  }
  
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ doctype, name }),
    credentials: 'include'
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to fetch document' }))
    throw new Error(error.message || `Failed to fetch ${name} in ${doctype}`)
  }

  const data = await response.json()
  return data.message as SafeDetailDoc
}

async function createSafeDoc(
  doctype: string, 
  values: Record<string, any>
): Promise<{ success: boolean; name?: string; error?: string }> {
  const url = '/api/method/scanifyme.api.safe_list_api.create_safe_doc'
  const csrfToken = getCSRFToken()
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  }
  
  if (csrfToken) {
    headers['X-Frappe-CSRF-Token'] = csrfToken
  }
  
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ doctype, values: JSON.stringify(values) }),
    credentials: 'include'
  })

  const data = await response.json()
  
  if (data.exc) {
    // Frappe exception format
    try {
      const exc = JSON.parse(data.exc)
      const errorMsg = exc[0]?.message || data._server_messages ? JSON.parse(data._server_messages)[0]?.message : 'Failed to create document'
      return { success: false, error: errorMsg }
    } catch {
      return { success: false, error: 'Failed to create document' }
    }
  }
  
  return data.message || { success: false, error: 'Invalid response' }
}

async function updateSafeDoc(
  doctype: string, 
  name: string,
  values: Record<string, any>
): Promise<{ success: boolean; name?: string; error?: string }> {
  const url = '/api/method/scanifyme.api.safe_list_api.update_safe_doc'
  const csrfToken = getCSRFToken()
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  }
  
  if (csrfToken) {
    headers['X-Frappe-CSRF-Token'] = csrfToken
  }
  
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ doctype, name, values: JSON.stringify(values) }),
    credentials: 'include'
  })

  const data = await response.json()
  
  if (data.exc) {
    // Frappe exception format
    try {
      const exc = JSON.parse(data.exc)
      const errorMsg = exc[0]?.message || data._server_messages ? JSON.parse(data._server_messages)[0]?.message : 'Failed to update document'
      return { success: false, error: errorMsg }
    } catch {
      return { success: false, error: 'Failed to update document' }
    }
  }
  
  return data.message || { success: false, error: 'Invalid response' }
}

async function deleteSafeDoc(
  doctype: string, 
  name: string
): Promise<{ success: boolean; error?: string }> {
  const url = '/api/method/scanifyme.api.safe_list_api.delete_safe_doc'
  const csrfToken = getCSRFToken()
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  }
  
  if (csrfToken) {
    headers['X-Frappe-CSRF-Token'] = csrfToken
  }
  
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ doctype, name }),
    credentials: 'include'
  })

  const data = await response.json()
  
  if (data.exc) {
    // Frappe exception format
    try {
      const exc = JSON.parse(data.exc)
      const errorMsg = exc[0]?.message || data._server_messages ? JSON.parse(data._server_messages)[0]?.message : 'Failed to delete document'
      return { success: false, error: errorMsg }
    } catch {
      return { success: false, error: 'Failed to delete document' }
    }
  }
  
  return data.message || { success: false, error: 'Invalid response' }
}

export function useSafeDetail(options: UseSafeDetailOptions) {
  const { doctype, name, enabled = true } = options
  
  const [schema, setSchema] = useState<SafeDetailSchema | null>(null)
  const [doc, setDoc] = useState<SafeDetailDoc | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isPermissionError, setIsPermissionError] = useState(false)

  const loadData = useCallback(async () => {
    if (!doctype || !name || !enabled) return

    setIsLoading(true)
    setError(null)
    setIsPermissionError(false)

    try {
      // Fetch schema
      const schemaData = await fetchSafeDetailSchema(doctype)
      setSchema(schemaData)

      // Fetch doc
      const docData = await fetchSafeDetailDoc(doctype, name)
      setDoc(docData)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load document'
      
      // Check if it's a permission error
      const isPermError = message.toLowerCase().includes('permission') || 
                         message.toLowerCase().includes('denied')
      setIsPermissionError(isPermError)
      
      setError(message)
      console.error(`Failed to load detail for ${doctype}/${name}:`, err)
    } finally {
      setIsLoading(false)
    }
  }, [doctype, name, enabled])

  useEffect(() => {
    loadData()
  }, [loadData])

  const refresh = useCallback(() => {
    loadData()
  }, [loadData])

  const createDoc = useCallback(async (values: Record<string, any>) => {
    if (!doctype) {
      return { success: false, error: 'DocType is required' }
    }
    
    setIsSaving(true)
    setError(null)
    
    try {
      const result = await createSafeDoc(doctype, values)
      
      if (!result.success) {
        setError(result.error || 'Failed to create document')
      }
      
      return result
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to create document'
      setError(errorMsg)
      return { success: false, error: errorMsg }
    } finally {
      setIsSaving(false)
    }
  }, [doctype])

  const updateDoc = useCallback(async (values: Record<string, any>) => {
    if (!doctype || !name) {
      return { success: false, error: 'DocType and name are required' }
    }
    
    setIsSaving(true)
    setError(null)
    
    try {
      const result = await updateSafeDoc(doctype, name, values)
      
      if (!result.success) {
        setError(result.error || 'Failed to update document')
      } else {
        // Refresh data after successful update
        await loadData()
      }
      
      return result
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to update document'
      setError(errorMsg)
      return { success: false, error: errorMsg }
    } finally {
      setIsSaving(false)
    }
  }, [doctype, name, loadData])

  const deleteDoc = useCallback(async () => {
    if (!doctype || !name) {
      return { success: false, error: 'DocType and name are required' }
    }
    
    setIsDeleting(true)
    setError(null)
    
    try {
      const result = await deleteSafeDoc(doctype, name)
      
      if (!result.success) {
        setError(result.error || 'Failed to delete document')
      }
      
      return result
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to delete document'
      setError(errorMsg)
      return { success: false, error: errorMsg }
    } finally {
      setIsDeleting(false)
    }
  }, [doctype, name])

  return {
    schema,
    doc,
    fields: schema?.fields || [],
    displayValues: doc?.display_values || {},
    values: doc?.values || {},
    canWrite: doc?.permissions?.can_write ?? false,
    canDelete: schema?.permissions?.can_delete ?? false,
    canCreate: schema?.permissions?.can_create ?? false,
    isLoading,
    isSaving,
    isDeleting,
    error,
    isPermissionError,
    refresh,
    createDoc,
    updateDoc,
    deleteDoc
  }
}

// Hook for creating new documents (without loading existing doc)
export function useSafeCreate(doctype: string | null) {
  const [schema, setSchema] = useState<SafeDetailSchema | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadSchema = useCallback(async () => {
    if (!doctype) return

    setIsLoading(true)
    setError(null)

    try {
      const schemaData = await fetchSafeDetailSchema(doctype)
      setSchema(schemaData)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load schema'
      setError(message)
      console.error(`Failed to load schema for ${doctype}:`, err)
    } finally {
      setIsLoading(false)
    }
  }, [doctype])

  useEffect(() => {
    loadSchema()
  }, [loadSchema])

  const createDoc = useCallback(async (values: Record<string, any>) => {
    if (!doctype) {
      return { success: false, error: 'DocType is required' }
    }
    
    setIsSaving(true)
    setError(null)
    
    try {
      const result = await createSafeDoc(doctype, values)
      
      if (!result.success) {
        setError(result.error || 'Failed to create document')
      }
      
      return result
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to create document'
      setError(errorMsg)
      return { success: false, error: errorMsg }
    } finally {
      setIsSaving(false)
    }
  }, [doctype])

  return {
    schema,
    fields: schema?.fields || [],
    canCreate: schema?.permissions?.can_create ?? false,
    isLoading,
    isSaving,
    error,
    refresh: loadSchema,
    createDoc
  }
}

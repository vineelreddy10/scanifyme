/**
 * useSafeDetail - Hook for fetching safe detail data using server-driven approach.
 * 
 * This hook uses the safe_list_api backend which normalizes all values
 * into safe renderable strings, preventing React runtime crashes.
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
  canWrite: boolean
  isLoading: boolean
  error: string | null
  isPermissionError: boolean
  refresh: () => void
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

export function useSafeDetail(options: UseSafeDetailOptions) {
  const { doctype, name, enabled = true } = options
  
  const [schema, setSchema] = useState<SafeDetailSchema | null>(null)
  const [doc, setDoc] = useState<SafeDetailDoc | null>(null)
  const [isLoading, setIsLoading] = useState(false)
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

  return {
    schema,
    doc,
    fields: schema?.fields || [],
    displayValues: doc?.display_values || {},
    canWrite: doc?.permissions?.can_write ?? false,
    isLoading,
    error,
    isPermissionError,
    refresh
  }
}

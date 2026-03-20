/**
 * useDoctypeMeta - Hook to fetch and cache DocType metadata.
 * 
 * Provides field definitions, labels, types, and list view configuration
 * for building generic list/detail pages.
 */

import { useState, useEffect, useCallback } from 'react'

// Types
export interface DocTypeField {
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

export interface DocTypeMeta {
  name: string
  label: string
  fields: DocTypeField[]
  title_field: string | null
  sort_field: string
  sort_order: 'ASC' | 'DESC'
  editable_grid: boolean
}

// API function
async function fetchDoctypeMeta(doctype: string): Promise<DocTypeMeta> {
  const baseURL = ''
  const url = baseURL ? `${baseURL}/api/method/scanifyme.api.metadata_api.get_doctype_meta` : `/api/method/scanifyme.api.metadata_api.get_doctype_meta`
  
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
    body: JSON.stringify({ doctype }),
    credentials: 'include',
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || `Failed to fetch metadata for ${doctype}`)
  }

  const data = await response.json()
  return data.message as DocTypeMeta
}

// Simple cache
const metaCache = new Map<string, { meta: DocTypeMeta; timestamp: number }>()
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

function getCachedMeta(doctype: string): DocTypeMeta | null {
  const cached = metaCache.get(doctype)
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.meta
  }
  return null
}

function setCachedMeta(doctype: string, meta: DocTypeMeta): void {
  metaCache.set(doctype, { meta, timestamp: Date.now() })
}

// Hook
export function useDoctypeMeta(doctype: string | null) {
  const [meta, setMeta] = useState<DocTypeMeta | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadMeta = useCallback(async () => {
    if (!doctype) {
      setMeta(null)
      setError(null)
      return
    }

    // Check cache first
    const cached = getCachedMeta(doctype)
    if (cached) {
      setMeta(cached)
      setIsLoading(false)
      setError(null)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const metaData = await fetchDoctypeMeta(doctype)
      setCachedMeta(doctype, metaData)
      setMeta(metaData)
    } catch (err: any) {
      console.error(`Failed to fetch metadata for ${doctype}:`, err)
      setError(err.message || `Failed to load metadata for ${doctype}`)
      setMeta(null)
    } finally {
      setIsLoading(false)
    }
  }, [doctype])

  useEffect(() => {
    loadMeta()
  }, [loadMeta])

  const refresh = useCallback(() => {
    if (doctype) {
      metaCache.delete(doctype)
      loadMeta()
    }
  }, [doctype, loadMeta])

  return {
    meta,
    isLoading,
    error,
    refresh,
  }
}

// Helper to get list view fields from metadata
export function getListViewFields(meta: DocTypeMeta | null): DocTypeField[] {
  if (!meta) return []
  return meta.fields.filter(f => f.in_list_view)
}

// Helper to get filterable fields from metadata
export function getFilterFields(meta: DocTypeMeta | null): DocTypeField[] {
  if (!meta) return []
  return meta.fields.filter(f => f.in_standard_filter)
}

// Helper to get sortable fields from metadata
export function getSortableFields(meta: DocTypeMeta | null): DocTypeField[] {
  if (!meta) return []
  // All fields are potentially sortable, but prefer those in list view
  return meta.fields.filter(f => f.in_list_view || f.fieldtype !== 'Table')
}

// Format field value for display
export function formatFieldValue(value: unknown, field: DocTypeField): string {
  if (value === null || value === undefined) return '-'
  
  switch (field.fieldtype) {
    case 'Check':
      return value ? 'Yes' : 'No'
    case 'Datetime':
    case 'Date':
      if (typeof value === 'string') {
        const date = new Date(value)
        if (isNaN(date.getTime())) return String(value)
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        })
      }
      return String(value)
    case 'Currency':
    case 'Float':
    case 'Int':
      if (typeof value === 'number') {
        return value.toLocaleString()
      }
      return String(value)
    case 'Link':
      return String(value).split('.').pop() || String(value)
    default:
      return String(value)
  }
}

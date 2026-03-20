/**
 * useSafeList - Hook for fetching safe list data using server-driven approach.
 * 
 * This hook uses the safe_list_api backend which normalizes all values
 * into safe renderable strings, preventing React runtime crashes.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  SafeListSchema,
  SafeListResponse,
  SafeListRow,
  SafeListColumn
} from '../../utils/renderValue'

interface UseSafeListOptions {
  doctype: string | null
  pageSize?: number
  enabled?: boolean
}

interface UseSafeListResult {
  schema: SafeListSchema | null
  rows: SafeListRow[]
  columns: SafeListColumn[]
  totalCount: number
  page: number
  pageSize: number
  totalPages: number
  isLoading: boolean
  error: string | null
  refresh: () => void
  goToPage: (page: number) => void
  setPageSize: (size: number) => void
}

// Get CSRF token from window (set by Frappe during page load)
function getCSRFToken(): string {
  return typeof window !== 'undefined' ? (window as Window & { csrf_token?: string }).csrf_token || '' : ''
}

// API functions with CSRF token handling
async function fetchSafeListSchema(doctype: string): Promise<SafeListSchema> {
  const url = '/api/method/scanifyme.api.safe_list_api.get_safe_list_schema'
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
  return data.message as SafeListSchema
}

async function fetchSafeListRows(
  doctype: string,
  page: number,
  pageSize: number
): Promise<SafeListResponse> {
  const url = '/api/method/scanifyme.api.safe_list_api.get_safe_list_rows'
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
    body: JSON.stringify({
      doctype,
      start: (page - 1) * pageSize,
      page_length: pageSize
    }),
    credentials: 'include'
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to fetch rows' }))
    throw new Error(error.message || `Failed to fetch rows for ${doctype}`)
  }

  const data = await response.json()
  return data.message as SafeListResponse
}

export function useSafeList(options: UseSafeListOptions) {
  const { doctype, pageSize = 20, enabled = true } = options
  
  const [schema, setSchema] = useState<SafeListSchema | null>(null)
  const [rows, setRows] = useState<SafeListRow[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(1)
  const [currentPageSize, setCurrentPageSize] = useState(pageSize)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const totalPages = Math.ceil(totalCount / currentPageSize) || 1

  const loadData = useCallback(async () => {
    if (!doctype || !enabled) return

    setIsLoading(true)
    setError(null)

    try {
      // Fetch schema
      const schemaData = await fetchSafeListSchema(doctype)
      setSchema(schemaData)

      // Fetch rows
      const rowsData = await fetchSafeListRows(doctype, page, currentPageSize)
      setRows(rowsData.rows)
      setTotalCount(rowsData.total_count)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load data'
      setError(message)
      console.error(`Failed to load list for ${doctype}:`, err)
    } finally {
      setIsLoading(false)
    }
  }, [doctype, enabled, page, currentPageSize])

  useEffect(() => {
    loadData()
  }, [loadData])

  const refresh = useCallback(() => {
    loadData()
  }, [loadData])

  const goToPage = useCallback((newPage: number) => {
    setPage(newPage)
  }, [])

  const setPageSize = useCallback((size: number) => {
    setCurrentPageSize(size)
    setPage(1)
  }, [])

  return {
    schema,
    rows,
    columns: schema?.columns || [],
    totalCount,
    page,
    pageSize: currentPageSize,
    totalPages,
    isLoading,
    error,
    refresh,
    goToPage,
    setPageSize
  }
}

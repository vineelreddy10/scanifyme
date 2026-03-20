/**
 * useDoctypeList - Hook for fetching DocType document lists with filters, sort, and pagination.
 * 
 * Features:
 * - URL state sync for shareable list state
 * - Optional local persistence for list preferences
 * - Selection state for bulk actions
 * 
 * Uses the Frappe REST API v2: GET /api/v2/document/{doctype}
 * with query params: fields, filters, order_by, limit_page_length, limit_start
 */

import { useState, useEffect, useCallback, useRef } from 'react'

// Types
export type FilterOperator = '=' | '!=' | '>' | '<' | '>=' | '<=' | 'like' | 'in' | 'not in' | 'between' | 'is'

export interface FilterCondition {
  fieldname: string
  operator: FilterOperator
  value: unknown
}

export interface SortConfig {
  fieldname: string
  direction: 'asc' | 'desc'
}

export interface ListParams {
  doctype: string
  fields?: string[]
  filters?: FilterCondition[]
  sort?: SortConfig
  page?: number
  pageSize?: number
}

// URL State Management
const URL_PARAM_KEYS = {
  page: 'page',
  pageSize: 'page_size',
  sort: 'sort',
  filters: 'filters',
} as const

function parseUrlState(): Partial<{
  page: number
  pageSize: number
  sort: SortConfig
  filters: FilterCondition[]
}> {
  if (typeof window === 'undefined') return {}
  
  const params = new URLSearchParams(window.location.search)
  const result: Partial<{
    page: number
    pageSize: number
    sort: SortConfig
    filters: FilterCondition[]
  }> = {}
  
  const page = params.get(URL_PARAM_KEYS.page)
  if (page) result.page = parseInt(page, 10)
  
  const pageSize = params.get(URL_PARAM_KEYS.pageSize)
  if (pageSize) result.pageSize = parseInt(pageSize, 10)
  
  const sort = params.get(URL_PARAM_KEYS.sort)
  if (sort) {
    const [fieldname, direction] = sort.split(':')
    if (fieldname && (direction === 'asc' || direction === 'desc')) {
      result.sort = { fieldname, direction }
    }
  }
  
  const filters = params.get(URL_PARAM_KEYS.filters)
  if (filters) {
    try {
      result.filters = JSON.parse(decodeURIComponent(filters))
    } catch {
      result.filters = []
    }
  }
  
  return result
}

function buildUrlParams(state: {
  page?: number
  pageSize?: number
  sort?: SortConfig
  filters?: FilterCondition[]
}): URLSearchParams {
  const params = new URLSearchParams()
  
  if (state.page && state.page > 1) {
    params.set(URL_PARAM_KEYS.page, String(state.page))
  }
  if (state.pageSize && state.pageSize !== 20) {
    params.set(URL_PARAM_KEYS.pageSize, String(state.pageSize))
  }
  if (state.sort) {
    params.set(URL_PARAM_KEYS.sort, `${state.sort.fieldname}:${state.sort.direction}`)
  }
  if (state.filters && state.filters.length > 0) {
    params.set(URL_PARAM_KEYS.filters, encodeURIComponent(JSON.stringify(state.filters)))
  }
  
  return params
}

// Local Storage for persistence
const STORAGE_KEY_PREFIX = 'scanifyme_list_'

function getStorageKey(doctype: string): string {
  return `${STORAGE_KEY_PREFIX}${doctype}_prefs`
}

interface LocalPrefs {
  pageSize?: number
  sort?: SortConfig
}

function loadLocalPrefs(doctype: string): LocalPrefs {
  if (typeof window === 'undefined') return {}
  
  try {
    const stored = localStorage.getItem(getStorageKey(doctype))
    return stored ? JSON.parse(stored) : {}
  } catch {
    return {}
  }
}

function saveLocalPrefs(doctype: string, prefs: LocalPrefs): void {
  if (typeof window === 'undefined') return
  
  try {
    localStorage.setItem(getStorageKey(doctype), JSON.stringify(prefs))
  } catch {
    // Ignore storage errors
  }
}

export interface ListResponse {
  data: Record<string, unknown>[]
  totalCount: number
  page: number
  pageSize: number
  totalPages: number
}

// API function using Frappe REST API v2
async function fetchDoctypeList(params: ListParams): Promise<ListResponse> {
  const { doctype, fields = ['name'], filters = [], sort, page = 1, pageSize = 20 } = params
  
  // Build URL with query params
  const url = new URL(`/api/v2/document/${encodeURIComponent(doctype)}`, window.location.origin)
  
  // Add fields
  if (fields.length > 0) {
    url.searchParams.set('fields', JSON.stringify(fields))
  }
  
  // Add filters
  if (filters.length > 0) {
    const filterTuples = filters.map(f => [f.fieldname, f.operator, f.value] as [string, string, unknown])
    url.searchParams.set('filters', JSON.stringify(filterTuples))
  }
  
  // Add sorting
  if (sort) {
    url.searchParams.set('order_by', `${sort.fieldname} ${sort.direction}`)
  }
  
  // Add pagination
  url.searchParams.set('limit_page_length', String(pageSize))
  url.searchParams.set('limit_start', String((page - 1) * pageSize))
  
  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to fetch list' }))
    throw new Error(error.message || `Failed to fetch list for ${doctype}`)
  }
  
  const data = await response.json()
  
  // Calculate total pages (estimate from response)
  const docs = data.data || []
  const totalCount = data.total_count || docs.length || 0
  
  return {
    data: docs,
    totalCount,
    page,
    pageSize,
    totalPages: Math.ceil(totalCount / pageSize) || 1,
  }
}

// Alternative: Use our backend API which returns total_count directly
async function fetchDoctypeListViaAPI(params: ListParams): Promise<ListResponse> {
  const { doctype, fields = ['name'], filters = [], sort, page = 1, pageSize = 20 } = params
  
  const baseURL = ''
  const url = baseURL ? `${baseURL}/api/method/scanifyme.api.metadata_api.get_doctype_list` : '/api/method/scanifyme.api.metadata_api.get_doctype_list'
  
  const csrfToken = typeof window !== 'undefined' ? (window as any).csrf_token : ''
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  
  if (csrfToken) {
    headers['X-Frappe-CSRF-Token'] = csrfToken
  }
  
  // Build filter tuples for backend
  const filterTuples = filters.map(f => [f.fieldname, f.operator, f.value])
  
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      doctype,
      fields: JSON.stringify(fields),
      filters: JSON.stringify(filterTuples),
      order_by: sort ? `${sort.fieldname} ${sort.direction}` : undefined,
      limit_start: (page - 1) * pageSize,
      limit_page_length: pageSize,
    }),
    credentials: 'include',
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to fetch list' }))
    throw new Error(error.message || `Failed to fetch list for ${doctype}`)
  }
  
  const data = await response.json()
  const result = data.message
  
  return {
    data: result.data || [],
    totalCount: result.total_count || 0,
    page,
    pageSize,
    totalPages: Math.ceil((result.total_count || 0) / pageSize) || 1,
  }
}

// Selection state management
export interface SelectionState {
  selectedRows: Set<string>
  selectRow: (name: string, selected: boolean) => void
  selectAll: (names: string[], selected: boolean) => void
  clearSelection: () => void
  isSelected: (name: string) => boolean
  toggleSelect: (name: string) => void
}

export function useSelectionState(): SelectionState {
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set())
  
  return {
    selectedRows,
    selectRow: useCallback((name: string, selected: boolean) => {
      setSelectedRows(prev => {
        const next = new Set(prev)
        if (selected) {
          next.add(name)
        } else {
          next.delete(name)
        }
        return next
      })
    }, []),
    selectAll: useCallback((names: string[], selected: boolean) => {
      if (selected) {
        setSelectedRows(new Set(names))
      } else {
        setSelectedRows(new Set())
      }
    }, []),
    clearSelection: useCallback(() => {
      setSelectedRows(new Set())
    }, []),
    isSelected: useCallback((name: string) => selectedRows.has(name), [selectedRows]),
    toggleSelect: useCallback((name: string) => {
      setSelectedRows(prev => {
        const next = new Set(prev)
        if (next.has(name)) {
          next.delete(name)
        } else {
          next.add(name)
        }
        return next
      })
    }, []),
  }
}

// URL sync state hook
export interface UrlSyncState {
  syncToUrl: boolean
  setSyncToUrl: (value: boolean) => void
}

export function useUrlSync(params: {
  page?: number
  pageSize?: number
  sort?: SortConfig
  filters?: FilterCondition[]
}) {
  const [syncToUrl, setSyncToUrl] = useState(true)
  const isInitialMount = useRef(true)
  
  useEffect(() => {
    if (!syncToUrl || typeof window === 'undefined') return
    
    if (isInitialMount.current) {
      isInitialMount.current = false
      return
    }
    
    const params_to_sync = {
      page: params.page,
      pageSize: params.pageSize,
      sort: params.sort,
      filters: params.filters,
    }
    
    const newParams = buildUrlParams(params_to_sync)
    const newUrl = newParams.toString()
      ? `${window.location.pathname}?${newParams.toString()}`
      : window.location.pathname
    
    window.history.replaceState(null, '', newUrl)
  }, [params.page, params.pageSize, params.sort, params.filters, syncToUrl])
  
  return { syncToUrl, setSyncToUrl }
}

// Hook
export function useDoctypeList(params: ListParams & { syncToUrl?: boolean } = { doctype: '', syncToUrl: true }) {
  const { syncToUrl = true, ...restParams } = params
  
  const [data, setData] = useState<Record<string, unknown>[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // URL state and local prefs
  const urlState = parseUrlState()
  const localPrefs = loadLocalPrefs(params.doctype)
  
  const [page, setPage] = useState(params.page || urlState.page || 1)
  const [pageSize, setPageSize] = useState(params.pageSize || urlState.pageSize || localPrefs.pageSize || 20)
  const [filters, setFilters] = useState<FilterCondition[]>(params.filters || urlState.filters || [])
  const [sort, setSort] = useState<SortConfig | undefined>(params.sort || urlState.sort || localPrefs.sort)
  const [searchQuery, setSearchQuery] = useState('')
  
  const loadList = useCallback(async () => {
    if (!params.doctype) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      const result = await fetchDoctypeListViaAPI({
        ...params,
        doctype: params.doctype,
        page,
        pageSize,
        filters,
        sort,
      })
      
      setData(result.data)
      setTotalCount(result.totalCount)
    } catch (err: any) {
      console.error(`Failed to fetch list for ${params.doctype}:`, err)
      setError(err.message || 'Failed to load data')
      setData([])
      setTotalCount(0)
    } finally {
      setIsLoading(false)
    }
  }, [params.doctype, page, pageSize, filters, sort, params.fields])
  
  // URL sync effect
  useUrlSync({ page, pageSize, sort, filters })
  
  // Persist preferences to localStorage
  useEffect(() => {
    saveLocalPrefs(params.doctype, { pageSize, sort })
  }, [params.doctype, pageSize, sort])
  
  // Initial load and refetch on param changes
  useEffect(() => {
    loadList()
  }, [loadList])
  
  // Pagination helpers
  const goToPage = useCallback((newPage: number) => {
    setPage(newPage)
  }, [])
  
  const nextPage = useCallback(() => {
    setPage(p => p + 1)
  }, [])
  
  const prevPage = useCallback(() => {
    setPage(p => Math.max(1, p - 1))
  }, [])
  
  const changePageSize = useCallback((newSize: number) => {
    setPageSize(newSize)
    setPage(1) // Reset to first page
  }, [])
  
  // Filter helpers
  const addFilter = useCallback((filter: FilterCondition) => {
    setFilters(prev => [...prev, filter])
    setPage(1)
  }, [])
  
  const removeFilter = useCallback((fieldname: string) => {
    setFilters(prev => prev.filter(f => f.fieldname !== fieldname))
    setPage(1)
  }, [])
  
  const clearFilters = useCallback(() => {
    setFilters([])
    setPage(1)
  }, [])
  
  const updateFilter = useCallback((fieldname: string, value: unknown) => {
    setFilters(prev => 
      prev.map(f => f.fieldname === fieldname ? { ...f, value } : f)
    )
    setPage(1)
  }, [])
  
  // Sort helpers
  const updateSort = useCallback((fieldname: string, direction?: 'asc' | 'desc') => {
    if (direction) {
      setSort({ fieldname, direction })
    } else {
      // Toggle direction
      setSort(prev => {
        if (prev?.fieldname === fieldname) {
          return { fieldname, direction: prev.direction === 'asc' ? 'desc' : 'asc' }
        }
        return { fieldname, direction: 'asc' }
      })
    }
  }, [])
  
  const clearSort = useCallback(() => {
    setSort(undefined)
  }, [])
  
  // Search - adds a filter for searchable fields
  useEffect(() => {
    if (!searchQuery.trim()) {
      // Remove search filter if search is cleared
      setFilters(prev => prev.filter(f => f.fieldname !== '_search'))
      return
    }
    
    // Add search filter (searches across all relevant fields)
    setFilters(prev => {
      const withoutSearch = prev.filter(f => f.fieldname !== '_search')
      return [...withoutSearch, { fieldname: '_search', operator: 'like', value: `%${searchQuery}%` }]
    })
    setPage(1)
  }, [searchQuery])
  
  return {
    // Data
    data,
    totalCount,
    
    // State
    isLoading,
    error,
    
    // Pagination
    page,
    pageSize,
    totalPages: Math.ceil(totalCount / pageSize) || 1,
    goToPage,
    nextPage,
    prevPage,
    changePageSize,
    
    // Filters
    filters,
    addFilter,
    removeFilter,
    clearFilters,
    updateFilter,
    
    // Sort
    sort,
    updateSort,
    clearSort,
    
    // Search
    searchQuery,
    setSearchQuery,
    
    // Actions
    refresh: loadList,
  }
}

// Helper to build filter from field value
export function buildFilter(
  fieldname: string,
  operator: FilterOperator,
  value: unknown
): FilterCondition {
  return { fieldname, operator, value }
}

// Helper to check if value is empty (for clearing filters)
export function isEmpty(value: unknown): boolean {
  if (value === null || value === undefined) return true
  if (typeof value === 'string' && value.trim() === '') return true
  if (Array.isArray(value) && value.length === 0) return true
  return false
}

// Serialization helpers for URL/localStorage
export function serializeSort(sort?: SortConfig): string | undefined {
  return sort ? `${sort.fieldname}:${sort.direction}` : undefined
}

export function deserializeSort(str?: string): SortConfig | undefined {
  if (!str) return undefined
  const [fieldname, direction] = str.split(':')
  if (fieldname && (direction === 'asc' || direction === 'desc')) {
    return { fieldname, direction }
  }
  return undefined
}

export function serializeFilters(filters: FilterCondition[]): string {
  return encodeURIComponent(JSON.stringify(filters))
}

export function deserializeFilters(str: string): FilterCondition[] {
  try {
    return JSON.parse(decodeURIComponent(str))
  } catch {
    return []
  }
}

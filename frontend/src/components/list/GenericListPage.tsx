/**
 * GenericListPage - Server-driven list page for DocTypes.
 * 
 * This component uses the safe_list_api backend which normalizes all values
 * into safe renderable strings, preventing React runtime crashes.
 */

import { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSafeList } from '../../features/safeList/useSafeList'
import { AppLayout, PageHeader, Content } from '../ui'
import { DynamicErrorBoundary } from '../errors/DynamicPageErrorBoundary'
import { 
  SafeListColumn, 
  SafeListRow,
  getColumnWidth,
  getBooleanClass,
  getLinkClass,
  getEmptyClass
} from '../../utils/renderValue'

interface GenericListPageProps {
  doctype: string
  detailRoutePrefix?: string
  title?: string
}

export function GenericListPage({
  doctype,
  detailRoutePrefix,
  title
}: GenericListPageProps) {
  const navigate = useNavigate()
  
  const [searchInput, setSearchInput] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [sortField, setSortField] = useState<string | null>(null)
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
  const [showSortMenu, setShowSortMenu] = useState(false)
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  const {
    schema,
    rows,
    columns,
    totalCount,
    page,
    pageSize,
    totalPages,
    isLoading,
    error,
    isPermissionError,
    refresh,
    goToPage,
    setPageSize
  } = useSafeList({
    doctype: doctype || null,
    pageSize: 20
  })

  const pageTitle = title || schema?.title || doctype

  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }
    searchTimeoutRef.current = setTimeout(() => {
      setDebouncedSearch(searchInput)
    }, 300)
    
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
    }
  }, [searchInput])

  const handleSort = useCallback((field: string) => {
    if (sortField === field) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder('asc')
    }
    setShowSortMenu(false)
  }, [sortField])

  const handleSearchChange = useCallback((value: string) => {
    setSearchInput(value)
  }, [])

  const filteredRows = useMemo(() => {
    if (!debouncedSearch.trim()) return rows
    const query = debouncedSearch.toLowerCase()
    return rows.filter(row => {
      return Object.values(row.display_values).some(val => 
        String(val).toLowerCase().includes(query)
      )
    })
  }, [rows, debouncedSearch])

  const sortedRows = useMemo(() => {
    if (!sortField) return filteredRows
    return [...filteredRows].sort((a, b) => {
      const aVal = a.display_values[sortField] || ''
      const bVal = b.display_values[sortField] || ''
      const comparison = aVal.localeCompare(bVal, undefined, { numeric: true })
      return sortOrder === 'asc' ? comparison : -comparison
    })
  }, [filteredRows, sortField, sortOrder])

  const handleRowClick = (row: SafeListRow) => {
    if (detailRoutePrefix) {
      navigate(`${detailRoutePrefix}/${encodeURIComponent(row.name)}`)
    }
  }

  if (isPermissionError) {
    return (
      <AppLayout>
        <PageHeader title={pageTitle} />
        <Content>
          <StateCard type="error" title="Permission Denied" description={`You don't have permission to view ${doctype}.`} />
        </Content>
      </AppLayout>
    )
  }

  if (error) {
    return (
      <AppLayout>
        <PageHeader title={pageTitle} />
        <Content>
          <StateCard type="error" title={`Error Loading ${pageTitle}`} description={error} action={{ label: 'Try Again', onClick: refresh }} />
        </Content>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <PageHeader
        title={pageTitle}
        description={schema?.title ? `Manage your ${schema.title.toLowerCase()} records` : undefined}
        actions={
          <button
            onClick={refresh}
            className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <RefreshIcon />
            Refresh
          </button>
        }
      />
      <Content>
        <div className="space-y-4">
          <ListToolbar
            searchQuery={searchInput}
            onSearchChange={handleSearchChange}
            isDebouncing={searchInput !== debouncedSearch}
            columns={columns}
            sortField={sortField}
            sortOrder={sortOrder}
            onSortChange={handleSort}
            showSortMenu={showSortMenu}
            onToggleSortMenu={() => setShowSortMenu(!showSortMenu)}
            totalCount={totalCount}
            isLoading={isLoading}
          />
          
          {isLoading ? (
            <ListTableSkeleton columns={columns} />
          ) : sortedRows.length === 0 ? (
            <EmptyState title={pageTitle} hasSearch={!!searchQuery} />
          ) : (
            <SafeListTable
              columns={columns}
              rows={sortedRows}
              onRowClick={detailRoutePrefix ? handleRowClick : undefined}
              sortField={sortField}
              sortOrder={sortOrder}
              onSort={handleSort}
            />
          )}
          
          {!isLoading && sortedRows.length > 0 && (
            <Pagination
              page={page}
              totalPages={totalPages}
              totalCount={totalCount}
              pageSize={pageSize}
              onPageChange={goToPage}
              onPageSizeChange={setPageSize}
            />
          )}
        </div>
      </Content>
    </AppLayout>
  )
}

function ListToolbar({
  searchQuery,
  onSearchChange,
  isDebouncing,
  columns,
  sortField,
  sortOrder,
  onSortChange,
  showSortMenu,
  onToggleSortMenu,
  totalCount,
  isLoading
}: {
  searchQuery: string
  onSearchChange: (value: string) => void
  isDebouncing: boolean
  columns: SafeListColumn[]
  sortField: string | null
  sortOrder: 'asc' | 'desc'
  onSortChange: (field: string) => void
  showSortMenu: boolean
  onToggleSortMenu: () => void
  totalCount: number
  isLoading: boolean
}) {
  const sortableColumns = columns.filter(c => c.fieldtype !== 'Check')

  return (
    <div className="bg-white rounded-lg border px-4 py-3">
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 max-w-md">
          <div className="relative">
            {isDebouncing ? <LoadingSpinner /> : <SearchIcon />}
            <input
              type="text"
              placeholder="Search records..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {!isLoading && (
            <span className="text-sm text-gray-500">
              <span className="font-medium text-gray-900">{totalCount}</span> records
            </span>
          )}
          
          <div className="relative">
            <button
              onClick={onToggleSortMenu}
              className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <SortIcon />
              Sort
              {sortField && (
                <span className="ml-1 px-1.5 py-0.5 text-xs bg-indigo-100 text-indigo-700 rounded">
                  {columns.find(c => c.fieldname === sortField)?.label || sortField}
                </span>
              )}
            </button>
            
            {showSortMenu && sortableColumns.length > 0 && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border z-10">
                <div className="py-1">
                  <div className="px-3 py-1.5 text-xs font-medium text-gray-500 uppercase">
                    Sort by
                  </div>
                  {sortableColumns.map(col => (
                    <button
                      key={col.fieldname}
                      onClick={() => onSortChange(col.fieldname)}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center justify-between"
                    >
                      <span>{col.label}</span>
                      {sortField === col.fieldname && (
                        <span className="text-indigo-600">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function SafeListTable({
  columns,
  rows,
  onRowClick,
  sortField,
  sortOrder,
  onSort
}: {
  columns: SafeListColumn[]
  rows: SafeListRow[]
  onRowClick?: (row: SafeListRow) => void
  sortField: string | null
  sortOrder: 'asc' | 'desc'
  onSort: (field: string) => void
}) {
  if (columns.length === 0) {
    return (
      <StateCard type="warning" title="No Configuration" description="No columns are configured for this list view." />
    )
  }

  return (
    <div className="bg-white rounded-lg border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.fieldname}
                  className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${getColumnWidth(col.fieldtype)}`}
                >
                  <button
                    onClick={() => onSort(col.fieldname)}
                    className="flex items-center gap-1 hover:text-gray-700"
                  >
                    {col.label}
                    {sortField === col.fieldname ? (
                      <span className="text-indigo-600">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    ) : (
                      <span className="text-gray-400 opacity-0 group-hover:opacity-100">↕</span>
                    )}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rows.map((row) => (
              <tr
                key={row.name}
                className={`hover:bg-gray-50 transition-colors ${onRowClick ? 'cursor-pointer' : ''}`}
                onClick={() => onRowClick?.(row)}
              >
                {columns.map((col) => {
                  const displayValue = row.display_values[col.fieldname] ?? '-'
                  const rawValue = row.values[col.fieldname]
                  
                  return (
                    <td
                      key={col.fieldname}
                      className={`px-6 py-4 whitespace-nowrap text-sm ${getEmptyClass(rawValue)}`}
                    >
                      {col.fieldtype === 'Check' ? (
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getBooleanClass(rawValue)}`}>
                          {displayValue}
                        </span>
                      ) : col.fieldtype === 'Link' ? (
                        <span className={getLinkClass()}>
                          {displayValue}
                        </span>
                      ) : (
                        <span className="truncate max-w-xs" title={String(displayValue)}>
                          {displayValue}
                        </span>
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ListTableSkeleton({ columns }: { columns: SafeListColumn[] }) {
  return (
    <div className="bg-white rounded-lg border overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col) => (
              <th key={col.fieldname} className="px-6 py-3">
                <div className="h-4 bg-gray-200 rounded animate-pulse w-20"></div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {[...Array(5)].map((_, i) => (
            <tr key={i}>
              {columns.map((col) => (
                <td key={col.fieldname} className="px-6 py-4">
                  <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function EmptyState({ title, hasSearch }: { title: string; hasSearch?: boolean }) {
  return (
    <div className="bg-white rounded-lg border p-12 text-center">
      <div className="mx-auto h-12 w-12 text-gray-400">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <h3 className="mt-4 text-lg font-medium text-gray-900">
        {hasSearch ? 'No matching records' : `No ${title}`}
      </h3>
      <p className="mt-2 text-sm text-gray-500">
        {hasSearch 
          ? 'Try adjusting your search criteria.'
          : 'Get started by creating a new record.'}
      </p>
    </div>
  )
}

function StateCard({ 
  type, 
  title, 
  description, 
  action 
}: { 
  type: 'error' | 'warning' | 'info'
  title: string
  description: string
  action?: { label: string; onClick: () => void }
}) {
  const styles = {
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800'
  }
  const iconStyles = {
    error: 'text-red-400',
    warning: 'text-yellow-400', 
    info: 'text-blue-400'
  }
  const icons = {
    error: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
    warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
    info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  }

  return (
    <div className={`rounded-lg p-6 border ${styles[type]}`}>
      <div className="flex">
        <div className={`flex-shrink-0 ${iconStyles[type]}`}>
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={icons[type]} />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium">{title}</h3>
          <div className="mt-2 text-sm opacity-90">
            <p>{description}</p>
          </div>
          {action && (
            <div className="mt-4">
              <button
                onClick={action.onClick}
                className="text-sm font-medium underline hover:no-underline"
              >
                {action.label}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Pagination({
  page,
  totalPages,
  totalCount,
  pageSize,
  onPageChange,
  onPageSizeChange
}: {
  page: number
  totalPages: number
  totalCount: number
  pageSize: number
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
}) {
  return (
    <div className="flex items-center justify-between bg-white rounded-lg border px-4 py-3">
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-700">
          <span className="font-medium">{(page - 1) * pageSize + 1}</span> to{' '}
          <span className="font-medium">{Math.min(page * pageSize, totalCount)}</span> of{' '}
          <span className="font-medium">{totalCount}</span>
        </span>
        <select
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          className="text-sm border border-gray-300 rounded-md px-2 py-1"
        >
          <option value={10}>10 / page</option>
          <option value={20}>20 / page</option>
          <option value={50}>50 / page</option>
          <option value={100}>100 / page</option>
        </select>
      </div>
      
      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
        >
          Previous
        </button>
        
        <span className="text-sm text-gray-700 px-2">
          Page {page} of {totalPages}
        </span>
        
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
        >
          Next
        </button>
      </div>
    </div>
  )
}

function SearchIcon() {
  return (
    <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  )
}

function LoadingSpinner() {
  return (
    <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
  )
}

function SortIcon() {
  return (
    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
    </svg>
  )
}

function RefreshIcon() {
  return (
    <svg className="h-4 w-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  )
}

export default GenericListPage

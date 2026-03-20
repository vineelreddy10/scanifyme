/**
 * ListToolbar - Search, filter controls, and pagination for list views.
 */

import { useState } from 'react'
import { DocTypeField } from '../../features/meta/useDoctypeMeta'
import { FilterCondition, SortConfig } from '../../features/list/useDoctypeList'

interface FilterChip {
  fieldname: string
  label: string
  value: string
  onRemove: () => void
}

interface BulkActionConfig {
  label: string
  value: string
  variant?: 'default' | 'danger' | 'success'
}

interface ListToolbarProps {
  // Search
  searchQuery: string
  onSearchChange: (query: string) => void
  searchableFields?: DocTypeField[]
  
  // Filters
  filterableFields: DocTypeField[]
  activeFilters: FilterCondition[]
  activeFiltersCount: number
  onShowFilters: () => void
  onRemoveFilter?: (fieldname: string) => void
  onClearFilters?: () => void
  
  // Sort
  sort?: SortConfig
  sortableFields: DocTypeField[]
  onSortChange?: (sort: SortConfig | undefined) => void
  
  // Pagination
  page: number
  pageSize: number
  totalCount: number
  totalPages: number
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
  
  // Bulk actions
  selectedCount: number
  onBulkAction?: (action: string) => void
  onClearSelection?: () => void
  bulkActions?: BulkActionConfig[]
  
  // View options
  showViewToggle?: boolean
  viewMode?: 'list' | 'grid'
  onViewModeChange?: (mode: 'list' | 'grid') => void
  
  // Refresh
  onRefresh: () => void
  isLoading?: boolean
  
  // Filter field labels map for chips
  getFieldLabel?: (fieldname: string) => string
}

export function ListToolbar({
  searchQuery,
  onSearchChange,
  searchableFields = [],
  filterableFields,
  activeFilters = [],
  activeFiltersCount,
  onShowFilters,
  onRemoveFilter,
  onClearFilters,
  sort,
  sortableFields,
  onSortChange,
  page,
  pageSize,
  totalCount,
  totalPages,
  onPageChange,
  onPageSizeChange,
  selectedCount,
  onBulkAction,
  onClearSelection,
  bulkActions = [],
  showViewToggle = false,
  viewMode = 'list',
  onViewModeChange,
  onRefresh,
  isLoading = false,
  getFieldLabel,
}: ListToolbarProps) {
  const [showBulkActions, setShowBulkActions] = useState(false)
  
  // Calculate pagination info
  const startItem = (page - 1) * pageSize + 1
  const endItem = Math.min(page * pageSize, totalCount)
  
  // Build filter chips
  const filterChips: FilterChip[] = activeFilters
    .filter(f => f.fieldname !== '_search')
    .map(f => ({
      fieldname: f.fieldname,
      label: getFieldLabel?.(f.fieldname) || f.fieldname,
      value: String(f.value),
      onRemove: () => onRemoveFilter?.(f.fieldname),
    }))
  
  // Handle search submit
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Search is already applied on change via debounce in parent
  }

  // Handle sort change
  const handleSortChange = (fieldname: string) => {
    if (!onSortChange) return
    
    if (sort?.fieldname === fieldname) {
      // Toggle direction
      onSortChange({
        fieldname,
        direction: sort.direction === 'asc' ? 'desc' : 'asc',
      })
    } else {
      // New sort
      onSortChange({ fieldname, direction: 'asc' })
    }
  }

  return (
    <div className="space-y-4">
      {/* Filter chips */}
      {filterChips.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          {filterChips.map((chip) => (
            <div
              key={chip.fieldname}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 border border-indigo-200 rounded-full text-sm"
            >
              <span className="text-indigo-600 font-medium">{chip.label}:</span>
              <span className="text-indigo-900">{chip.value}</span>
              <button
                onClick={chip.onRemove}
                className="ml-1 text-indigo-400 hover:text-indigo-600 transition-colors"
                title="Remove filter"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
          {filterChips.length > 1 && onClearFilters && (
            <button
              onClick={onClearFilters}
              className="text-sm text-gray-500 hover:text-gray-700 underline"
            >
              Clear all
            </button>
          )}
        </div>
      )}
      
      {/* Sort indicator when sorted */}
      {sort && !filterChips.find(c => c.fieldname === sort.fieldname) && (
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>Sorted by</span>
          <span className="font-medium">{getFieldLabel?.(sort.fieldname) || sort.fieldname}</span>
          <span>{sort.direction === 'asc' ? '↑' : '↓'}</span>
          {onSortChange && (
            <button
              onClick={() => onSortChange(undefined)}
              className="text-gray-400 hover:text-gray-600"
              title="Clear sort"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      )}
      
      {/* Top toolbar: Search, Filters, Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        {/* Left side: Search + Filters */}
        <div className="flex items-center gap-3">
          {/* Search */}
          <form onSubmit={handleSearchSubmit} className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg
                className="h-5 w-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search..."
              className="block w-64 pl-10 pr-3 py-2 border border-gray-300 rounded-lg text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </form>

          {/* Filter button */}
          <button
            onClick={onShowFilters}
            className={`inline-flex items-center px-3 py-2 border rounded-lg text-sm font-medium transition-colors ${
              activeFiltersCount > 0
                ? 'border-indigo-500 bg-indigo-50 text-indigo-700 hover:bg-indigo-100'
                : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            <svg
              className="h-4 w-4 mr-1.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
              />
            </svg>
            Filters
            {activeFiltersCount > 0 && (
              <span className="ml-1.5 inline-flex items-center justify-center w-5 h-5 text-xs font-medium text-white bg-indigo-600 rounded-full">
                {activeFiltersCount}
              </span>
            )}
          </button>

          {/* Sort dropdown */}
          {sortableFields.length > 0 && onSortChange && (
            <div className="relative inline-block">
              <select
                value={sort?.fieldname || ''}
                onChange={(e) => {
                  if (e.target.value) {
                    handleSortChange(e.target.value)
                  }
                }}
                className="block w-48 pl-3 pr-10 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option value="">Sort by...</option>
                {sortableFields.map((field) => (
                  <option key={field.fieldname} value={field.fieldname}>
                    {field.label}
                  </option>
                ))}
              </select>
              {sort && (
                <button
                  onClick={() => onSortChange(undefined)}
                  className="absolute right-8 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  title="Clear sort"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          )}
        </div>

        {/* Right side: Bulk actions, View toggle, Refresh */}
        <div className="flex items-center gap-3">
          {/* Bulk actions bar */}
          {selectedCount > 0 && bulkActions.length > 0 && (
            <div className="flex items-center gap-2 bg-indigo-50 border border-indigo-200 rounded-lg px-3 py-1.5">
              <span className="text-sm font-medium text-indigo-700">
                {selectedCount} selected
              </span>
              <div className="w-px h-4 bg-indigo-300"></div>
              {bulkActions.map((action) => {
                const variant = action.variant || 'default'
                const baseClasses = 'px-2.5 py-1 text-sm font-medium rounded transition-colors'
                const variantClasses = {
                  default: 'text-indigo-600 hover:text-indigo-800 hover:bg-indigo-100',
                  danger: 'text-red-600 hover:text-red-800 hover:bg-red-100',
                  success: 'text-green-600 hover:text-green-800 hover:bg-green-100',
                }
                return (
                  <button
                    key={action.value}
                    onClick={() => onBulkAction?.(action.value)}
                    className={`${baseClasses} ${variantClasses[variant]}`}
                  >
                    {action.label}
                  </button>
                )
              })}
              {onClearSelection && (
                <>
                  <div className="w-px h-4 bg-indigo-300"></div>
                  <button
                    onClick={onClearSelection}
                    className="px-2.5 py-1 text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
                  >
                    Clear
                  </button>
                </>
              )}
            </div>
          )}

          {/* View toggle */}
          {showViewToggle && onViewModeChange && (
            <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden">
              <button
                onClick={() => onViewModeChange('list')}
                className={`p-2 ${
                  viewMode === 'list' ? 'bg-gray-100 text-gray-900' : 'text-gray-400 hover:text-gray-600'
                }`}
                title="List view"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
              </button>
              <button
                onClick={() => onViewModeChange('grid')}
                className={`p-2 ${
                  viewMode === 'grid' ? 'bg-gray-100 text-gray-900' : 'text-gray-400 hover:text-gray-600'
                }`}
                title="Grid view"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
              </button>
            </div>
          )}

          {/* Refresh */}
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50"
            title="Refresh"
          >
            <svg
              className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Pagination and count */}
      <div className="flex items-center justify-between">
        {/* Results count */}
        <div className="text-sm text-gray-600">
          {totalCount === 0 ? (
            'No results'
          ) : (
            <>
              Showing <span className="font-medium">{startItem}</span> to{' '}
              <span className="font-medium">{endItem}</span> of{' '}
              <span className="font-medium">{totalCount.toLocaleString()}</span> results
            </>
          )}
        </div>

        {/* Pagination controls */}
        <div className="flex items-center gap-4">
          {/* Page size selector */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Show</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              className="block w-20 pl-2 pr-8 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          {/* Page navigation */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => onPageChange(1)}
              disabled={page === 1}
              className="p-1.5 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
              title="First page"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
              </svg>
            </button>
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page === 1}
              className="p-1.5 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Previous page"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>

            {/* Page numbers */}
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum: number
                if (totalPages <= 5) {
                  pageNum = i + 1
                } else if (page <= 3) {
                  pageNum = i + 1
                } else if (page >= totalPages - 2) {
                  pageNum = totalPages - 4 + i
                } else {
                  pageNum = page - 2 + i
                }

                return (
                  <button
                    key={pageNum}
                    onClick={() => onPageChange(pageNum)}
                    className={`w-8 h-8 text-sm font-medium rounded ${
                      page === pageNum
                        ? 'bg-indigo-600 text-white'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {pageNum}
                  </button>
                )
              })}
            </div>

            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page === totalPages}
              className="p-1.5 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Next page"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
            <button
              onClick={() => onPageChange(totalPages)}
              disabled={page === totalPages}
              className="p-1.5 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Last page"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

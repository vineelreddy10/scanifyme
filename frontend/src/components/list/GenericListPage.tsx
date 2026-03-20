/**
 * GenericListPage - Server-driven list page for DocTypes.
 * 
 * This component uses the safe_list_api backend which normalizes all values
 * into safe renderable strings, preventing React runtime crashes.
 * 
 * Features:
 * - Server-driven list rendering (no raw metadata interpretation)
 * - Safe value rendering (all values are pre-normalized by backend)
 * - Error boundary for crash protection
 * - Loading/error/empty states
 * - Pagination
 * - Row selection
 * - Permission handling
 */

import { useMemo } from 'react'
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
  /** DocType name (e.g., "Item Category", "QR Batch") */
  doctype: string
  
  /** Route prefix for detail pages (e.g., "/items" for /items/:id) */
  detailRoutePrefix?: string
  
  /** Custom title (defaults to DocType label from schema) */
  title?: string
}

export function GenericListPage({
  doctype,
  detailRoutePrefix,
  title
}: GenericListPageProps) {
  const navigate = useNavigate()
  
  // Use safe list hook (server-driven approach)
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

  // Determine page title
  const pageTitle = title || schema?.title || doctype

  // Handle permission error
  if (isPermissionError) {
    return (
      <AppLayout>
        <PageHeader title={pageTitle} />
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
                  <p>You don't have permission to view {doctype}.</p>
                  <p className="mt-1">Please contact your administrator if you believe this is an error.</p>
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
        <PageHeader title={pageTitle} />
        <Content>
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error Loading {pageTitle}</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
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

  // Handle row click
  const handleRowClick = (row: SafeListRow) => {
    if (detailRoutePrefix) {
      navigate(`${detailRoutePrefix}/${encodeURIComponent(row.name)}`)
    }
  }

  return (
    <AppLayout>
      <PageHeader
        title={pageTitle}
        actions={
          <button
            onClick={refresh}
            className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        }
      />
      <Content>
        <div className="space-y-4">
          {/* Table or Loading/Empty State */}
          {isLoading ? (
            <ListTableSkeleton columns={columns} />
          ) : rows.length === 0 ? (
            <EmptyState title={pageTitle} />
          ) : (
            <SafeListTable
              columns={columns}
              rows={rows}
              onRowClick={detailRoutePrefix ? handleRowClick : undefined}
            />
          )}
          
          {/* Pagination */}
          {!isLoading && rows.length > 0 && (
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

// Safe List Table - renders pre-normalized display values
function SafeListTable({
  columns,
  rows,
  onRowClick
}: {
  columns: SafeListColumn[]
  rows: SafeListRow[]
  onRowClick?: (row: SafeListRow) => void
}) {
  if (columns.length === 0) {
    return (
      <div className="bg-white rounded-lg border p-6 text-center text-gray-500">
        No columns configured for list view.
      </div>
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
                  {col.label}
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
                        displayValue
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

// Loading skeleton
function ListTableSkeleton({ columns }: { columns: SafeListColumn[] }) {
  return (
    <div className="bg-white rounded-lg border overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col) => (
              <th
                key={col.fieldname}
                className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${getColumnWidth(col.fieldtype)}`}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
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

// Empty state
function EmptyState({ title }: { title: string }) {
  return (
    <div className="bg-white rounded-lg border p-12 text-center">
      <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
      </svg>
      <h3 className="mt-2 text-sm font-medium text-gray-900">No {title}</h3>
      <p className="mt-1 text-sm text-gray-500">Get started by creating a new record.</p>
    </div>
  )
}

// Pagination
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
          Showing <span className="font-medium">{(page - 1) * pageSize + 1}</span> to{' '}
          <span className="font-medium">{Math.min(page * pageSize, totalCount)}</span> of{' '}
          <span className="font-medium">{totalCount}</span> results
        </span>
        <select
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          className="text-sm border-gray-300 rounded-md"
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
          className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
        >
          Previous
        </button>
        
        <span className="text-sm text-gray-700">
          Page {page} of {totalPages}
        </span>
        
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
        >
          Next
        </button>
      </div>
    </div>
  )
}

export default GenericListPage

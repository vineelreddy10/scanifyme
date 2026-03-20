/**
 * ListTable - Renders a data table with columns derived from DocType metadata.
 */

import { useState, useRef, useEffect } from 'react'
import { DocTypeField, formatFieldValue } from '../../features/meta/useDoctypeMeta'
import { SortConfig } from '../../features/list/useDoctypeList'

interface RowAction {
  label: string
  icon?: React.ReactNode
  onClick: (row: Record<string, unknown>, name: string) => void
  variant?: 'default' | 'danger'
}

interface ListTableProps {
  columns: DocTypeField[]
  data: Record<string, unknown>[]
  isLoading: boolean
  sort?: SortConfig
  onSort?: (fieldname: string, direction?: 'asc' | 'desc') => void
  onRowClick?: (row: Record<string, unknown>, name: string) => void
  selectedRows?: Set<string>
  onSelectRow?: (name: string, selected: boolean) => void
  onSelectAll?: (selected: boolean) => void
  rowActions?: RowAction[]
}

export function ListTable({
  columns,
  data,
  isLoading,
  sort,
  onSort,
  onRowClick,
  selectedRows = new Set(),
  onSelectRow,
  onSelectAll,
  rowActions,
}: ListTableProps) {
  const [openMenuForRow, setOpenMenuForRow] = useState<string | null>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  
  // Check if any rows are selected
  const allSelected = data.length > 0 && data.every(row => selectedRows.has(String(row.name)))
  const someSelected = data.some(row => selectedRows.has(String(row.name)))
  
  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpenMenuForRow(null)
      }
    }
    
    if (openMenuForRow) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [openMenuForRow])
  
  // Close menu on escape
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setOpenMenuForRow(null)
      }
    }
    
    if (openMenuForRow) {
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
  }, [openMenuForRow])

  const handleSort = (fieldname: string) => {
    onSort?.(fieldname)
  }

  const handleRowClick = (row: Record<string, unknown>) => {
    const name = String(row.name || row.Name || '')
    if (name) {
      onRowClick?.(row, name)
    }
  }

  const handleSelectRow = (name: string, checked: boolean) => {
    onSelectRow?.(name, checked)
  }

  const handleSelectAll = (checked: boolean) => {
    onSelectAll?.(checked)
  }
  
  const handleRowAction = (row: Record<string, unknown>, name: string, action: RowAction) => {
    setOpenMenuForRow(null)
    action.onClick(row, name)
  }
  
  const toggleMenu = (name: string) => {
    setOpenMenuForRow(prev => prev === name ? null : name)
  }

  // Get sort indicator
  const getSortIndicator = (fieldname: string) => {
    if (!sort || sort.fieldname !== fieldname) {
      return (
        <span className="ml-1 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
          ↕
        </span>
      )
    }
    return (
      <span className="ml-1 text-indigo-600">
        {sort.direction === 'asc' ? '↑' : '↓'}
      </span>
    )
  }

  // Format cell value
  const formatCellValue = (value: unknown, field: DocTypeField) => {
    return formatFieldValue(value, field)
  }

  // Get column width class based on fieldtype
  const getColumnWidth = (field: DocTypeField) => {
    switch (field.fieldtype) {
      case 'Int':
      case 'Float':
      case 'Currency':
        return 'w-24'
      case 'Check':
        return 'w-16'
      case 'Datetime':
      case 'Date':
        return 'w-40'
      default:
        return ''
    }
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.fieldname}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
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

  if (data.length === 0) {
    return null // Empty state handled by parent
  }

  const hasActions = rowActions && rowActions.length > 0
  
  return (
    <div className="bg-white rounded-lg border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {/* Checkbox column */}
              {(onSelectRow || onSelectAll) && (
                <th className="w-12 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    ref={(el) => {
                      if (el) el.indeterminate = someSelected && !allSelected
                    }}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="h-4 w-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                  />
                </th>
              )}
              {columns.map((col) => (
                <th
                  key={col.fieldname}
                  className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${getColumnWidth(col)} ${
                    col.in_list_view ? 'group cursor-pointer hover:bg-gray-100' : ''
                  }`}
                  onClick={col.in_list_view ? () => handleSort(col.fieldname) : undefined}
                >
                  <span className="flex items-center">
                    {col.label}
                    {col.in_list_view ? getSortIndicator(col.fieldname) : null}
                  </span>
                </th>
              ))}
              {hasActions && (
                <th className="w-12 px-4 py-3"></th>
              )}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((row, rowIndex) => {
              const name = String(row.name || row.Name || '')
              const isSelected = selectedRows.has(name)

              return (
                <tr
                  key={name || rowIndex}
                  className={`hover:bg-gray-50 transition-colors ${
                    isSelected ? 'bg-indigo-50' : ''
                  } ${onRowClick ? 'cursor-pointer' : ''}`}
                  onClick={() => handleRowClick(row)}
                >
                  {/* Checkbox cell */}
                  {(onSelectRow || onSelectAll) && (
                    <td
                      className="w-12 px-4 py-4"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => handleSelectRow(name, e.target.checked)}
                        className="h-4 w-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                      />
                    </td>
                  )}
                  {columns.map((col) => {
                    const value = row[col.fieldname]
                    const formattedValue = formatCellValue(value, col)

                    return (
                      <td
                        key={col.fieldname}
                        className={`px-6 py-4 whitespace-nowrap text-sm ${
                          col.fieldtype === 'Check'
                            ? ''
                            : 'text-gray-900'
                        }`}
                      >
                        {/* Special rendering for certain fieldtypes */}
                        {col.fieldtype === 'Check' ? (
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              value
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-500'
                            }`}
                          >
                            {value ? 'Yes' : 'No'}
                          </span>
                        ) : col.fieldtype === 'Link' ? (
                          <span className="text-indigo-600 hover:text-indigo-900">
                            {formattedValue}
                          </span>
                        ) : (
                          <span
                            className={
                              value === null || value === undefined
                                ? 'text-gray-400'
                                : ''
                            }
                          >
                            {formattedValue}
                          </span>
                        )}
                      </td>
                    )
                  })}
                  {/* Actions cell */}
                  {hasActions && (
                    <td
                      className="w-12 px-4 py-4"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <div className="relative" ref={openMenuForRow === name ? menuRef : undefined}>
                        <button
                          onClick={() => toggleMenu(name)}
                          className="p-1 text-gray-400 hover:text-gray-600 rounded hover:bg-gray-100"
                          title="Actions"
                        >
                          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
                          </svg>
                        </button>
                        {openMenuForRow === name && (
                          <div className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg border z-10">
                            {rowActions!.map((action, idx) => (
                              <button
                                key={idx}
                                onClick={() => handleRowAction(row, name, action)}
                                className={`w-full text-left px-4 py-2 text-sm flex items-center gap-2 ${
                                  action.variant === 'danger'
                                    ? 'text-red-600 hover:bg-red-50'
                                    : 'text-gray-700 hover:bg-gray-50'
                                }`}
                              >
                                {action.icon && (
                                  <span className="w-4 h-4">{action.icon}</span>
                                )}
                                {action.label}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

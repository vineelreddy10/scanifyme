/**
 * ListFilters - Filter panel for list views.
 */

import { useState } from 'react'
import { DocTypeField } from '../../features/meta/useDoctypeMeta'
import { FilterCondition, FilterOperator, buildFilter } from '../../features/list/useDoctypeList'

interface ListFiltersProps {
  fields: DocTypeField[]
  activeFilters: FilterCondition[]
  onApplyFilters: (filters: FilterCondition[]) => void
  onClearFilters: () => void
  onClose: () => void
}

export function ListFilters({
  fields,
  activeFilters,
  onApplyFilters,
  onClearFilters,
  onClose,
}: ListFiltersProps) {
  // Get filterable fields (fields with in_standard_filter)
  const filterableFields = fields.filter(f => f.in_standard_filter)
  
  // Local state for filters being edited
  const [localFilters, setLocalFilters] = useState<FilterCondition[]>(
    activeFilters.filter(f => f.fieldname !== '_search')
  )
  const [newFilter, setNewFilter] = useState<{
    fieldname: string
    operator: FilterOperator
    value: string
  } | null>(null)

  // Get operators based on field type
  const getOperators = (fieldtype: string): FilterOperator[] => {
    switch (fieldtype) {
      case 'Select':
        return ['=', '!=']
      case 'Check':
        return ['=']
      case 'Int':
      case 'Float':
      case 'Currency':
        return ['=', '!=', '>', '<', '>=', '<=']
      case 'Datetime':
      case 'Date':
        return ['=', '!=', '>', '<', 'between']
      default:
        return ['=', '!=', 'like']
    }
  }

  // Add a new filter
  const handleAddFilter = () => {
    if (!newFilter) return
    
    const filter = buildFilter(
      newFilter.fieldname,
      newFilter.operator,
      newFilter.operator === 'like' ? `%${newFilter.value}%` : newFilter.value
    )
    
    setLocalFilters(prev => [...prev, filter])
    setNewFilter(null)
  }

  // Remove a filter
  const handleRemoveFilter = (fieldname: string) => {
    setLocalFilters(prev => prev.filter(f => f.fieldname !== fieldname))
  }

  // Apply filters
  const handleApply = () => {
    onApplyFilters(localFilters)
    onClose()
  }

  // Clear all filters
  const handleClear = () => {
    setLocalFilters([])
    onClearFilters()
  }

  // Get field by name
  const getField = (fieldname: string) => {
    return fields.find(f => f.fieldname === fieldname)
  }

  // Get filterable fields not already in use
  const availableFields = filterableFields.filter(
    f => !localFilters.some(lf => lf.fieldname === f.fieldname)
  )

  return (
    <div className="bg-white rounded-lg border shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <h3 className="text-sm font-medium text-gray-900">Filters</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Active filters */}
      {localFilters.length > 0 && (
        <div className="px-4 py-3 border-b">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-700 uppercase tracking-wider">
              Active Filters
            </span>
            <button
              onClick={handleClear}
              className="text-xs text-indigo-600 hover:text-indigo-800"
            >
              Clear all
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {localFilters.map((filter) => {
              const field = getField(filter.fieldname)
              return (
                <div
                  key={filter.fieldname}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-indigo-50 text-indigo-700 rounded text-sm"
                >
                  <span className="font-medium">{field?.label || filter.fieldname}:</span>
                  <span>{filter.operator}</span>
                  <span>{String(filter.value).replace(/%/g, '')}</span>
                  <button
                    onClick={() => handleRemoveFilter(filter.fieldname)}
                    className="ml-1 text-indigo-400 hover:text-indigo-600"
                  >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Add new filter */}
      {availableFields.length > 0 && (
        <div className="px-4 py-3 border-b">
          <div className="text-xs font-medium text-gray-700 uppercase tracking-wider mb-2">
            Add Filter
          </div>
          
          {newFilter ? (
            <div className="space-y-2">
              {/* Selected field info */}
              <div className="flex items-center gap-2 text-sm">
                <span className="font-medium text-gray-700">
                  {getField(newFilter.fieldname)?.label}:
                </span>
              </div>
              
              {/* Operator select */}
              <select
                value={newFilter.operator}
                onChange={(e) => setNewFilter({ ...newFilter, operator: e.target.value as FilterOperator })}
                className="block w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {getOperators(getField(newFilter.fieldname)?.fieldtype || 'Data').map((op) => {
                  const labels: Record<string, string> = {
                    '=': 'equals',
                    '!=': 'not equals',
                    '>': 'greater than',
                    '<': 'less than',
                    '>=': 'greater or equal',
                    '<=': 'less or equal',
                    'like': 'contains',
                    'between': 'between',
                    'is': 'is',
                    'in': 'in',
                    'not in': 'not in',
                  }
                  return (
                    <option key={op} value={op}>
                      {labels[op] || op}
                    </option>
                  )
                })}
              </select>
              
              {/* Value input */}
              {newFilter.operator === 'between' ? (
                <div className="flex gap-2">
                  <input
                    type="date"
                    value={(newFilter.value as string[])?.[0] || ''}
                    onChange={(e) => setNewFilter({ 
                      ...newFilter, 
                      value: [e.target.value, (newFilter.value as string[])?.[1] || '']
                    })}
                    className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="From"
                  />
                  <input
                    type="date"
                    value={(newFilter.value as string[])?.at(1) || ''}
                    onChange={(e) => setNewFilter({ 
                      ...newFilter, 
                      value: [(newFilter.value as string[])?.[0] || '', e.target.value]
                    })}
                    className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="To"
                  />
                </div>
              ) : getField(newFilter.fieldname)?.fieldtype === 'Select' ? (
                <select
                  value={newFilter.value}
                  onChange={(e) => setNewFilter({ ...newFilter, value: e.target.value })}
                  className="block w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select...</option>
                  {getField(newFilter.fieldname)?.options_list?.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              ) : getField(newFilter.fieldname)?.fieldtype === 'Check' ? (
                <select
                  value={newFilter.value}
                  onChange={(e) => setNewFilter({ ...newFilter, value: e.target.value })}
                  className="block w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="1">Yes</option>
                  <option value="0">No</option>
                </select>
              ) : (
                <input
                  type={getField(newFilter.fieldname)?.fieldtype === 'Date' ? 'date' : 'text'}
                  value={newFilter.value}
                  onChange={(e) => setNewFilter({ ...newFilter, value: e.target.value })}
                  className="block w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Value..."
                />
              )}
              
              {/* Add/Cancel buttons */}
              <div className="flex gap-2">
                <button
                  onClick={handleAddFilter}
                  disabled={!newFilter.value}
                  className="flex-1 px-3 py-1.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  Add
                </button>
                <button
                  onClick={() => setNewFilter(null)}
                  className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <select
              value=""
              onChange={(e) => {
                const field = getField(e.target.value)
                if (field) {
                  setNewFilter({
                    fieldname: field.fieldname,
                    operator: getOperators(field.fieldtype)[0],
                    value: '',
                  })
                }
              }}
              className="block w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Select a field...</option>
              {availableFields.map((field) => (
                <option key={field.fieldname} value={field.fieldname}>
                  {field.label}
                </option>
              ))}
            </select>
          )}
        </div>
      )}

      {/* Footer with Apply/Cancel buttons */}
      <div className="px-4 py-3 bg-gray-50 rounded-b-lg flex justify-end gap-2">
        <button
          onClick={onClose}
          className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
        >
          Cancel
        </button>
        <button
          onClick={handleApply}
          className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
        >
          Apply Filters
        </button>
      </div>
    </div>
  )
}

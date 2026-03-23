/**
 * Safe Value Rendering Utilities
 * 
 * These utilities ensure that dynamic values from the backend
 * are rendered safely in React without causing runtime crashes.
 */

/**
 * Check if a value is a renderable primitive.
 * A renderable primitive is a string, number, boolean, or null/undefined.
 */
export function isRenderablePrimitive(value: unknown): boolean {
  if (value === null || value === undefined) return true
  if (typeof value === 'string') return true
  if (typeof value === 'number') return true
  if (typeof value === 'boolean') return true
  return false
}

/**
 * Render a primitive value safely as a string.
 * Returns "-" for null/undefined.
 */
export function renderPrimitive(value: unknown): string {
  if (value === null || value === undefined) {
    return '-'
  }
  
  if (typeof value === 'string') {
    return value || '-'
  }
  
  if (typeof value === 'number') {
    if (isNaN(value)) return '-'
    return String(value)
  }
  
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }
  
  // For any other type (objects, arrays, functions, etc.), return fallback
  return '-'
}

/**
 * Get column width class based on fieldtype.
 */
export function getColumnWidth(fieldtype: string): string {
  switch (fieldtype) {
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

/**
 * Get CSS class for boolean/badge display.
 */
export function getBooleanClass(value: unknown): string {
  return value
    ? 'bg-green-100 text-green-800'
    : 'bg-gray-100 text-gray-500'
}

/**
 * Get CSS class for link fields.
 */
export function getLinkClass(): string {
  return 'text-indigo-600 hover:text-indigo-900'
}

/**
 * Get CSS class for null/empty values.
 */
export function getEmptyClass(value: unknown): string {
  return value === null || value === undefined || value === ''
    ? 'text-gray-400'
    : ''
}

export function isImageField(fieldtype: string): boolean {
  return fieldtype === 'Attach Image' || fieldtype === 'Attach'
}

export function getImageUrl(filePath: string | null | undefined): string | null {
  if (!filePath || filePath === '-') return null
  if (filePath.startsWith('http://') || filePath.startsWith('https://')) return filePath
  if (typeof window !== 'undefined') {
    return window.location.origin + filePath
  }
  return filePath
}

/**
 * Truncate a string to a maximum length.
 */
export function truncate(str: string, maxLength: number = 50): string {
  if (str.length <= maxLength) return str
  return str.slice(0, maxLength - 3) + '...'
}

/**
 * Format a value for display in a list cell.
 * This is a fallback for when backend normalization is not available.
 */
export function formatListValue(value: unknown, fieldtype: string): string {
  if (value === null || value === undefined) {
    return '-'
  }
  
  // For display_values from backend, just return as-is
  if (typeof value === 'string') {
    return value || '-'
  }
  
  // Boolean
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }
  
  // Number
  if (typeof value === 'number') {
    if (isNaN(value)) return '-'
    return value.toLocaleString()
  }
  
  // For any other type, render as string or fallback
  if (typeof value === 'object') {
    return '-'
  }
  
  return String(value) || '-'
}

/**
 * Type definitions for safe list schema
 */
export interface SafeListColumn {
  fieldname: string
  label: string
  fieldtype: string
  in_list_view: number
  width: string | null
}

export interface SafeListSchema {
  doctype: string
  title: string
  columns: SafeListColumn[]
  permissions: {
    can_read: boolean
    can_write: boolean
    can_create: boolean
    can_delete: boolean
  }
  sort_field: string
  sort_order: string
}

export interface SafeListRow {
  name: string
  values: Record<string, unknown>
  display_values: Record<string, string>
}

export interface SafeListResponse {
  rows: SafeListRow[]
  total_count: number
  page: number
  page_length: number
}

/**
 * Type definitions for safe detail schema
 */
export interface SafeDetailField {
  fieldname: string
  label: string
  fieldtype: string
  options: string | null
  options_list?: string[]
  read_only: boolean
  reqd: boolean
}

export interface SafeDetailSchema {
  doctype: string
  title: string
  fields: SafeDetailField[]
  permissions: {
    can_read: boolean
    can_write: boolean
    can_create: boolean
    can_delete: boolean
  }
}

export interface SafeDetailDoc {
  doctype: string
  name: string
  values: Record<string, unknown>
  display_values: Record<string, string>
  permissions: {
    can_read: boolean
    can_write: boolean
  }
}

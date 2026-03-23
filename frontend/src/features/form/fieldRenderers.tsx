/**
 * fieldRenderers.tsx - Specific field type renderers for generic forms.
 * 
 * Provides input components for different Frappe field types.
 */

import React from 'react'

// Common input props
interface BaseFieldProps {
  value: unknown
  onChange: (value: unknown) => void
  disabled?: boolean
  error?: string | null
  placeholder?: string
}

// Text Input (Data, URL, Email, Phone)
export const TextField: React.FC<BaseFieldProps & { maxLength?: number }> = ({
  value,
  onChange,
  disabled,
  error,
  placeholder,
  maxLength,
}) => (
  <input
    type="text"
    value={value as string || ''}
    onChange={(e) => onChange(e.target.value)}
    disabled={disabled}
    placeholder={placeholder}
    maxLength={maxLength}
    className={`block w-full rounded-md shadow-sm sm:text-sm ${
      error
        ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
        : 'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500'
    } ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
  />
)

// Text Area (Text, Small Text, Long Text)
export const TextAreaField: React.FC<BaseFieldProps & { rows?: number }> = ({
  value,
  onChange,
  disabled,
  error,
  placeholder,
  rows = 3,
}) => (
  <textarea
    value={value as string || ''}
    onChange={(e) => onChange(e.target.value)}
    disabled={disabled}
    placeholder={placeholder}
    rows={rows}
    className={`block w-full rounded-md shadow-sm sm:text-sm ${
      error
        ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
        : 'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500'
    } ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
  />
)

// Number Input (Int, Float, Currency)
export const NumberField: React.FC<BaseFieldProps & { min?: number; max?: number; step?: string }> = ({
  value,
  onChange,
  disabled,
  error,
  placeholder,
  min,
  max,
  step,
}) => (
  <input
    type="number"
    value={value as number | string || ''}
    onChange={(e) => {
      const val = e.target.value
      onChange(val === '' ? '' : Number(val))
    }}
    disabled={disabled}
    placeholder={placeholder}
    min={min}
    max={max}
    step={step || 'any'}
    className={`block w-full rounded-md shadow-sm sm:text-sm ${
      error
        ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
        : 'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500'
    } ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
  />
)

// Select Dropdown
export const SelectField: React.FC<BaseFieldProps & { options?: string[] }> = ({
  value,
  onChange,
  disabled,
  error,
  options = [],
}) => (
  <select
    value={value as string || ''}
    onChange={(e) => onChange(e.target.value)}
    disabled={disabled}
    className={`block w-full rounded-md shadow-sm sm:text-sm ${
      error
        ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
        : 'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500'
    } ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
  >
    <option value="">Select...</option>
    {options.map((opt) => (
      <option key={opt} value={opt}>
        {opt}
      </option>
    ))}
  </select>
)

// Checkbox (Check)
export const CheckboxField: React.FC<BaseFieldProps> = ({
  value,
  onChange,
  disabled,
}) => (
  <input
    type="checkbox"
    checked={Boolean(value)}
    onChange={(e) => onChange(e.target.checked ? 1 : 0)}
    disabled={disabled}
    className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
  />
)

// Date Input
export const DateField: React.FC<BaseFieldProps> = ({
  value,
  onChange,
  disabled,
  error,
}) => (
  <input
    type="date"
    value={value as string || ''}
    onChange={(e) => onChange(e.target.value)}
    disabled={disabled}
    className={`block w-full rounded-md shadow-sm sm:text-sm ${
      error
        ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
        : 'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500'
    } ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
  />
)

// DateTime Input
export const DateTimeField: React.FC<BaseFieldProps> = ({
  value,
  onChange,
  disabled,
  error,
}) => (
  <input
    type="datetime-local"
    value={value as string || ''}
    onChange={(e) => onChange(e.target.value)}
    disabled={disabled}
    className={`block w-full rounded-md shadow-sm sm:text-sm ${
      error
        ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
        : 'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500'
    } ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
  />
)

// Link Field (DocType reference) - Read-only display with lookup
export const LinkField: React.FC<BaseFieldProps & { doctype?: string; doctypeField?: string }> = ({
  value,
  disabled,
  error,
}) => (
  <input
    type="text"
    value={value as string || ''}
    readOnly
    disabled
    className={`block w-full rounded-md shadow-sm sm:text-sm bg-gray-100 ${
      error ? 'border-red-300' : 'border-gray-300'
    } cursor-not-allowed`}
  />
)

// Read-only display for unsupported types
export const ReadOnlyField: React.FC<{ value: unknown }> = ({ value }) => (
  <div className="block w-full rounded-md bg-gray-50 px-3 py-2 text-sm text-gray-600 sm:text-sm">
    {value === null || value === undefined || value === ''
      ? '-'
      : String(value)}
  </div>
)

// Field type to renderer mapping
export const fieldRenderers = {
  'Data': TextField,
  'URL': TextField,
  'Email': TextField,
  'Phone': TextField,
  'Text': TextAreaField,
  'Small Text': TextAreaField,
  'Long Text': TextAreaField,
  'Text Editor': TextAreaField,
  'HTML': TextAreaField,
  'Code': TextAreaField,
  'Int': NumberField,
  'Float': NumberField,
  'Currency': NumberField,
  'Percent': NumberField,
  'Select': SelectField,
  'Check': CheckboxField,
  'Date': DateField,
  'Datetime': DateTimeField,
  'Time': TextField,
  'Link': LinkField,
  'Dynamic Link': LinkField,
}

// Get renderer for field type
export function getFieldRenderer(fieldtype: string) {
  return fieldRenderers[fieldtype as keyof typeof fieldRenderers] || ReadOnlyField
}

// Format value for display (read-only mode)
export function formatValueForDisplay(value: unknown, fieldtype: string): string {
  if (value === null || value === undefined || value === '') {
    return '-'
  }

  switch (fieldtype) {
    case 'Check':
      return value ? 'Yes' : 'No'
    case 'Date':
    case 'Datetime':
      if (typeof value === 'string') {
        const date = new Date(value)
        if (isNaN(date.getTime())) return String(value)
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          ...(fieldtype === 'Datetime' && {
            hour: '2-digit',
            minute: '2-digit',
          }),
        })
      }
      return String(value)
    case 'Int':
    case 'Float':
    case 'Currency':
    case 'Percent':
      if (typeof value === 'number') {
        return value.toLocaleString()
      }
      return String(value)
    case 'Link':
      // Extract name from "Doctype Name" format
      return String(value).split(' ').pop() || String(value)
    case 'Password':
      return '••••••••'
    default:
      return String(value)
  }
}

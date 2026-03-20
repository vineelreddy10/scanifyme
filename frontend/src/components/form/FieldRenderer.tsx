/**
 * FieldRenderer - Renders a single DocType field based on fieldtype.
 */

import React from 'react'
import { getFieldRenderer, formatValueForDisplay } from '../../features/form/fieldRenderers'
import { DocField } from '../../features/form/useDoctypeForm'

interface FieldRendererProps {
  field: DocField
  value: unknown
  onChange?: (value: unknown) => void
  editable?: boolean
  error?: string | null
}

export const FieldRenderer: React.FC<FieldRendererProps> = ({
  field,
  value,
  onChange,
  editable = false,
  error,
}) => {
  const Renderer = getFieldRenderer(field.fieldtype)
  const isEditable = editable && !field.read_only && onChange !== undefined

  // Special handling for Check field (always editable unless read_only)
  if (field.fieldtype === 'Check') {
    return (
      <div className="flex items-center">
        <Renderer
          value={value}
          onChange={isEditable ? onChange! : () => {}}
          disabled={!isEditable}
          error={error}
        />
      </div>
    )
  }

  // Read-only mode
  if (!isEditable) {
    return (
      <div>
        <div className="text-sm text-gray-900">
          {formatValueForDisplay(value, field.fieldtype)}
        </div>
        {error && (
          <p className="mt-1 text-sm text-red-600">{error}</p>
        )}
      </div>
    )
  }

  // Editable mode - render appropriate input
  return (
    <div>
      <Renderer
        value={value}
        onChange={onChange!}
        disabled={false}
        error={error}
        options={field.options_list}
      />
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
      {field.description && (
        <p className="mt-1 text-xs text-gray-500">{field.description}</p>
      )}
    </div>
  )
}

// Field label with required indicator
export const FieldLabel: React.FC<{
  field: DocField
  editable?: boolean
}> = ({ field, editable }) => (
  <label className="block text-sm font-medium text-gray-700">
    {field.label}
    {field.reqd && editable && (
      <span className="text-red-500 ml-1">*</span>
    )}
    {!editable && field.reqd && (
      <span className="text-red-500 ml-1">*</span>
    )}
  </label>
)

// Field wrapper with label and description
interface FieldWrapperProps {
  field: DocField
  children: React.ReactNode
  editable?: boolean
}

export const FieldWrapper: React.FC<FieldWrapperProps> = ({
  field,
  children,
  editable = false,
}) => {
  return (
    <div className="sm:col-span-6">
      <FieldLabel field={field} editable={editable} />
      <div className="mt-1">
        {children}
      </div>
      {!editable && field.description && (
        <p className="mt-1 text-xs text-gray-500">{field.description}</p>
      )}
    </div>
  )
}

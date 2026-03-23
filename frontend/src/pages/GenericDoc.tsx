/**
 * GenericDoc - Page wrapper for the generic document detail page.
 * 
 * This component wraps GenericDocPage for routing purposes.
 * It reads doctype and name from URL params.
 */

import { useParams, useNavigate } from 'react-router-dom'
import { GenericDocPage } from '../components/form/GenericDocPage'

export default function GenericDoc() {
  const { doctype, name } = useParams<{ doctype: string; name: string }>()
  const navigate = useNavigate()
  
  if (!doctype) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">DocType Not Specified</h1>
          <p className="mt-2 text-gray-600">
            Please specify a DocType in the URL.
          </p>
        </div>
      </div>
    )
  }
  
  // Decode the doctype from URL
  const decodedDoctype = decodeURIComponent(doctype)
  const decodedName = name ? decodeURIComponent(name) : undefined
  
  // Handle back navigation
  const handleBack = () => {
    // Go back to list page for this doctype
    navigate(`/list/${encodeURIComponent(decodedDoctype)}`)
  }
  
  // Map doctypes to custom titles or exclusions
  const getDocTypeConfig = (dt: string) => {
    const configs: Record<string, { title?: string; excludeFields?: string[] }> = {
      'Item Category': {
        excludeFields: ['name'], // Exclude auto-generated name field
      },
      'QR Batch': {
        excludeFields: ['name', 'naming_series'], // Exclude auto-generated fields
      },
      'QR Code Tag': {
        excludeFields: ['name'], // Only exclude name, show all QR fields
      },
      'Recovery Case': {
        excludeFields: ['name'], // Exclude name field
      },
      'Registered Item': {
        excludeFields: ['name'], // Exclude name field
      },
    }
    return configs[dt] || {}
  }
  
  const config = getDocTypeConfig(decodedDoctype)
  
  return (
    <GenericDocPage
      doctype={decodedDoctype}
      name={decodedName}
      title={config.title}
      excludeFields={config.excludeFields}
      onBack={handleBack}
    />
  )
}

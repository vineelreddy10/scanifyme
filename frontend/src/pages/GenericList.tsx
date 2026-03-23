/**
 * GenericList - Page wrapper for the generic list page.
 * 
 * This component wraps GenericListPage for routing purposes.
 * It reads the doctype from URL params and passes it to GenericListPage.
 * 
 * Uses server-driven approach for safe rendering.
 */

import { useParams, useSearchParams } from 'react-router-dom'
import { GenericListPage } from '../components/list/GenericListPage'

export default function GenericList() {
  const { doctype } = useParams<{ doctype: string }>()
  const [searchParams] = useSearchParams()
  
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
  
  const decodedDoctype = decodeURIComponent(doctype)
  
  const getDetailRoute = (dt: string): string | undefined => {
    const routes: Record<string, string | undefined> = {
      'Item Category': undefined,
      'QR Batch': '/qr-batches',
      'QR Code Tag': '/m/QR Code Tag',
      'Recovery Case': '/recovery',
      'Registered Item': '/items',
      'Notification Event Log': undefined,
      'Owner Profile': '/m/Owner Profile',
      'Scan Event': undefined,
      'Finder Session': undefined,
      'Ownership Transfer': undefined,
    }
    return routes[dt]
  }
  
  const filters: Record<string, string> = {}
  searchParams.forEach((value, key) => {
    filters[key] = value
  })
  
  return (
    <GenericListPage
      doctype={decodedDoctype}
      detailRoutePrefix={getDetailRoute(decodedDoctype)}
      filters={Object.keys(filters).length > 0 ? filters : undefined}
    />
  )
}

/**
 * GenericList - Page wrapper for the generic list page.
 * 
 * This component wraps GenericListPage for routing purposes.
 * It reads the doctype from URL params and passes it to GenericListPage.
 * 
 * Uses server-driven approach for safe rendering.
 */

import { useParams } from 'react-router-dom'
import { GenericListPage } from '../components/list/GenericListPage'

export default function GenericList() {
  const { doctype } = useParams<{ doctype: string }>()
  
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
  
  // Decode the doctype from URL (handles %20 spaces)
  const decodedDoctype = decodeURIComponent(doctype)
  
  // Map doctype names to detail routes
  // Some doctypes have custom pages, others use generic detail
  const getDetailRoute = (dt: string): string | undefined => {
    const routes: Record<string, string | undefined> = {
      'Item Category': undefined, // No detail page needed
      'QR Batch': undefined, // No detail page needed
      'QR Code Tag': '/m/QR Code Tag', // Generic detail
      'Recovery Case': '/recovery',
      'Registered Item': '/items',
      'Notification Event Log': undefined, // No detail page
      'Owner Profile': '/m/Owner Profile', // Generic detail
      'Scan Event': undefined, // No detail page
      'Finder Session': undefined, // No detail page
      'Ownership Transfer': undefined, // No detail page
    }
    return routes[dt]
  }
  
  return (
    <GenericListPage
      doctype={decodedDoctype}
      detailRoutePrefix={getDetailRoute(decodedDoctype)}
    />
  )
}

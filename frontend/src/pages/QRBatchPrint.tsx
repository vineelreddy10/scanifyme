import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AppLayout, PageHeader, Content, Card, ErrorBanner } from '../components/ui'

interface QRCodeTag {
  name: string
  qr_uid: string
  qr_token: string
  qr_url: string
  qr_image: string | null
  status: string
}

function getCSRFToken(): string {
  return typeof window !== 'undefined' ? (window as Window & { csrf_token?: string }).csrf_token || '' : ''
}

async function fetchBatchTags(batchName: string): Promise<QRCodeTag[]> {
  const url = '/api/method/scanifyme.qr_management.api.qr_api.get_qr_tags'
  const csrfToken = getCSRFToken()
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  }
  
  if (csrfToken) {
    headers['X-Frappe-CSRF-Token'] = csrfToken
  }
  
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ batch: batchName, limit: 1000 }),
    credentials: 'include'
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to fetch tags' }))
    throw new Error(error.message || 'Failed to fetch tags')
  }

  const data = await response.json()
  return data.message.rows || []
}

function getImageUrl(filePath: string | null): string | null {
  if (!filePath) return null
  if (filePath.startsWith('http://') || filePath.startsWith('https://')) return filePath
  if (typeof window !== 'undefined') {
    return window.location.origin + filePath
  }
  return filePath
}

export default function QRBatchPrint() {
  const { name } = useParams<{ name: string }>()
  const navigate = useNavigate()
  const [tags, setTags] = useState<QRCodeTag[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadTags = useCallback(async () => {
    if (!name) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await fetchBatchTags(name)
      setTags(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load tags'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [name])

  useEffect(() => {
    loadTags()
  }, [loadTags])

  if (isLoading) {
    return (
      <AppLayout>
        <PageHeader title="Print Batch" />
        <Content>
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        </Content>
      </AppLayout>
    )
  }

  if (error) {
    return (
      <AppLayout>
        <PageHeader title="Print Batch" />
        <Content>
          <ErrorBanner message={error} onRetry={loadTags} />
        </Content>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <PageHeader
        title="Print Batch"
        description={`${name} • ${tags.length} QR codes`}
        actions={
          <div className="flex items-center gap-3">
            <button
              onClick={() => window.print()}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
            >
              <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              Print
            </button>
            <button
              onClick={() => navigate(-1)}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Back
            </button>
          </div>
        }
      />
      <Content>
        <div className="print:block">
          <div className="hidden print:block text-center mb-4">
            <h1 className="text-xl font-bold">ScanifyMe QR Labels</h1>
            <p className="text-sm text-gray-600">Batch: {name} | Total: {tags.length}</p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {tags.map((tag) => (
              <div 
                key={tag.name} 
                className="border border-gray-200 rounded-lg p-4 text-center print:border-gray-400"
              >
                {getImageUrl(tag.qr_image) ? (
                  <img 
                    src={getImageUrl(tag.qr_image) || ''} 
                    alt={tag.qr_uid}
                    className="w-24 h-24 mx-auto object-contain"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(tag.qr_url)}`
                    }}
                  />
                ) : (
                  <div className="w-24 h-24 mx-auto bg-gray-100 rounded flex items-center justify-center">
                    <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                    </svg>
                  </div>
                )}
                <div className="mt-2 font-bold text-sm">{tag.qr_uid}</div>
                <div className="text-xs text-gray-500 truncate">{tag.qr_url}</div>
              </div>
            ))}
          </div>
          {tags.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No QR codes in this batch
            </div>
          )}
        </div>
      </Content>
      <style>{`
        @media print {
          body * {
            visibility: hidden;
          }
          .print\\:block, .print\\:block * {
            visibility: visible;
          }
          .print\\:block {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
          }
          .no-print {
            display: none !important;
          }
        }
      `}</style>
    </AppLayout>
  )
}

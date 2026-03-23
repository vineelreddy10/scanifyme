import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AppLayout, PageHeader, Content, Card, ErrorBanner } from '../components/ui'

interface QRCodeTagDetail {
  name: string
  qr_uid: string
  qr_token: string
  qr_url: string
  qr_image: string | null
  batch: string | null
  status: string
  created_on: string | null
}

function getCSRFToken(): string {
  return typeof window !== 'undefined' ? (window as Window & { csrf_token?: string }).csrf_token || '' : ''
}

async function fetchQRDetail(tagName: string): Promise<QRCodeTagDetail> {
  const url = '/api/method/scanifyme.qr_management.api.qr_api.get_qr_tag_detail'
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
    body: JSON.stringify({ tag_name: tagName }),
    credentials: 'include'
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to fetch QR code' }))
    throw new Error(error.message || 'Failed to fetch QR code')
  }

  const data = await response.json()
  return data.message as QRCodeTagDetail
}

function getImageUrl(filePath: string | null): string | null {
  if (!filePath) return null
  if (filePath.startsWith('http://') || filePath.startsWith('https://')) return filePath
  if (typeof window !== 'undefined') {
    return window.location.origin + filePath
  }
  return filePath
}

export default function QRPrint() {
  const { name } = useParams<{ name: string }>()
  const navigate = useNavigate()
  const [tag, setTag] = useState<QRCodeTagDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadTag = useCallback(async () => {
    if (!name) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await fetchQRDetail(name)
      setTag(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load QR code'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [name])

  useEffect(() => {
    loadTag()
  }, [loadTag])

  if (isLoading) {
    return (
      <AppLayout>
        <PageHeader title="Print QR Code" />
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
        <PageHeader title="Print QR Code" />
        <Content>
          <ErrorBanner message={error} onRetry={loadTag} />
        </Content>
      </AppLayout>
    )
  }

  if (!tag) {
    return (
      <AppLayout>
        <PageHeader title="Print QR Code" />
        <Content>
          <div className="text-center py-12">
            <p className="text-gray-500">QR code not found</p>
          </div>
        </Content>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <PageHeader
        title={`Print QR Code: ${tag.qr_uid}`}
        description={tag.batch ? `Batch: ${tag.batch}` : undefined}
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
          <Card title="QR Code Details">
            <div className="flex flex-col items-center space-y-6">
              {getImageUrl(tag.qr_image) ? (
                <img 
                  src={getImageUrl(tag.qr_image) || ''} 
                  alt={tag.qr_uid}
                  className="w-64 h-64 object-contain"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(tag.qr_url)}`
                  }}
                />
              ) : (
                <div className="w-64 h-64 bg-gray-100 rounded flex items-center justify-center">
                  <svg className="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                  </svg>
                </div>
              )}
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{tag.qr_uid}</div>
                <div className="mt-2 text-sm text-gray-500 break-all">{tag.qr_url}</div>
              </div>
            </div>
            <dl className="mt-6 grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium text-gray-500">QR Token</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">{tag.qr_token}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Status</dt>
                <dd className="mt-1">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    tag.status === 'Generated' ? 'bg-blue-100 text-blue-800' :
                    tag.status === 'Printed' ? 'bg-purple-100 text-purple-800' :
                    tag.status === 'In Stock' ? 'bg-green-100 text-green-800' :
                    tag.status === 'Assigned' ? 'bg-yellow-100 text-yellow-800' :
                    tag.status === 'Activated' ? 'bg-emerald-100 text-emerald-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {tag.status}
                  </span>
                </dd>
              </div>
              {tag.batch && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Batch</dt>
                  <dd className="mt-1 text-sm text-gray-900">{tag.batch}</dd>
                </div>
              )}
              {tag.created_on && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Created On</dt>
                  <dd className="mt-1 text-sm text-gray-900">{tag.created_on}</dd>
                </div>
              )}
            </dl>
          </Card>
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
        }
      `}</style>
    </AppLayout>
  )
}

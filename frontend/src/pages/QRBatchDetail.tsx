import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AppLayout, PageHeader, Content, Card, ErrorBanner, SuccessBanner } from '../components/ui'

interface BatchDetail {
  name: string
  batch_name: string
  batch_prefix: string | null
  batch_size: number
  status: string
  created_by: string
  created_on: string | null
  total_tags: number
  status_counts: Record<string, number>
  can_generate: boolean
}

function getCSRFToken(): string {
  return typeof window !== 'undefined' ? (window as Window & { csrf_token?: string }).csrf_token || '' : ''
}

async function fetchBatchDetail(batchName: string): Promise<BatchDetail> {
  const url = '/api/method/scanifyme.qr_management.api.qr_api.get_qr_batch_detail'
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
    body: JSON.stringify({ batch_name: batchName }),
    credentials: 'include'
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to fetch batch' }))
    throw new Error(error.message || 'Failed to fetch batch')
  }

  const data = await response.json()
  return data.message as BatchDetail
}

async function generateQRCodes(batchName: string): Promise<{ success: boolean; tags_generated: number }> {
  const url = '/api/method/scanifyme.qr_management.api.qr_api.generate_qr_codes_for_batch'
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
    body: JSON.stringify({ batch_name: batchName }),
    credentials: 'include'
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to generate QR codes' }))
    throw new Error(error.message || 'Failed to generate QR codes')
  }

  return response.json().then(d => d.message)
}

const statusColors: Record<string, string> = {
  'Generated': 'bg-blue-100 text-blue-800',
  'Printed': 'bg-purple-100 text-purple-800',
  'In Stock': 'bg-green-100 text-green-800',
  'Assigned': 'bg-yellow-100 text-yellow-800',
  'Activated': 'bg-emerald-100 text-emerald-800',
  'Suspended': 'bg-gray-100 text-gray-800',
  'Retired': 'bg-red-100 text-red-800',
}

export default function QRBatchDetail() {
  const { name } = useParams<{ name: string }>()
  const navigate = useNavigate()
  const [batch, setBatch] = useState<BatchDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generateSuccess, setGenerateSuccess] = useState<string | null>(null)
  const [generateError, setGenerateError] = useState<string | null>(null)

  const loadBatch = useCallback(async () => {
    if (!name) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await fetchBatchDetail(name)
      setBatch(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load batch'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [name])

  useEffect(() => {
    loadBatch()
  }, [loadBatch])

  const handleGenerate = async () => {
    if (!name || !batch) return
    setIsGenerating(true)
    setGenerateError(null)
    try {
      const result = await generateQRCodes(name)
      setGenerateSuccess(`Successfully generated ${result.tags_generated} QR codes!`)
      await loadBatch()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate QR codes'
      setGenerateError(message)
    } finally {
      setIsGenerating(false)
    }
  }

  if (isLoading) {
    return (
      <AppLayout>
        <PageHeader title="QR Batch" />
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
        <PageHeader title="QR Batch" />
        <Content>
          <ErrorBanner message={error} onRetry={loadBatch} />
        </Content>
      </AppLayout>
    )
  }

  if (!batch) {
    return (
      <AppLayout>
        <PageHeader title="QR Batch" />
        <Content>
          <div className="text-center py-12">
            <p className="text-gray-500">Batch not found</p>
          </div>
        </Content>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <PageHeader
        title={batch.batch_name}
        description={`QR Batch • ${batch.total_tags} tags`}
        actions={
          <div className="flex items-center gap-3">
            {batch.can_generate && (
              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {isGenerating ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Generating...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Generate QRs
                  </>
                )}
              </button>
            )}
            <button
              onClick={() => navigate(`/qr-batches/${name}/print`)}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              Print Batch
            </button>
            <button
              onClick={() => navigate(`/list/QR%20Code%20Tag?batch=${encodeURIComponent(batch.name)}`)}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100"
            >
              <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
              View QR Tags
            </button>
            <button
              onClick={loadBatch}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        }
      />
      <Content>
        {generateSuccess && <SuccessBanner message={generateSuccess} onClose={() => setGenerateSuccess(null)} />}
        {generateError && <ErrorBanner message={generateError} onClose={() => setGenerateError(null)} />}

        <div className="space-y-6">
          {/* Batch Info */}
          <Card title="Batch Information">
            <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">Batch Name</dt>
                <dd className="mt-1 text-sm text-gray-900">{batch.batch_name}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Prefix</dt>
                <dd className="mt-1 text-sm text-gray-900">{batch.batch_prefix || '—'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Size</dt>
                <dd className="mt-1 text-sm text-gray-900">{batch.batch_size}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Status</dt>
                <dd className="mt-1">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    batch.status === 'Draft' ? 'bg-gray-100 text-gray-800' :
                    batch.status === 'Generated' ? 'bg-blue-100 text-blue-800' :
                    batch.status === 'Printed' ? 'bg-purple-100 text-purple-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {batch.status}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Created By</dt>
                <dd className="mt-1 text-sm text-gray-900">{batch.created_by || '—'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Created On</dt>
                <dd className="mt-1 text-sm text-gray-900">{batch.created_on || '—'}</dd>
              </div>
            </dl>
          </Card>

          {/* Tag Status Summary */}
          <Card title="Tag Status Summary">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {Object.entries(batch.status_counts).map(([status, count]) => (
                <div key={status} className="bg-gray-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-gray-900">{count}</div>
                  <div className={`text-sm font-medium mt-1 ${statusColors[status] || 'text-gray-600'}`}>
                    {status}
                  </div>
                </div>
              ))}
              {Object.keys(batch.status_counts).length === 0 && (
                <div className="col-span-full text-center py-4 text-gray-500">
                  No QR codes generated yet
                </div>
              )}
            </div>
          </Card>

          {/* Quick Actions */}
          <Card title="Quick Actions">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <button
                onClick={() => navigate(`/list/QR%20Code%20Tag?batch=${encodeURIComponent(batch.name)}`)}
                className="flex items-center p-4 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors"
              >
                <div className="flex-shrink-0 w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                  </svg>
                </div>
                <div className="ml-4 text-left">
                  <div className="text-sm font-medium text-gray-900">View All Tags</div>
                  <div className="text-xs text-gray-500">{batch.total_tags} total</div>
                </div>
              </button>
              <button
                onClick={() => navigate(`/qr-batches/${name}/print`)}
                className="flex items-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
              >
                <div className="flex-shrink-0 w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                  </svg>
                </div>
                <div className="ml-4 text-left">
                  <div className="text-sm font-medium text-gray-900">Print Batch</div>
                  <div className="text-xs text-gray-500">Print all QR codes</div>
                </div>
              </button>
              {batch.can_generate && (
                <button
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  className="flex items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors disabled:opacity-50"
                >
                  <div className="flex-shrink-0 w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                  </div>
                  <div className="ml-4 text-left">
                    <div className="text-sm font-medium text-gray-900">
                      {isGenerating ? 'Generating...' : 'Generate QRs'}
                    </div>
                    <div className="text-xs text-gray-500">Create {batch.batch_size} QR codes</div>
                  </div>
                </button>
              )}
            </div>
          </Card>
        </div>
      </Content>
    </AppLayout>
  )
}

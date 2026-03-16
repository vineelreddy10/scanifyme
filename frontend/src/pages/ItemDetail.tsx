import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { getItemDetails, updateItemStatus, ItemDetails } from '../api/frappe'

const ItemDetail = () => {
  const { id } = useParams<{ id: string }>()
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()
  const [item, setItem] = useState<ItemDetails | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isUpdating, setIsUpdating] = useState(false)
  const [showStatusMenu, setShowStatusMenu] = useState(false)

  const handleLogout = async () => {
    await logout()
    window.location.href = '/login'
  }

  useEffect(() => {
    if (id) {
      loadItem()
    }
  }, [id])

  const loadItem = async () => {
    setIsLoading(true)
    try {
      const data = await getItemDetails(id!)
      if (data) {
        setItem(data)
      } else {
        setError('Item not found or you do not have permission to view it')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load item')
    } finally {
      setIsLoading(false)
    }
  }

  const handleStatusChange = async (newStatus: string) => {
    if (!item) return
    
    setIsUpdating(true)
    try {
      const result = await updateItemStatus(item.id, newStatus)
      if (result.success) {
        setItem({ ...item, status: newStatus })
        setShowStatusMenu(false)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update status')
    } finally {
      setIsUpdating(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      'Draft': 'bg-gray-100 text-gray-800',
      'Active': 'bg-green-100 text-green-800',
      'Lost': 'bg-red-100 text-red-800',
      'Recovered': 'bg-blue-100 text-blue-800',
      'Archived': 'bg-yellow-100 text-yellow-800',
    }
    return styles[status] || 'bg-gray-100 text-gray-800'
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never'
    return new Date(dateStr).toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <svg className="animate-spin h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
    )
  }

  if (error || !item) {
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-bold text-gray-900">ScanifyMe</h1>
              </div>
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => navigate('/items')}
                  className="text-sm text-indigo-600 hover:text-indigo-800"
                >
                  ← Back to Items
                </button>
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <p className="text-sm text-red-700">{error || 'Item not found'}</p>
            </div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-6">
              <h1 className="text-xl font-bold text-gray-900">ScanifyMe</h1>
              <div className="flex space-x-4">
                <button
                  onClick={() => navigate('/')}
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Dashboard
                </button>
                <button
                  onClick={() => navigate('/items')}
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Items
                </button>
                <button
                  onClick={() => navigate('/activate-qr')}
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Activate QR
                </button>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                {currentUser as string}
              </span>
              <button
                onClick={handleLogout}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-6 flex items-center justify-between">
            <button
              onClick={() => navigate('/items')}
              className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Items
            </button>
            <div className="relative">
              <button
                onClick={() => setShowStatusMenu(!showStatusMenu)}
                disabled={isUpdating}
                className={`inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md ${getStatusBadge(item.status)} hover:opacity-80`}
              >
                {isUpdating ? 'Updating...' : item.status}
                <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {showStatusMenu && (
                <div className="absolute right-0 mt-2 w-40 bg-white rounded-md shadow-lg border z-10">
                  {['Active', 'Lost', 'Recovered', 'Archived'].filter(s => s !== item.status).map(status => (
                    <button
                      key={status}
                      onClick={() => handleStatusChange(status)}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Mark as {status}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-white shadow rounded-xl border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Item Details</h2>
                <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Item Name</dt>
                    <dd className="mt-1 text-sm text-gray-900">{item.item_name}</dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Category</dt>
                    <dd className="mt-1 text-sm text-gray-900">{item.item_category_name || '-'}</dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Public Label</dt>
                    <dd className="mt-1 text-sm text-gray-900">{item.public_label || '-'}</dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Status</dt>
                    <dd className="mt-1">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(item.status)}`}>
                        {item.status}
                      </span>
                    </dd>
                  </div>
                </dl>
              </div>

              <div className="bg-white shadow rounded-xl border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Recovery Information</h2>
                <dl className="space-y-4">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Recovery Note</dt>
                    <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                      {item.recovery_note || 'No recovery instructions provided'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Reward Note</dt>
                    <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                      {item.reward_note || 'No reward information provided'}
                    </dd>
                  </div>
                </dl>
              </div>

              {item.photos && item.photos.length > 0 && (
                <div className="bg-white shadow rounded-xl border p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">Photos</h2>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    {item.photos.map((photo, idx) => (
                      <div key={idx} className="relative aspect-square bg-gray-100 rounded-lg overflow-hidden">
                        {photo.image ? (
                          <img 
                            src={photo.image} 
                            alt={photo.caption || 'Item photo'} 
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="flex items-center justify-center h-full text-gray-400">
                            No image
                          </div>
                        )}
                        {photo.caption && (
                          <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs p-1">
                            {photo.caption}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-6">
              <div className="bg-white shadow rounded-xl border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">QR Code</h2>
                {item.qr_code && (
                  <dl className="space-y-3">
                    <div>
                      <dt className="text-sm font-medium text-gray-500">QR UID</dt>
                      <dd className="mt-1 text-sm font-mono text-gray-900">{item.qr_code.uid}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Status</dt>
                      <dd className="mt-1">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          {item.qr_code.status}
                        </span>
                      </dd>
                    </div>
                  </dl>
                )}
              </div>

              <div className="bg-white shadow rounded-xl border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Activity</h2>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Activated</dt>
                    <dd className="mt-1 text-sm text-gray-900">{formatDate(item.activation_date)}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Last Scan</dt>
                    <dd className="mt-1 text-sm text-gray-900">{formatDate(item.last_scan_at)}</dd>
                  </div>
                </dl>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <div className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="ml-3">
                    <p className="text-sm text-blue-700">
                      Founders can scan the QR code to see your recovery notes and contact you.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default ItemDetail
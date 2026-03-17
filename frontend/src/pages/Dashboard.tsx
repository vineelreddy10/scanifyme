import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { getQRBatches, getQRTags, type QRBatch, type QRCodeTag } from '../api/frappe'
import NotificationBell from '../components/NotificationBell'

const Dashboard = () => {
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()
  const [batches, setBatches] = useState<QRBatch[]>([])
  const [tags, setTags] = useState<QRCodeTag[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [batchesData, tagsData] = await Promise.all([
        getQRBatches(5),
        getQRTags(undefined, undefined, 5),
      ])
      setBatches(batchesData)
      setTags(tagsData)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = async () => {
    await logout()
    window.location.href = '/login'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Generated':
        return 'bg-blue-100 text-blue-800'
      case 'Printed':
        return 'bg-yellow-100 text-yellow-800'
      case 'In Stock':
        return 'bg-green-100 text-green-800'
      case 'Assigned':
        return 'bg-purple-100 text-purple-800'
      case 'Activated':
        return 'bg-emerald-100 text-emerald-800'
      case 'Suspended':
        return 'bg-red-100 text-red-800'
      case 'Retired':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
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
                  className="text-indigo-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
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
                <button
                  onClick={() => navigate('/recovery')}
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Recovery
                </button>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <NotificationBell />
              <span className="text-sm text-gray-600">
                {currentUser as string}
              </span>
              <a
                href="/app/settings/users"
                className="text-sm text-indigo-600 hover:text-indigo-800"
              >
                Profile
              </a>
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
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white overflow-hidden shadow rounded-xl border">
              <div className="p-5">
                <h3 className="text-sm font-medium text-gray-500">Total Batches</h3>
                <p className="mt-2 text-3xl font-bold text-indigo-600">{batches.length}</p>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-xl border">
              <div className="p-5">
                <h3 className="text-sm font-medium text-gray-500">Total QR Codes</h3>
                <p className="mt-2 text-3xl font-bold text-green-600">{tags.length}</p>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-xl border">
              <div className="p-5">
                <h3 className="text-sm font-medium text-gray-500">In Stock</h3>
                <p className="mt-2 text-3xl font-bold text-blue-600">
                  {tags.filter((t) => t.status === 'In Stock').length}
                </p>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-xl border">
              <div className="p-5">
                <h3 className="text-sm font-medium text-gray-500">Activated</h3>
                <p className="mt-2 text-3xl font-bold text-emerald-600">
                  {tags.filter((t) => t.status === 'Activated').length}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white shadow rounded-xl border">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">Recent Batches</h2>
                  <a
                    href="/app/qr-batch"
                    className="text-sm text-indigo-600 hover:text-indigo-800"
                  >
                    View All
                  </a>
                </div>
                {batches.length === 0 ? (
                  <p className="text-gray-500 text-sm">No batches created yet.</p>
                ) : (
                  <div className="space-y-3">
                    {batches.map((batch) => (
                      <div
                        key={batch.name}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div>
                          <p className="font-medium text-gray-900">{batch.batch_name}</p>
                          <p className="text-sm text-gray-500">
                            {batch.batch_size} codes · {new Date(batch.created_on).toLocaleDateString()}
                          </p>
                        </div>
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            batch.status === 'Generated'
                              ? 'bg-blue-100 text-blue-800'
                              : batch.status === 'Printed'
                              ? 'bg-yellow-100 text-yellow-800'
                              : batch.status === 'Distributed'
                              ? 'bg-purple-100 text-purple-800'
                              : batch.status === 'Closed'
                              ? 'bg-gray-100 text-gray-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {batch.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="bg-white shadow rounded-xl border">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">Recent QR Codes</h2>
                  <a
                    href="/app/qr-code-tag"
                    className="text-sm text-indigo-600 hover:text-indigo-800"
                  >
                    View All
                  </a>
                </div>
                {tags.length === 0 ? (
                  <p className="text-gray-500 text-sm">No QR codes generated yet.</p>
                ) : (
                  <div className="space-y-3">
                    {tags.map((tag) => (
                      <div
                        key={tag.name}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div>
                          <p className="font-medium text-gray-900 font-mono">{tag.qr_uid}</p>
                          <p className="text-sm text-gray-500">
                            {tag.batch} · {new Date(tag.created_on).toLocaleDateString()}
                          </p>
                        </div>
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                            tag.status
                          )}`}
                        >
                          {tag.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="mt-8 bg-white shadow rounded-xl border">
            <div className="p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <a
                  href="/app/qr-batch/new-qr-batch-1"
                  className="flex items-center justify-center p-4 bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 transition-colors"
                >
                  <svg
                    className="w-5 h-5 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4v16m8-8H4"
                    />
                  </svg>
                  Create New Batch
                </a>
                <a
                  href="/items"
                  className="flex items-center justify-center p-4 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors"
                >
                  <svg
                    className="w-5 h-5 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                    />
                  </svg>
                  Manage Items
                </a>
                <a
                  href="/activate-qr"
                  className="flex items-center justify-center p-4 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors"
                >
                  <svg
                    className="w-5 h-5 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h2M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"
                    />
                  </svg>
                  Activate QR Code
                </a>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default Dashboard

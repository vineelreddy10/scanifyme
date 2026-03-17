import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

// Types
export interface RecoveryCase {
  name: string
  case_title: string
  status: string
  opened_on: string
  last_activity_on: string
  registered_item: string
  finder_name: string | null
  finder_contact_hint: string | null
  latest_message_preview: string | null
}

// API functions
async function frappeCall<T>(method: string, args: Record<string, unknown> = {}): Promise<T> {
  const baseURL = ''
  const url = baseURL ? `${baseURL}/api/method/${method}` : `/api/method/${method}`
  
  const csrfToken = typeof window !== 'undefined' ? (window as any).csrf_token : ''
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  
  if (csrfToken) {
    headers['X-Frappe-CSRF-Token'] = csrfToken
  }
  
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(args),
    credentials: 'include',
  })

  if (!response.ok) {
    throw new Error(`API call failed: ${response.statusText}`)
  }

  const data = await response.json()
  return data.message as T
}

export const getOwnerRecoveryCases = async (status?: string): Promise<RecoveryCase[]> => {
  return await frappeCall<RecoveryCase[]>('scanifyme.recovery.api.recovery_api.get_owner_recovery_cases', {
    status: status || null,
  })
}

const RecoveryList = () => {
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()
  const [cases, setCases] = useState<RecoveryCase[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')

  const handleLogout = async () => {
    await logout()
    window.location.href = '/login'
  }

  useEffect(() => {
    loadCases()
  }, [statusFilter])

  const loadCases = async () => {
    setIsLoading(true)
    try {
      const data = await getOwnerRecoveryCases(statusFilter || undefined)
      setCases(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load recovery cases')
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      'Open': 'bg-yellow-100 text-yellow-800',
      'Owner Responded': 'bg-blue-100 text-blue-800',
      'Return Planned': 'bg-purple-100 text-purple-800',
      'Recovered': 'bg-green-100 text-green-800',
      'Closed': 'bg-gray-100 text-gray-800',
      'Invalid': 'bg-red-100 text-red-800',
      'Spam': 'bg-red-100 text-red-800',
    }
    return styles[status] || 'bg-gray-100 text-gray-800'
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
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
                <button
                  onClick={() => navigate('/recovery')}
                  className="text-indigo-600 hover:text-indigo-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Recovery
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
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Recovery Cases</h2>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="mt-1 block w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value="">All Statuses</option>
              <option value="Open">Open</option>
              <option value="Owner Responded">Owner Responded</option>
              <option value="Return Planned">Return Planned</option>
              <option value="Recovered">Recovered</option>
              <option value="Closed">Closed</option>
            </select>
          </div>

          {isLoading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-800">{error}</p>
              <button
                onClick={loadCases}
                className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                Try again
              </button>
            </div>
          ) : cases.length === 0 ? (
            <div className="bg-white shadow rounded-lg p-6">
              <p className="text-gray-500 text-center">No recovery cases found.</p>
            </div>
          ) : (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {cases.map((recoveryCase) => (
                  <li key={recoveryCase.name}>
                    <button
                      onClick={() => navigate(`/recovery/${recoveryCase.name}`)}
                      className="block hover:bg-gray-50 w-full text-left"
                    >
                      <div className="px-4 py-4 sm:px-6">
                        <div className="flex items-center justify-between">
                          <div className="flex flex-col">
                            <p className="text-lg font-medium text-indigo-600 truncate">
                              {recoveryCase.case_title}
                            </p>
                            <p className="text-sm text-gray-500 mt-1">
                              {recoveryCase.registered_item}
                            </p>
                          </div>
                          <div className="ml-2 flex-shrink-0 flex">
                            <p className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(recoveryCase.status)}`}>
                              {recoveryCase.status}
                            </p>
                          </div>
                        </div>
                        <div className="mt-2 sm:flex sm:justify-between">
                          <div className="sm:flex">
                            <p className="flex items-center text-sm text-gray-500">
                              {recoveryCase.finder_name ? `Finder: ${recoveryCase.finder_name}` : 'Anonymous Finder'}
                            </p>
                          </div>
                          <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                            <p>
                              Last activity: {formatDate(recoveryCase.last_activity_on)}
                            </p>
                          </div>
                        </div>
                        {recoveryCase.latest_message_preview && (
                          <div className="mt-2">
                            <p className="text-sm text-gray-600 italic">
                              "{recoveryCase.latest_message_preview}"
                            </p>
                          </div>
                        )}
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default RecoveryList

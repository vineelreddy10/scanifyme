import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppLayout } from '../components/ui/AppLayout'
import { CaseStatusBadge } from '../components/ui/StatusBadge'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { PageLoading, ListItemSkeleton } from '../components/ui/LoadingSpinner'
import EmptyState from '../components/EmptyState'

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
  const navigate = useNavigate()
  const [cases, setCases] = useState<RecoveryCase[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')

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

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="space-y-4">
          <ListItemSkeleton />
          <ListItemSkeleton />
          <ListItemSkeleton />
        </div>
      )
    }

    if (error) {
      return (
        <ErrorBanner
          message={error}
          onRetry={loadCases}
        />
      )
    }

     if (cases.length === 0) {
       return (
         <EmptyState
           icon="inbox"
           title="No recovery cases yet"
           description="Recovery cases appear here when someone scans your QR tags and contacts you about a lost item. You'll see what information finders can access, maintain control over your privacy, and can reply through secure messages."
           action={{
             label: 'Register an Item',
             onClick: () => navigate('/activate-qr'),
             variant: 'primary',
           }}
         />
       );
     }

    return (
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
                      <CaseStatusBadge status={recoveryCase.status} />
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
    )
  }

  return (
    <AppLayout>
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

      {renderContent()}
    </AppLayout>
  )
}

export default RecoveryList

import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

// Types
export interface RecoveryCaseDetails {
  name: string
  case_title: string
  status: string
  opened_on: string
  last_activity_on: string
  closed_on: string | null
  finder_name: string | null
  finder_contact_hint: string | null
  notes_internal: string | null
  registered_item: {
    name: string
    item_name: string
    public_label: string | null
    qr_code_tag: string | null
  }
  qr_tag: {
    name: string
    qr_token: string
  }
}

export interface RecoveryMessage {
  name: string
  sender_type: 'Finder' | 'Owner' | 'System'
  sender_name: string | null
  message: string
  attachment: string | null
  created_on: string
  is_read_by_owner: boolean
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

export const getRecoveryCaseDetails = async (caseId: string): Promise<RecoveryCaseDetails> => {
  return await frappeCall<RecoveryCaseDetails>('scanifyme.recovery.api.recovery_api.get_recovery_case_details', {
    case_id: caseId,
  })
}

export const getRecoveryCaseMessages = async (caseId: string): Promise<RecoveryMessage[]> => {
  return await frappeCall<RecoveryMessage[]>('scanifyme.recovery.api.recovery_api.get_recovery_case_messages', {
    case_id: caseId,
  })
}

export const sendOwnerReply = async (caseId: string, message: string): Promise<{ success: boolean; message: string }> => {
  return await frappeCall<{ success: boolean; message: string }>('scanifyme.recovery.api.recovery_api.send_owner_reply', {
    case_id: caseId,
    message,
  })
}

export const updateRecoveryCaseStatus = async (caseId: string, status: string): Promise<{ success: boolean; message: string }> => {
  return await frappeCall<{ success: boolean; message: string }>('scanifyme.recovery.api.recovery_api.mark_recovery_case_status', {
    case_id: caseId,
    status,
  })
}

const RecoveryDetail = () => {
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [caseDetails, setCaseDetails] = useState<RecoveryCaseDetails | null>(null)
  const [messages, setMessages] = useState<RecoveryMessage[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [replyMessage, setReplyMessage] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [sendError, setSendError] = useState('')
  const [sendSuccess, setSendSuccess] = useState('')
  const [showStatusModal, setShowStatusModal] = useState(false)
  const [newStatus, setNewStatus] = useState('')

  const handleLogout = async () => {
    await logout()
    window.location.href = '/login'
  }

  useEffect(() => {
    if (id) {
      loadCaseData()
    }
  }, [id])

  const loadCaseData = async () => {
    setIsLoading(true)
    try {
      const [details, msgs] = await Promise.all([
        getRecoveryCaseDetails(id!),
        getRecoveryCaseMessages(id!),
      ])
      setCaseDetails(details)
      setMessages(msgs)
    } catch (err: any) {
      setError(err.message || 'Failed to load case details')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendReply = async () => {
    if (!replyMessage.trim()) return
    
    setIsSending(true)
    setSendError('')
    setSendSuccess('')
    
    try {
      const result = await sendOwnerReply(id!, replyMessage)
      if (result.success) {
        setSendSuccess('Reply sent successfully!')
        setReplyMessage('')
        loadCaseData() // Refresh messages
      } else {
        setSendError(result.message || 'Failed to send reply')
      }
    } catch (err: any) {
      setSendError(err.message || 'Failed to send reply')
    } finally {
      setIsSending(false)
    }
  }

  const handleStatusUpdate = async () => {
    if (!newStatus) return
    
    try {
      const result = await updateRecoveryCaseStatus(id!, newStatus)
      if (result.success) {
        loadCaseData() // Refresh case details
        setShowStatusModal(false)
      } else {
        setSendError(result.message || 'Failed to update status')
      }
    } catch (err: any) {
      setSendError(err.message || 'Failed to update status')
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

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  if (error || !caseDetails) {
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <button onClick={() => navigate('/recovery')} className="text-gray-600 hover:text-gray-900 mr-4">
                  ← Back
                </button>
                <h1 className="text-xl font-bold text-gray-900">Error</h1>
              </div>
            </div>
          </div>
        </nav>
        <div className="max-w-7xl mx-auto py-6 px-4">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-800">{error || 'Case not found'}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-6">
              <button onClick={() => navigate('/recovery')} className="text-gray-600 hover:text-gray-900">
                ← Back
              </button>
              <h1 className="text-xl font-bold text-gray-900">Recovery Case</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">{currentUser as string}</span>
              <button onClick={handleLogout} className="text-sm text-red-600 hover:text-red-800">
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Case Info Card */}
          <div className="bg-white shadow rounded-lg mb-6">
            <div className="px-4 py-5 sm:px-6">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    {caseDetails.case_title}
                  </h3>
                  <p className="mt-1 max-w-2xl text-sm text-gray-500">
                    Item: {caseDetails.registered_item?.item_name || caseDetails.registered_item?.name}
                  </p>
                </div>
                <div className="flex flex-col items-end">
                  <span className={`px-3 py-1 inline-flex text-sm leading-5 font-semibold rounded-full ${getStatusBadge(caseDetails.status)}`}>
                    {caseDetails.status}
                  </span>
                  <button
                    onClick={() => { setNewStatus(caseDetails.status); setShowStatusModal(true); }}
                    className="mt-2 text-sm text-indigo-600 hover:text-indigo-800"
                  >
                    Change Status
                  </button>
                </div>
              </div>
              <div className="mt-4 border-t border-gray-200 pt-4">
                <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-3">
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Finder</dt>
                    <dd className="mt-1 text-sm text-gray-900">{caseDetails.finder_name || 'Anonymous'}</dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Contact</dt>
                    <dd className="mt-1 text-sm text-gray-900">{caseDetails.finder_contact_hint || '-'}</dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Opened</dt>
                    <dd className="mt-1 text-sm text-gray-900">{formatDate(caseDetails.opened_on)}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="bg-white shadow rounded-lg mb-6">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Messages</h3>
              
              {messages.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No messages yet.</p>
              ) : (
                <div className="space-y-4">
                  {messages.map((msg) => (
                    <div
                      key={msg.name}
                      className={`p-4 rounded-lg ${
                        msg.sender_type === 'Owner'
                          ? 'bg-indigo-50 ml-8'
                          : msg.sender_type === 'Finder'
                          ? 'bg-gray-50 mr-8'
                          : 'bg-yellow-50 mx-8'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {msg.sender_name || msg.sender_type}
                            {msg.sender_type === 'Owner' && ' (You)'}
                          </p>
                          <p className="text-xs text-gray-500">{formatDate(msg.created_on)}</p>
                        </div>
                      </div>
                      <p className="mt-2 text-sm text-gray-800 whitespace-pre-wrap">{msg.message}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Reply Box */}
          {caseDetails.status !== 'Closed' && caseDetails.status !== 'Recovered' && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Send a Reply</h3>
                
                {sendError && (
                  <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-2">
                    <p className="text-sm text-red-800">{sendError}</p>
                  </div>
                )}
                
                {sendSuccess && (
                  <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-2">
                    <p className="text-sm text-green-800">{sendSuccess}</p>
                  </div>
                )}
                
                <textarea
                  rows={4}
                  className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border border-gray-300 rounded-md p-2"
                  placeholder="Type your message to the finder..."
                  value={replyMessage}
                  onChange={(e) => setReplyMessage(e.target.value)}
                />
                <div className="mt-3 flex justify-end">
                  <button
                    onClick={handleSendReply}
                    disabled={isSending || !replyMessage.trim()}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSending ? 'Sending...' : 'Send Reply'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Status Update Modal */}
      {showStatusModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Update Case Status</h3>
            <select
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value="Open">Open</option>
              <option value="Owner Responded">Owner Responded</option>
              <option value="Return Planned">Return Planned</option>
              <option value="Recovered">Recovered</option>
              <option value="Closed">Closed</option>
              <option value="Invalid">Invalid</option>
              <option value="Spam">Spam</option>
            </select>
            <div className="mt-4 flex justify-end space-x-2">
              <button
                onClick={() => setShowStatusModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleStatusUpdate}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
              >
                Update
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default RecoveryDetail

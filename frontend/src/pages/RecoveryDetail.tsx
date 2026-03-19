import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { safeToFixed, isValidNumber } from '../utils/number'

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

export interface LocationShare {
  name: string
  latitude: number | null   // null when no location shared yet
  longitude: number | null  // null when no location shared yet
  accuracy_meters: number | null
  source: string
  shared_on: string
  note: string | null
  is_latest: boolean
  maps_url: string
}

export interface TimelineEvent {
  name: string
  event_type: string
  event_label: string | null
  actor_type: string
  actor_reference: string | null
  event_time: string
  summary: string | null
  reference_doctype: string | null
  reference_name: string | null
}

export interface HandoverDetails {
  case_id: string
  handover_status: string
  handover_note: string | null
  latest_location_summary: string | null
  valid_statuses: string[]
}

export interface RewardStatusDetails {
  case: string
  reward_offered: boolean
  reward_display_text: string | null
  reward_status: string | null
  reward_internal_note: string | null
  reward_last_updated_on: string | null
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

export const getLatestCaseLocation = async (caseId: string): Promise<LocationShare | null> => {
  return await frappeCall<LocationShare | null>('scanifyme.recovery.api.recovery_api.get_latest_case_location', {
    case_id: caseId,
  })
}

export const getRecoveryCaseTimeline = async (caseId: string): Promise<TimelineEvent[]> => {
  return await frappeCall<TimelineEvent[]>('scanifyme.recovery.api.recovery_api.get_recovery_case_timeline', {
    case_id: caseId,
  })
}

export const getCaseHandoverDetails = async (caseId: string): Promise<HandoverDetails> => {
  return await frappeCall<HandoverDetails>('scanifyme.recovery.api.recovery_api.get_case_handover_details', {
    case_id: caseId,
  })
}

export const updateHandoverStatus = async (caseId: string, handoverStatus: string, handoverNote?: string): Promise<{ success: boolean; message: string }> => {
  return await frappeCall<{ success: boolean; message: string }>('scanifyme.recovery.api.recovery_api.update_handover_status', {
    case_id: caseId,
    handover_status: handoverStatus,
    handover_note: handoverNote,
  })
}

export const getCaseRewardStatus = async (caseId: string): Promise<RewardStatusDetails> => {
  return await frappeCall<RewardStatusDetails>('scanifyme.recovery.api.recovery_api.get_case_reward_status', {
    case_id: caseId,
  })
}

export const updateRecoveryCaseRewardStatus = async (
  caseId: string,
  rewardStatus: string,
  rewardInternalNote?: string
): Promise<{ success: boolean; message: string }> => {
  return await frappeCall<{ success: boolean; message: string }>('scanifyme.recovery.api.recovery_api.update_recovery_case_reward_status', {
    case_id: caseId,
    reward_status: rewardStatus,
    reward_internal_note: rewardInternalNote,
  })
}

const RecoveryDetail = () => {
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [caseDetails, setCaseDetails] = useState<RecoveryCaseDetails | null>(null)
  const [messages, setMessages] = useState<RecoveryMessage[]>([])
  const [latestLocation, setLatestLocation] = useState<LocationShare | null>(null)
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])
  const [handoverDetails, setHandoverDetails] = useState<HandoverDetails | null>(null)
  const [rewardStatus, setRewardStatus] = useState<RewardStatusDetails | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [replyMessage, setReplyMessage] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [sendError, setSendError] = useState('')
  const [sendSuccess, setSendSuccess] = useState('')
  const [showStatusModal, setShowStatusModal] = useState(false)
  const [showHandoverModal, setShowHandoverModal] = useState(false)
  const [newStatus, setNewStatus] = useState('')
  const [newHandoverStatus, setNewHandoverStatus] = useState('')
  const [handoverNote, setHandoverNote] = useState('')
  const [showTimeline, setShowTimeline] = useState(false)
  const [showRewardModal, setShowRewardModal] = useState(false)
  const [newRewardStatus, setNewRewardStatus] = useState('')
  const [rewardInternalNote, setRewardInternalNote] = useState('')

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
      const [details, msgs, location, timelineData, handover, reward] = await Promise.all([
        getRecoveryCaseDetails(id!),
        getRecoveryCaseMessages(id!),
        getLatestCaseLocation(id!),
        getRecoveryCaseTimeline(id!),
        getCaseHandoverDetails(id!),
        getCaseRewardStatus(id!),
      ])
      setCaseDetails(details)
      setMessages(msgs)
      setLatestLocation(location)
      setTimeline(timelineData)
      setHandoverDetails(handover)
      setRewardStatus(reward)
      if (handover) {
        setNewHandoverStatus(handover.handover_status)
        setHandoverNote(handover.handover_note || '')
      }
      if (reward) {
        setNewRewardStatus(reward.reward_status || 'Not Applicable')
        setRewardInternalNote(reward.reward_internal_note || '')
      }
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

  const handleHandoverStatusUpdate = async () => {
    if (!newHandoverStatus) return
    
    try {
      const result = await updateHandoverStatus(id!, newHandoverStatus, handoverNote)
      if (result.success) {
        loadCaseData()
        setShowHandoverModal(false)
      } else {
        setSendError(result.message || 'Failed to update handover status')
      }
    } catch (err: any) {
      setSendError(err.message || 'Failed to update handover status')
    }
  }

  const handleRewardStatusUpdate = async () => {
    if (!newRewardStatus) return
    
    try {
      const result = await updateRecoveryCaseRewardStatus(id!, newRewardStatus, rewardInternalNote)
      if (result.success) {
        loadCaseData()
        setShowRewardModal(false)
      } else {
        setSendError(result.message || 'Failed to update reward status')
      }
    } catch (err: any) {
      setSendError(err.message || 'Failed to update reward status')
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

  const getHandoverStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      'Not Started': 'bg-gray-100 text-gray-800',
      'Finder Contacted': 'bg-yellow-100 text-yellow-800',
      'Location Shared': 'bg-blue-100 text-blue-800',
      'Return Planned': 'bg-purple-100 text-purple-800',
      'Handover Scheduled': 'bg-indigo-100 text-indigo-800',
      'Recovered': 'bg-green-100 text-green-800',
      'Closed': 'bg-gray-100 text-gray-800',
      'Failed': 'bg-red-100 text-red-800',
    }
    return styles[status] || 'bg-gray-100 text-gray-800'
  }

  const getRewardStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      'Not Applicable': 'bg-gray-100 text-gray-800',
      'Offered': 'bg-yellow-100 text-yellow-800',
      'Mentioned To Finder': 'bg-blue-100 text-blue-800',
      'Return Completed': 'bg-green-100 text-green-800',
      'Closed Without Reward': 'bg-red-100 text-red-800',
      'Cancelled': 'bg-gray-100 text-gray-800',
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

          {/* Handover Status Card */}
          {handoverDetails && (
            <div className="bg-white shadow rounded-lg mb-6">
              <div className="px-4 py-5 sm:px-6">
                <div className="flex justify-between items-start">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">Recovery Progress</h3>
                  <button
                    onClick={() => { setNewHandoverStatus(handoverDetails.handover_status); setHandoverNote(handoverDetails.handover_note || ''); setShowHandoverModal(true); }}
                    className="text-sm text-indigo-600 hover:text-indigo-800"
                  >
                    Update Progress
                  </button>
                </div>
                <div className="mt-4">
                  <span className={`px-3 py-1 inline-flex text-sm leading-5 font-semibold rounded-full ${getHandoverStatusBadge(handoverDetails.handover_status)}`}>
                    {handoverDetails.handover_status}
                  </span>
                  {handoverDetails.handover_note && (
                    <p className="mt-2 text-sm text-gray-600">{handoverDetails.handover_note}</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Reward Status Card */}
          {rewardStatus && (
            <div className="bg-white shadow rounded-lg mb-6">
              <div className="px-4 py-5 sm:px-6">
                <div className="flex justify-between items-start">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">Reward Status</h3>
                  <button
                    onClick={() => { setNewRewardStatus(rewardStatus.reward_status || 'Not Applicable'); setRewardInternalNote(rewardStatus.reward_internal_note || ''); setShowRewardModal(true); }}
                    className="text-sm text-indigo-600 hover:text-indigo-800"
                  >
                    Update Reward
                  </button>
                </div>
                <div className="mt-4">
                  {rewardStatus.reward_offered ? (
                    <>
                      <span className={`px-3 py-1 inline-flex text-sm leading-5 font-semibold rounded-full ${getRewardStatusBadge(rewardStatus.reward_status || 'Not Applicable')}`}>
                        {rewardStatus.reward_status || 'Not Applicable'}
                      </span>
                      {rewardStatus.reward_display_text && (
                        <p className="mt-2 text-sm text-gray-600">Reward: {rewardStatus.reward_display_text}</p>
                      )}
                      {rewardStatus.reward_internal_note && (
                        <p className="mt-2 text-sm text-gray-500">Note: {rewardStatus.reward_internal_note}</p>
                      )}
                    </>
                  ) : (
                    <p className="text-sm text-gray-500">No reward offered for this item</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Location Card */}
          {latestLocation && (
            <div className="bg-white shadow rounded-lg mb-6">
              <div className="px-4 py-5 sm:px-6">
                <div className="flex justify-between items-start">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">Finder's Location</h3>
                  {latestLocation.maps_url && (
                    <a
                      href={latestLocation.maps_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-indigo-600 hover:text-indigo-800"
                    >
                      Open in Maps →
                    </a>
                  )}
                </div>
                <div className="mt-4">
                  <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
                    <div className="sm:col-span-1">
                      <dt className="text-sm font-medium text-gray-500">Coordinates</dt>
                      <dd className="mt-1 text-sm text-gray-900 font-mono">
                        {isValidNumber(latestLocation.latitude) && isValidNumber(latestLocation.longitude)
                          ? `${safeToFixed(latestLocation.latitude, 6)}°, ${safeToFixed(latestLocation.longitude, 6)}°`
                          : '—'}
                      </dd>
                    </div>
                    {latestLocation.accuracy_meters && (
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Accuracy</dt>
                        <dd className="mt-1 text-sm text-gray-900">±{Math.round(latestLocation.accuracy_meters)}m</dd>
                      </div>
                    )}
                    <div className="sm:col-span-1">
                      <dt className="text-sm font-medium text-gray-500">Shared</dt>
                      <dd className="mt-1 text-sm text-gray-900">{formatDate(latestLocation.shared_on)}</dd>
                    </div>
                    <div className="sm:col-span-1">
                      <dt className="text-sm font-medium text-gray-500">Source</dt>
                      <dd className="mt-1 text-sm text-gray-900">{latestLocation.source}</dd>
                    </div>
                  </dl>
                  {latestLocation.note && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <dt className="text-sm font-medium text-gray-500">Note</dt>
                      <dd className="mt-1 text-sm text-gray-900">{latestLocation.note}</dd>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Timeline Card */}
          <div className="bg-white shadow rounded-lg mb-6">
            <div className="px-4 py-5 sm:px-6">
              <button
                onClick={() => setShowTimeline(!showTimeline)}
                className="flex justify-between items-center w-full"
              >
                <h3 className="text-lg leading-6 font-medium text-gray-900">Activity Timeline</h3>
                <span className="text-sm text-gray-500">
                  {showTimeline ? '▲ Hide' : `▼ Show ${timeline.length} events`}
                </span>
              </button>
              
              {showTimeline && timeline.length > 0 && (
                <div className="mt-4 border-t border-gray-200 pt-4">
                  <div className="space-y-4">
                    {timeline.map((event) => (
                      <div key={event.name} className="flex gap-4">
                        <div className="flex-shrink-0">
                          <div className="h-2 w-2 rounded-full bg-indigo-500 mt-2"></div>
                        </div>
                        <div className="flex-1">
                          <div className="flex justify-between items-start">
                            <p className="text-sm font-medium text-gray-900">{event.event_label || event.event_type}</p>
                            <p className="text-xs text-gray-500">{formatDate(event.event_time)}</p>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{event.summary}</p>
                          <p className="text-xs text-gray-400 mt-1">by {event.actor_type}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {showTimeline && timeline.length === 0 && (
                <p className="mt-4 text-gray-500 text-center py-4">No timeline events yet.</p>
              )}
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

      {/* Handover Status Update Modal */}
      {showHandoverModal && handoverDetails && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Update Recovery Progress</h3>
            <select
              value={newHandoverStatus}
              onChange={(e) => setNewHandoverStatus(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              {handoverDetails.valid_statuses.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700">Note (optional)</label>
              <textarea
                rows={3}
                value={handoverNote}
                onChange={(e) => setHandoverNote(e.target.value)}
                className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border border-gray-300 rounded-md p-2"
                placeholder="Add a note about the handover progress..."
              />
            </div>
            <div className="mt-4 flex justify-end space-x-2">
              <button
                onClick={() => setShowHandoverModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleHandoverStatusUpdate}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
              >
                Update
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reward Status Update Modal */}
      {showRewardModal && rewardStatus && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Update Reward Status</h3>
            <select
              value={newRewardStatus}
              onChange={(e) => setNewRewardStatus(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value="Not Applicable">Not Applicable</option>
              <option value="Offered">Offered</option>
              <option value="Mentioned To Finder">Mentioned To Finder</option>
              <option value="Return Completed">Return Completed</option>
              <option value="Closed Without Reward">Closed Without Reward</option>
              <option value="Cancelled">Cancelled</option>
            </select>
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700">Internal Note (optional)</label>
              <textarea
                rows={3}
                value={rewardInternalNote}
                onChange={(e) => setRewardInternalNote(e.target.value)}
                className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border border-gray-300 rounded-md p-2"
                placeholder="Add an internal note about the reward..."
              />
            </div>
            <div className="mt-4 flex justify-end space-x-2">
              <button
                onClick={() => setShowRewardModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleRewardStatusUpdate}
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

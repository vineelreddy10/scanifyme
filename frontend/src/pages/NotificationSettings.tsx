import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

// Types
export interface NotificationPreferences {
  name: string
  owner_profile: string
  enable_in_app_notifications: boolean
  enable_email_notifications: boolean
  notify_on_new_finder_message: boolean
  notify_on_case_opened: boolean
  notify_on_case_status_change: boolean
  is_default: boolean
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

export const getNotificationPreferences = async (): Promise<{ success: boolean; preferences: NotificationPreferences }> => {
  return await frappeCall<{ success: boolean; preferences: NotificationPreferences }>('scanifyme.notifications.api.notification_api.get_notification_preferences')
}

export const saveNotificationPreferences = async (
  enableInApp: boolean,
  enableEmail: boolean,
  notifyOnNewFinderMessage: boolean,
  notifyOnCaseOpened: boolean,
  notifyOnCaseStatusChange: boolean
): Promise<{ success: boolean; message: string }> => {
  return await frappeCall<{ success: boolean; message: string }>('scanifyme.notifications.api.notification_api.save_notification_preferences', {
    enable_in_app_notifications: enableInApp ? 1 : 0,
    enable_email_notifications: enableEmail ? 1 : 0,
    notify_on_new_finder_message: notifyOnNewFinderMessage ? 1 : 0,
    notify_on_case_opened: notifyOnCaseOpened ? 1 : 0,
    notify_on_case_status_change: notifyOnCaseStatusChange ? 1 : 0,
  })
}

const NotificationSettings = () => {
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  // Form state
  const [enableInApp, setEnableInApp] = useState(true)
  const [enableEmail, setEnableEmail] = useState(true)
  const [notifyOnNewFinderMessage, setNotifyOnNewFinderMessage] = useState(true)
  const [notifyOnCaseOpened, setNotifyOnCaseOpened] = useState(true)
  const [notifyOnCaseStatusChange, setNotifyOnCaseStatusChange] = useState(true)

  const handleLogout = async () => {
    await logout()
    window.location.href = '/login'
  }

  useEffect(() => {
    loadPreferences()
  }, [])

  const loadPreferences = async () => {
    setIsLoading(true)
    try {
      const result = await getNotificationPreferences()
      if (result.success && result.preferences) {
        setPreferences(result.preferences)
        setEnableInApp(result.preferences.enable_in_app_notifications)
        setEnableEmail(result.preferences.enable_email_notifications)
        setNotifyOnNewFinderMessage(result.preferences.notify_on_new_finder_message)
        setNotifyOnCaseOpened(result.preferences.notify_on_case_opened)
        setNotifyOnCaseStatusChange(result.preferences.notify_on_case_status_change)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load notification preferences')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    setMessage('')
    setError('')
    
    try {
      const result = await saveNotificationPreferences(
        enableInApp,
        enableEmail,
        notifyOnNewFinderMessage,
        notifyOnCaseOpened,
        notifyOnCaseStatusChange
      )
      if (result.success) {
        setMessage('Notification preferences saved successfully!')
      } else {
        setError(result.message || 'Failed to save preferences')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to save preferences')
    } finally {
      setIsSaving(false)
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
              <button onClick={() => navigate('/')} className="text-gray-600 hover:text-gray-900">
                ← Back to Dashboard
              </button>
              <h1 className="text-xl font-bold text-gray-900">Notification Settings</h1>
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
          <div className="bg-white shadow rounded-lg">
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">
                Notification Preferences
              </h2>
              <p className="text-sm text-gray-500 mb-6">
                Configure how you want to receive notifications about your recovery cases.
              </p>

              {message && (
                <div className="mb-4 p-3 rounded bg-green-100 text-green-700">
                  {message}
                </div>
              )}

              {error && (
                <div className="mb-4 p-3 rounded bg-red-100 text-red-700">
                  {error}
                </div>
              )}

              <div className="space-y-6">
                {/* Notification Channels */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Notification Channels</h3>
                  <div className="space-y-3">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="enableInApp"
                        checked={enableInApp}
                        onChange={(e) => setEnableInApp(e.target.checked)}
                        className="h-4 w-4 text-indigo-600 border-gray-300 rounded"
                      />
                      <label htmlFor="enableInApp" className="ml-2 block text-sm text-gray-900">
                        In-App Notifications
                      </label>
                      <span className="ml-2 text-xs text-gray-500">(Receive notifications within the app)</span>
                    </div>

                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="enableEmail"
                        checked={enableEmail}
                        onChange={(e) => setEnableEmail(e.target.checked)}
                        className="h-4 w-4 text-indigo-600 border-gray-300 rounded"
                      />
                      <label htmlFor="enableEmail" className="ml-2 block text-sm text-gray-900">
                        Email Notifications
                      </label>
                      <span className="ml-2 text-xs text-gray-500">(Receive notifications via email)</span>
                    </div>
                  </div>
                </div>

                {/* Event Notifications */}
                <div className="border-t border-gray-200 pt-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Event Notifications</h3>
                  <div className="space-y-3">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="notifyOnNewFinderMessage"
                        checked={notifyOnNewFinderMessage}
                        onChange={(e) => setNotifyOnNewFinderMessage(e.target.checked)}
                        className="h-4 w-4 text-indigo-600 border-gray-300 rounded"
                        disabled={!enableInApp && !enableEmail}
                      />
                      <label htmlFor="notifyOnNewFinderMessage" className="ml-2 block text-sm text-gray-900">
                        New Finder Message
                      </label>
                      <span className="ml-2 text-xs text-gray-500">(Get notified when a finder sends you a message)</span>
                    </div>

                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="notifyOnCaseOpened"
                        checked={notifyOnCaseOpened}
                        onChange={(e) => setNotifyOnCaseOpened(e.target.checked)}
                        className="h-4 w-4 text-indigo-600 border-gray-300 rounded"
                        disabled={!enableInApp && !enableEmail}
                      />
                      <label htmlFor="notifyOnCaseOpened" className="ml-2 block text-sm text-gray-900">
                        Case Opened
                      </label>
                      <span className="ml-2 text-xs text-gray-500">(Get notified when a new recovery case is opened)</span>
                    </div>

                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="notifyOnCaseStatusChange"
                        checked={notifyOnCaseStatusChange}
                        onChange={(e) => setNotifyOnCaseStatusChange(e.target.checked)}
                        className="h-4 w-4 text-indigo-600 border-gray-300 rounded"
                        disabled={!enableInApp && !enableEmail}
                      />
                      <label htmlFor="notifyOnCaseStatusChange" className="ml-2 block text-sm text-gray-900">
                        Case Status Changes
                      </label>
                      <span className="ml-2 text-xs text-gray-500">(Get notified when a case status is updated)</span>
                    </div>
                  </div>
                </div>

                <div className="border-t border-gray-200 pt-6">
                  <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {isSaving ? 'Saving...' : 'Save Preferences'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default NotificationSettings

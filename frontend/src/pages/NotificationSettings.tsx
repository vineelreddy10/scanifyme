/**
 * NotificationSettings - User notification preferences page.
 * 
 * Allows users to configure their notification preferences for
 * in-app and email notifications.
 */

import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { AppLayout, PageHeader, Content, Card, ErrorBanner, SuccessBanner, PageLoading } from '../components/ui'

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
  const url = `/api/method/${method}`
  
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
  const { currentUser } = useAuth()
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
      <AppLayout>
        <PageLoading />
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <PageHeader
        title="Notification Settings"
        description="Configure how you want to receive notifications about your recovery cases"
      />
      <Content>
        <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-0.5">
              <svg className="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-medium text-blue-900">Your privacy is protected</h4>
              <p className="text-xs text-blue-700 mt-0.5">
                Notification emails are sent from ScanifyMe on your behalf. Your personal email is never exposed to finders.
              </p>
            </div>
          </div>
        </div>
        <Card>
          <div className="p-6">
            {message && (
              <SuccessBanner message={message} />
            )}

            {error && (
              <ErrorBanner message={error} />
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
                      className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
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
                      className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
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
                      className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
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
                      className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
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
                      className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
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
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                >
                  {isSaving ? 'Saving...' : 'Save Preferences'}
                </button>
              </div>
            </div>
          </div>
        </Card>
      </Content>
    </AppLayout>
  )
}

export default NotificationSettings

import { useState, useEffect, useCallback } from 'react'

// Types
export interface Notification {
  name: string
  title: string | null
  event_type: string
  message_summary: string | null
  priority: string
  is_read: number
  read_on: string | null
  triggered_on: string
  route: string | null
  recovery_case: string | null
  registered_item: string | null
  status: string
}

export interface NotificationCount {
  success: boolean
  count: number
}

export interface NotificationList {
  success: boolean
  notifications: Notification[]
}

export interface MarkReadResult {
  success: boolean
  message: string
}

export interface MarkAllReadResult {
  success: boolean
  message: string
  count: number
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

export const getUnreadNotificationCount = async (): Promise<number> => {
  const result = await frappeCall<NotificationCount>('scanifyme.notifications.api.notification_api.get_unread_notification_count')
  return result.count
}

export const getOwnerNotifications = async (isRead?: number, limit: number = 50): Promise<Notification[]> => {
  const result = await frappeCall<NotificationList>('scanifyme.notifications.api.notification_api.get_owner_notifications', {
    is_read: isRead ?? null,
    limit,
  })
  return result.notifications
}

export const markNotificationRead = async (notificationId: string): Promise<MarkReadResult> => {
  return await frappeCall<MarkReadResult>('scanifyme.notifications.api.notification_api.mark_notification_read', {
    notification_id: notificationId,
  })
}

export const markAllNotificationsRead = async (): Promise<MarkAllReadResult> => {
  return await frappeCall<MarkAllReadResult>('scanifyme.notifications.api.notification_api.mark_all_notifications_read')
}

// Hook
const POLLING_INTERVAL = 30000 // 30 seconds

export function useNotifications(pollingEnabled: boolean = true) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState<number>(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadNotifications = useCallback(async () => {
    try {
      const [notificationsData, countData] = await Promise.all([
        getOwnerNotifications(undefined, 50),
        getUnreadNotificationCount(),
      ])
      setNotifications(notificationsData)
      setUnreadCount(countData)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load notifications:', err)
      setError(err.message || 'Failed to load notifications')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const refresh = useCallback(async () => {
    try {
      const [notificationsData, countData] = await Promise.all([
        getOwnerNotifications(undefined, 50),
        getUnreadNotificationCount(),
      ])
      setNotifications(notificationsData)
      setUnreadCount(countData)
      setError(null)
    } catch (err: any) {
      console.error('Failed to refresh notifications:', err)
    }
  }, [])

  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      await markNotificationRead(notificationId)
      // Update local state
      setNotifications(prev => 
        prev.map(n => 
          n.name === notificationId 
            ? { ...n, is_read: 1, read_on: new Date().toISOString() }
            : n
        )
      )
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (err: any) {
      console.error('Failed to mark notification as read:', err)
      throw err
    }
  }, [])

  const markAllAsRead = useCallback(async () => {
    try {
      const result = await markAllNotificationsRead()
      // Update local state
      setNotifications(prev => 
        prev.map(n => ({ ...n, is_read: 1, read_on: new Date().toISOString() }))
      )
      setUnreadCount(0)
      return result
    } catch (err: any) {
      console.error('Failed to mark all notifications as read:', err)
      throw err
    }
  }, [])

  // Initial load
  useEffect(() => {
    loadNotifications()
  }, [loadNotifications])

  // Polling
  useEffect(() => {
    if (!pollingEnabled) return

    const intervalId = setInterval(() => {
      refresh()
    }, POLLING_INTERVAL)

    return () => clearInterval(intervalId)
  }, [pollingEnabled, refresh])

  return {
    notifications,
    unreadCount,
    isLoading,
    error,
    refresh,
    markAsRead,
    markAllAsRead,
  }
}

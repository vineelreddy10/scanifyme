import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useNotifications, Notification } from '../hooks/useNotifications'
import NotificationBell from '../components/NotificationBell'

// Types
interface NotificationItemProps {
  notification: Notification
  onMarkRead: (id: string) => void
  onNavigate: (notification: Notification) => void
}

const NotificationItem = ({ notification, onMarkRead, onNavigate }: NotificationItemProps) => {
  const getPriorityBadge = (priority: string) => {
    const styles: Record<string, string> = {
      'High': 'bg-red-100 text-red-800',
      'Normal': 'bg-blue-100 text-blue-800',
      'Low': 'bg-gray-100 text-gray-800',
    }
    return styles[priority] || styles['Normal']
  }

  const getEventTypeBadge = (eventType: string) => {
    const styles: Record<string, string> = {
      'Finder Message Received': 'bg-yellow-100 text-yellow-800',
      'Recovery Case Opened': 'bg-purple-100 text-purple-800',
      'Case Status Updated': 'bg-indigo-100 text-indigo-800',
      'Owner Reply Sent': 'bg-green-100 text-green-800',
      'Item Marked Recovered': 'bg-teal-100 text-teal-800',
    }
    return styles[eventType] || 'bg-gray-100 text-gray-800'
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    })
  }

  const handleClick = () => {
    if (!notification.is_read) {
      onMarkRead(notification.name)
    }
    onNavigate(notification)
  }

  return (
    <div
      className={`p-4 border-b border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors ${
        !notification.is_read ? 'bg-blue-50' : ''
      }`}
      onClick={handleClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            {!notification.is_read && (
              <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0"></span>
            )}
            <p className={`text-sm font-medium truncate ${!notification.is_read ? 'text-gray-900' : 'text-gray-700'}`}>
              {notification.title || notification.event_type}
            </p>
          </div>
          {notification.message_summary && (
            <p className="text-sm text-gray-600 truncate mb-2">
              {notification.message_summary}
            </p>
          )}
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`px-2 py-0.5 text-xs rounded-full ${getEventTypeBadge(notification.event_type)}`}>
              {notification.event_type}
            </span>
            <span className={`px-2 py-0.5 text-xs rounded-full ${getPriorityBadge(notification.priority)}`}>
              {notification.priority}
            </span>
            <span className="text-xs text-gray-500">
              {formatDate(notification.triggered_on)}
            </span>
          </div>
        </div>
        <div className="ml-4 flex-shrink-0">
          <svg
            className="h-5 w-5 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </div>
  )
}

const NotificationsPage = () => {
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()
  const { notifications, unreadCount, isLoading, error, refresh, markAsRead, markAllAsRead } = useNotifications(true)
  const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all')
  const [isMarkingAll, setIsMarkingAll] = useState(false)

  const handleLogout = async () => {
    await logout()
    window.location.href = '/login'
  }

  const handleMarkRead = async (notificationId: string) => {
    try {
      await markAsRead(notificationId)
    } catch (err) {
      console.error('Failed to mark as read:', err)
    }
  }

  const handleMarkAllRead = async () => {
    setIsMarkingAll(true)
    try {
      await markAllAsRead()
    } catch (err) {
      console.error('Failed to mark all as read:', err)
    } finally {
      setIsMarkingAll(false)
    }
  }

  const handleNavigate = (notification: Notification) => {
    if (notification.route) {
      // Remove the /frontend prefix if present (since we're already in /frontend)
      const route = notification.route.replace(/^\/frontend/, '')
      navigate(route)
    } else if (notification.recovery_case) {
      navigate(`/recovery/${notification.recovery_case}`)
    } else if (notification.registered_item) {
      navigate(`/items/${notification.registered_item}`)
    } else {
      navigate('/recovery')
    }
  }

  const filteredNotifications = notifications.filter(n => {
    if (filter === 'unread') return !n.is_read
    if (filter === 'read') return n.is_read
    return true
  })

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
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Notifications</h2>
              <p className="text-sm text-gray-600 mt-1">
                {unreadCount > 0 ? `You have ${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}` : 'You are all caught up!'}
              </p>
            </div>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                disabled={isMarkingAll}
                className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isMarkingAll ? 'Marking...' : 'Mark all as read'}
              </button>
            )}
          </div>

          <div className="mb-4 flex gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                filter === 'all'
                  ? 'bg-gray-900 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('unread')}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                filter === 'unread'
                  ? 'bg-gray-900 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
              }`}
            >
              Unread
            </button>
            <button
              onClick={() => setFilter('read')}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                filter === 'read'
                  ? 'bg-gray-900 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
              }`}
            >
              Read
            </button>
          </div>

          {isLoading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-800">{error}</p>
              <button
                onClick={refresh}
                className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                Try again
              </button>
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div className="bg-white shadow rounded-lg p-6">
              <div className="text-center">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                <p className="mt-2 text-gray-500">
                  {filter === 'all' 
                    ? 'No notifications yet' 
                    : filter === 'unread' 
                      ? 'No unread notifications' 
                      : 'No read notifications'}
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {filteredNotifications.map((notification) => (
                  <li key={notification.name}>
                    <NotificationItem
                      notification={notification}
                      onMarkRead={handleMarkRead}
                      onNavigate={handleNavigate}
                    />
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

export default NotificationsPage

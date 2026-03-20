import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useNotifications, Notification } from '../hooks/useNotifications'
import { AppLayout, PageHeader } from '../components/ui/AppLayout'
import { EventTypeBadge, PriorityBadge } from '../components/ui/StatusBadge'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { ListItemSkeleton } from '../components/ui/LoadingSpinner'
import EmptyState from '../components/EmptyState'

interface NotificationItemProps {
  notification: Notification
  onMarkRead: (id: string) => void
  onNavigate: (notification: Notification) => void
}

const NotificationItem = ({ notification, onMarkRead, onNavigate }: NotificationItemProps) => {
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
            <EventTypeBadge eventType={notification.event_type} />
            <PriorityBadge priority={notification.priority} />
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
  const navigate = useNavigate()
  const { notifications, unreadCount, isLoading, error, refresh, markAsRead, markAllAsRead } = useNotifications(true)
  const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all')
  const [isMarkingAll, setIsMarkingAll] = useState(false)

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
      return <ErrorBanner message={error} onRetry={refresh} />
    }

    if (filteredNotifications.length === 0) {
      return (
        <EmptyState
          icon="bell"
          title={filter === 'all' ? "You're all caught up!" : filter === 'unread' ? "No unread notifications" : "No read notifications"}
          description={filter === 'all' ? "You're all caught up! Notifications will appear here when someone contacts you about your items." : undefined}
          action={filter !== 'all' ? {
            label: 'View All Notifications',
            onClick: () => setFilter('all'),
            variant: 'secondary',
          } : undefined}
        />
      )
    }

    return (
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
    )
  }

  return (
    <AppLayout>
      <PageHeader
        title="Notifications"
        description={unreadCount > 0 ? `You have ${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}` : 'You are all caught up!'}
        actions={
          unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              disabled={isMarkingAll}
              className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isMarkingAll ? 'Marking...' : 'Mark all as read'}
            </button>
          )
        }
      />

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

      {renderContent()}
    </AppLayout>
  )
}

export default NotificationsPage

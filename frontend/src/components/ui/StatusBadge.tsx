/**
 * StatusBadge - Consistent status badge styling across the application.
 */

export type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple'

interface StatusBadgeProps {
  children: React.ReactNode
  variant?: BadgeVariant
  size?: 'sm' | 'md'
  className?: string
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-gray-100 text-gray-800',
  success: 'bg-green-100 text-green-800',
  warning: 'bg-yellow-100 text-yellow-800',
  danger: 'bg-red-100 text-red-800',
  info: 'bg-blue-100 text-blue-800',
  purple: 'bg-purple-100 text-purple-800',
}

const sizeStyles = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
}

export function StatusBadge({ children, variant = 'default', size = 'sm', className = '' }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center font-medium rounded-full ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  )
}

// Case status badges with predefined mappings
export function CaseStatusBadge({ status }: { status: string }) {
  const variantMap: Record<string, BadgeVariant> = {
    'Open': 'warning',
    'Owner Responded': 'info',
    'Return Planned': 'purple',
    'Recovered': 'success',
    'Closed': 'default',
    'Invalid': 'danger',
    'Spam': 'danger',
  }
  
  return (
    <StatusBadge variant={variantMap[status] || 'default'}>
      {status}
    </StatusBadge>
  )
}

// Item status badges
export function ItemStatusBadge({ status }: { status: string }) {
  const variantMap: Record<string, BadgeVariant> = {
    'Draft': 'default',
    'Active': 'success',
    'Lost': 'danger',
    'Recovered': 'info',
    'Archived': 'warning',
  }
  
  return (
    <StatusBadge variant={variantMap[status] || 'default'}>
      {status}
    </StatusBadge>
  )
}

// Notification priority badges
export function PriorityBadge({ priority }: { priority: string }) {
  const variantMap: Record<string, BadgeVariant> = {
    'High': 'danger',
    'Normal': 'info',
    'Low': 'default',
  }
  
  return (
    <StatusBadge variant={variantMap[priority] || 'default'}>
      {priority}
    </StatusBadge>
  )
}

// Notification event type badges
export function EventTypeBadge({ eventType }: { eventType: string }) {
  const variantMap: Record<string, BadgeVariant> = {
    'Finder Message Received': 'warning',
    'Recovery Case Opened': 'purple',
    'Case Status Updated': 'info',
    'Owner Reply Sent': 'success',
    'Item Marked Recovered': 'success',
  }
  
  return (
    <StatusBadge variant={variantMap[eventType] || 'default'}>
      {eventType}
    </StatusBadge>
  )
}

// QR status badges
export function QRStatusBadge({ status }: { status: string }) {
  const variantMap: Record<string, BadgeVariant> = {
    'Generated': 'default',
    'Printed': 'info',
    'In Stock': 'success',
    'Assigned': 'purple',
    'Activated': 'success',
    'Suspended': 'warning',
    'Retired': 'default',
    'Valid': 'success',
    'Invalid': 'danger',
  }
  
  return (
    <StatusBadge variant={variantMap[status] || 'default'}>
      {status}
    </StatusBadge>
  )
}

export default StatusBadge

/**
 * Navigation Configuration
 * 
 * Defines the grouped hierarchical menu structure for the product shell.
 * Supports role-based visibility filtering.
 */

// Re-export role types from canonical source
export type { UserRole } from '../types/roles'
import { UserRole, getUserRole } from '../types/roles'
export { getUserRole }

export interface NavItem {
  label: string
  path: string
  icon?: string
  badge?: string | number
}

export interface NavGroup {
  id: string
  title: string
  icon?: string
  items: NavItem[]
}

export interface NavigationConfig {
  groups: NavGroup[]
}

/**
 * Navigation configuration for different user roles.
 */
export function getNavigationConfig(role: UserRole): NavigationConfig {
  const groups: NavGroup[] = []

  // Home group - visible to all authenticated users
  groups.push({
    id: 'home',
    title: 'Home',
    items: [
      { label: 'Dashboard', path: '/' },
    ],
  })

  // Owner group - visible to owners and admins
  if (role === 'owner' || role === 'admin') {
    groups.push({
      id: 'owner',
      title: 'My Items',
      icon: 'box',
      items: [
        { label: 'My Items', path: '/items' },
        { label: 'Activate QR', path: '/activate-qr' },
        { label: 'Recovery Cases', path: '/recovery' },
        { label: 'Notifications', path: '/notifications' },
      ],
    })
  }

  // Masters group - visible based on role
  if (role === 'admin' || role === 'operations' || role === 'owner') {
    const mastersItems: NavItem[] = []
    
    // All roles can see Item Categories
    if (role === 'owner' || role === 'admin') {
      mastersItems.push({ label: 'Item Categories', path: '/list/Item Category' })
    }
    
    // Admin only masters
    if (role === 'admin') {
      mastersItems.push({ label: 'QR Code Batches', path: '/list/QR Batch' })
      mastersItems.push({ label: 'QR Code Tags', path: '/list/QR Code Tag' })
      mastersItems.push({ label: 'Owner Profiles', path: '/list/Owner Profile' })
    }
    
    // Operations only masters
    if (role === 'operations') {
      mastersItems.push({ label: 'QR Code Batches', path: '/list/QR Batch' })
    }
    
    if (mastersItems.length > 0) {
      groups.push({
        id: 'masters',
        title: 'Masters',
        icon: 'database',
        items: mastersItems,
      })
    }
  }

  // Settings group - visible to all authenticated users
  groups.push({
    id: 'settings',
    title: 'Settings',
    icon: 'cog',
    items: [
      { label: 'Notification Settings', path: '/settings/notifications' },
    ],
  })

  return { groups }
}

/**
 * Get icon path for a given icon name.
 */
export function getIconPath(icon: string): string {
  const icons: Record<string, string> = {
    'home': 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
    'box': 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4',
    'qrcode': 'M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z',
    'bell': 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9',
    'database': 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4',
    'cog': 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
    'chart': 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
    'user': 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    'logout': 'M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1',
  }
  
  return icons[icon] || icons['box']
}

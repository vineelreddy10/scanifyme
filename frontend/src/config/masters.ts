/**
 * Masters Configuration
 * 
 * Defines master data types accessible from the Masters menu.
 * Each master has:
 * - doctype: The Frappe DocType name
 * - label: Display label
 * - description: Brief description
 * - icon: Icon identifier
 * - roles: Which roles can access this master
 * - features: What operations are allowed
 */

export type MasterAccessRole = 'admin' | 'owner' | 'operations' | 'all'

export type MasterFeature = 'list' | 'create' | 'edit' | 'delete' | 'view'

export interface MasterDefinition {
  /** DocType name in Frappe */
  doctype: string
  
  /** Display label in the UI */
  label: string
  
  /** Brief description for the card */
  description: string
  
  /** Icon name (from heroicons or similar) */
  icon: 'cog' | 'tag' | 'bell' | 'qrcode' | 'user' | 'collection' | 'folder' | 'document'
  
  /** Which roles can access this master */
  roles: MasterAccessRole[]
  
  /** Which features are allowed */
  features: MasterFeature[]
  
  /** Whether this is a top-level master or sub-master */
  category?: 'configuration' | 'reference' | 'admin'
}

export interface MastersSection {
  title: string
  masters: MasterDefinition[]
}

/**
 * All masters available in the application.
 * This config drives both the Masters landing page and sidebar menu.
 */
export const MASTERS_CONFIG: MasterDefinition[] = [
  {
    doctype: 'Item Category',
    label: 'Item Categories',
    description: 'Organize and categorize your items for better management',
    icon: 'tag',
    roles: 'all',
    features: ['list', 'create', 'edit', 'delete'],
    category: 'reference',
  },
  {
    doctype: 'Notification Preference',
    label: 'Notification Preferences',
    description: 'Configure how and when you receive notifications',
    icon: 'bell',
    roles: 'owner',
    features: ['list', 'edit'],
    category: 'configuration',
  },
  {
    doctype: 'QR Batch',
    label: 'QR Code Batches',
    description: 'View and manage QR code batch assignments',
    icon: 'qrcode',
    roles: 'admin',
    features: ['list', 'view'],
    category: 'admin',
  },
  {
    doctype: 'QR Code Tag',
    label: 'QR Code Tags',
    description: 'Individual QR code tags and their status',
    icon: 'qrcode',
    roles: 'admin',
    features: ['list', 'view'],
    category: 'admin',
  },
  {
    doctype: 'Owner Profile',
    label: 'Owner Profiles',
    description: 'Manage owner account profiles',
    icon: 'user',
    roles: 'admin',
    features: ['list', 'view'],
    category: 'admin',
  },
]

/**
 * Group masters by category for display.
 */
export function getMastersByCategory(role: MasterAccessRole): MastersSection[] {
  const sections: Record<string, MasterDefinition[]> = {
    'configuration': [],
    'reference': [],
    'admin': [],
  }
  
  for (const master of MASTERS_CONFIG) {
    // Filter by role
    if (!canAccessMaster(master, role)) {
      continue
    }
    
    const category = master.category || 'reference'
    if (!sections[category]) {
      sections[category] = []
    }
    sections[category].push(master)
  }
  
  return [
    { title: 'Configuration', masters: sections['configuration'] },
    { title: 'Reference Data', masters: sections['reference'] },
    { title: 'Administration', masters: sections['admin'] },
  ].filter(section => section.masters.length > 0)
}

/**
 * Check if a role can access a master.
 */
export function canAccessMaster(master: MasterDefinition, role: MasterAccessRole): boolean {
  if (master.roles === 'all') return true
  if (master.roles === role) return true
  return false
}

/**
 * Get icon component name for a master.
 */
export function getMasterIcon(icon: MasterDefinition['icon']): string {
  const icons: Record<MasterDefinition['icon'], string> = {
    'cog': 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
    'tag': 'M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z',
    'bell': 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9',
    'qrcode': 'M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z',
    'user': 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    'collection': 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
    'folder': 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z',
    'document': 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
  }
  
  return icons[icon] || icons['document']
}

/**
 * Get the user's role based on their user type.
 * This should be fetched from the auth context or API.
 */
export type UserRole = 'admin' | 'owner' | 'operations' | 'guest'

/**
 * Map Frappe user types to application roles.
 * This is a simplified mapping - in production, you'd fetch this from the API.
 */
export function getUserRoleFromUserType(userType: string | null): UserRole {
  if (!userType) return 'guest'
  
  const userTypeLower = userType.toLowerCase()
  
  if (userTypeLower.includes('admin') || userTypeLower.includes('system')) {
    return 'admin'
  }
  
  if (userTypeLower.includes('operations')) {
    return 'operations'
  }
  
  if (userTypeLower.includes('owner')) {
    return 'owner'
  }
  
  return 'owner' // Default for authenticated users
}

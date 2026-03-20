/**
 * Sidebar Component
 * 
 * Persistent left sidebar with grouped hierarchical navigation.
 * Supports collapsible groups and active route highlighting.
 */

import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import type { NavGroup, NavItem } from '../../config/navigation'
import { getIconPath } from '../../config/navigation'

interface SidebarProps {
  groups: NavGroup[]
  unreadCount?: number
}

export function Sidebar({ groups, unreadCount = 0 }: SidebarProps) {
  const navigate = useNavigate()
  const location = useLocation()

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(path)
  }

  return (
    <nav className="flex flex-col h-full">
      {/* Logo/Brand */}
      <div className="flex-shrink-0 px-4 py-5 border-b border-gray-200">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-3 w-full focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded-lg p-1 -ml-1"
        >
          <div className="h-9 w-9 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center shadow-sm">
            <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
            </svg>
          </div>
          <span className="text-lg font-bold text-gray-900">ScanifyMe</span>
        </button>
      </div>

      {/* Navigation Groups */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {groups.map((group) => (
          <NavGroupComponent
            key={group.id}
            group={group}
            isActive={isActive}
            onNavigate={(path) => navigate(path)}
            unreadCount={unreadCount}
          />
        ))}
      </div>
    </nav>
  )
}

interface NavGroupComponentProps {
  group: NavGroup
  isActive: (path: string) => boolean
  onNavigate: (path: string) => void
  unreadCount?: number
}

function NavGroupComponent({ group, isActive, onNavigate, unreadCount }: NavGroupComponentProps) {
  const [isExpanded, setIsExpanded] = useState(() => {
    return group.items.some(item => isActive(item.path))
  })

  const hasActiveChild = group.items.some(item => isActive(item.path))

  return (
    <div className="space-y-1">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full px-3 py-2 text-sm font-medium text-gray-600 rounded-lg hover:bg-gray-100 hover:text-gray-900 transition-colors"
      >
        <div className="flex items-center gap-3">
          {group.icon && (
            <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={getIconPath(group.icon)} />
            </svg>
          )}
          <span>{group.title}</span>
        </div>
        <svg
          className={`h-4 w-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isExpanded && (
        <div className="space-y-0.5 ml-2 pl-2 border-l border-gray-200">
          {group.items.map((item) => (
            <NavItemComponent
              key={item.path}
              item={item}
              isActive={isActive(item.path)}
              onClick={() => onNavigate(item.path)}
              showBadge={item.label === 'Notifications' && unreadCount > 0}
              badgeCount={unreadCount}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface NavItemComponentProps {
  item: NavItem
  isActive: boolean
  onClick: () => void
  showBadge?: boolean
  badgeCount?: number
}

function NavItemComponent({ item, isActive, onClick, showBadge, badgeCount }: NavItemComponentProps) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center justify-between w-full px-3 py-2 text-sm rounded-lg transition-colors ${
        isActive
          ? 'bg-indigo-50 text-indigo-700 font-medium'
          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
      }`}
    >
      <span>{item.label}</span>
      {showBadge && badgeCount !== undefined && badgeCount > 0 && (
        <span className="inline-flex items-center justify-center h-5 min-w-[20px] px-1.5 text-xs font-medium bg-red-500 text-white rounded-full">
          {badgeCount > 99 ? '99+' : badgeCount}
        </span>
      )}
    </button>
  )
}

export default Sidebar

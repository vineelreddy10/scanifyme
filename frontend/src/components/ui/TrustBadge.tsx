/**
 * TrustBadge - Privacy, visibility, and trust indicator components
 * 
 * Reusable components for communicating privacy, visibility settings,
 * and trust cues across owner-facing pages.
 */

import React from 'react'

// ============================================================
// PrivacyBadge
// ============================================================

interface PrivacyBadgeProps {
  visibility: 'Public' | 'Private' | 'Hidden' | 'Visible to Finder' | 'Only Visible to You'
  size?: 'sm' | 'md'
}

export function PrivacyBadge({ visibility, size = 'md' }: PrivacyBadgeProps) {
  const sizeClasses = size === 'sm' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-1 text-xs'

  const variants: Record<string, string> = {
    'Public': 'bg-green-100 text-green-700',
    'Visible to Finder': 'bg-green-100 text-green-700',
    'Private': 'bg-blue-100 text-blue-700',
    'Only Visible to You': 'bg-blue-100 text-blue-700',
    'Hidden': 'bg-gray-100 text-gray-600',
  }

  return (
    <span className={`inline-flex items-center rounded-full font-medium ${sizeClasses} ${variants[visibility] || 'bg-gray-100 text-gray-600'}`}>
      {visibility === 'Public' || visibility === 'Visible to Finder' ? (
        <svg className={`${size === 'sm' ? 'h-2.5 w-2.5 mr-1' : 'h-3 w-3 mr-1.5'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
      ) : (
        <svg className={`${size === 'sm' ? 'h-2.5 w-2.5 mr-1' : 'h-3 w-3 mr-1.5'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      )}
      {visibility}
    </span>
  )
}

// ============================================================
// RewardVisibilityBadge
// ============================================================

interface RewardVisibilityBadgeProps {
  visibility: string
  hasReward: boolean
  size?: 'sm' | 'md'
}

export function RewardVisibilityBadge({ visibility, hasReward, size = 'md' }: RewardVisibilityBadgeProps) {
  const sizeClasses = size === 'sm' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-1 text-xs'

  if (!hasReward || visibility === 'Disabled') {
    return (
      <span className={`inline-flex items-center rounded-full font-medium ${sizeClasses} bg-gray-100 text-gray-600`}>
        <svg className={`${size === 'sm' ? 'h-2.5 w-2.5 mr-1' : 'h-3 w-3 mr-1.5'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
        </svg>
        No Reward
      </span>
    )
  }

  if (visibility === 'Public') {
    return (
      <span className={`inline-flex items-center rounded-full font-medium ${sizeClasses} bg-green-100 text-green-700`}>
        <svg className={`${size === 'sm' ? 'h-2.5 w-2.5 mr-1' : 'h-3 w-3 mr-1.5'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
        Reward Visible
      </span>
    )
  }

  if (visibility === 'Private Mention On Contact') {
    return (
      <span className={`inline-flex items-center rounded-full font-medium ${sizeClasses} bg-blue-100 text-blue-700`}>
        <svg className={`${size === 'sm' ? 'h-2.5 w-2.5 mr-1' : 'h-3 w-3 mr-1.5'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
        </svg>
        Reward on Contact
      </span>
    )
  }

  return (
    <span className={`inline-flex items-center rounded-full font-medium ${sizeClasses} bg-gray-100 text-gray-600`}>
      Hidden
    </span>
  )
}

// ============================================================
// TrustInfoCard
// ============================================================

interface TrustInfoCardProps {
  children: React.ReactNode
  variant?: 'privacy' | 'safety' | 'info'
  title?: string
  className?: string
}

export function TrustInfoCard({ children, variant = 'info', title, className = '' }: TrustInfoCardProps) {
  const variants = {
    privacy: {
      border: 'border-l-blue-500',
      bg: 'bg-blue-50',
      icon: (
        <svg className="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      ),
      iconBg: 'bg-blue-100',
    },
    safety: {
      border: 'border-l-green-500',
      bg: 'bg-green-50',
      icon: (
        <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      iconBg: 'bg-green-100',
    },
    info: {
      border: 'border-l-gray-400',
      bg: 'bg-gray-50',
      icon: (
        <svg className="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      iconBg: 'bg-gray-200',
    },
  }

  const v = variants[variant]

  return (
    <div className={`bg-white rounded-lg border border-gray-200 border-l-4 ${v.border} p-4 ${className}`}>
      {title && (
        <div className="flex items-center gap-2 mb-2">
          <div className={`flex-shrink-0 h-8 w-8 ${v.iconBg} rounded-lg flex items-center justify-center`}>
            {v.icon}
          </div>
          <h4 className="text-sm font-semibold text-gray-900">{title}</h4>
        </div>
      )}
      <div className={`${v.bg} rounded-md p-3`}>
        {children}
      </div>
    </div>
  )
}

// ============================================================
// VisibilityHint
// ============================================================

interface VisibilityHintProps {
  fieldName: string
  visibility: string
  className?: string
}

const visibilityExplanations: Record<string, string> = {
  'Public': 'Anyone who scans this QR can see this',
  'Visible to Finder': 'Only shown after the finder contacts you',
  'Only Visible to You': 'Only you can see this information',
  'Private': 'Only you can see this information',
  'Hidden': 'Not shown anywhere',
  'Disabled': 'Not shown anywhere',
}

export function VisibilityHint({ fieldName, visibility, className = '' }: VisibilityHintProps) {
  const explanation = visibilityExplanations[visibility] || 'Visibility setting applied'

  return (
    <span className={`text-xs text-gray-500 ${className}`}>
      <span className="font-medium">{fieldName}</span> is{' '}
      <span className="font-medium text-gray-700">{visibility}</span>{' '}
      <span className="text-gray-400">— {explanation}</span>
    </span>
  )
}

// ============================================================
// PublicPageFooter
// ============================================================

interface PublicPageFooterProps {
  message?: string
}

export function PublicPageFooter({ message }: PublicPageFooterProps) {
  return (
    <div className="flex items-center justify-center gap-2 py-6 text-gray-400">
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
      <span className="text-sm">{message || 'Secured by ScanifyMe'}</span>
    </div>
  )
}

// ============================================================
// PrivacyOverviewTable
// ============================================================

interface PrivacyField {
  field: string
  visibility: 'Public' | 'Private' | 'Hidden' | 'Visible to Finder' | 'Only Visible to You'
}

interface PrivacyOverviewTableProps {
  fields: PrivacyField[]
  className?: string
}

export function PrivacyOverviewTable({ fields, className = '' }: PrivacyOverviewTableProps) {
  return (
    <div className={`space-y-2 ${className}`}>
      {fields.map((f) => (
        <div key={f.field} className="flex items-center justify-between py-1">
          <span className="text-sm text-gray-600">{f.field}</span>
          <PrivacyBadge visibility={f.visibility} size="sm" />
        </div>
      ))}
    </div>
  )
}

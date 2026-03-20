/**
 * MastersPage - Landing page for the Masters section.
 * 
 * Displays master data types organized by category.
 * Each card links to the generic list view for that DocType.
 */

import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { AppLayout, PageHeader, Content } from '../components/ui'
import { 
  MASTERS_CONFIG, 
  MasterDefinition, 
  MastersSection,
  getMastersByCategory,
  getUserRoleFromUserType,
} from '../config/masters'

interface MastersPageProps {
  /** Optional header content */
  headerContent?: React.ReactNode
}

export default function MastersPage({ headerContent }: MastersPageProps) {
  const navigate = useNavigate()
  const { currentUser } = useAuth()

  // Determine user role based on current user
  // In production, this would be fetched from the API
  const userRole = currentUser?.includes('Administrator') 
    ? 'admin' as const 
    : 'owner' as const

  // Get masters accessible to this role
  const sections = getMastersByCategory(userRole)

  // Navigate to master's list page
  const handleMasterClick = (master: MasterDefinition) => {
    navigate(`/list/${encodeURIComponent(master.doctype)}`)
  }

  return (
    <AppLayout>
      <PageHeader
        title="Masters"
        description="Manage your master data and configurations"
        actions={headerContent}
      />
      <Content>
        {sections.length === 0 ? (
          <EmptyState
            title="No Masters Available"
            description="You don't have access to any master data sections."
          />
        ) : (
          <div className="space-y-8">
            {sections.map((section) => (
              <MastersSection 
                key={section.title} 
                section={section} 
                onMasterClick={handleMasterClick}
              />
            ))}
          </div>
        )}
      </Content>
    </AppLayout>
  )
}

// Masters Section Component
interface MastersSectionProps {
  section: MastersSection
  onMasterClick: (master: MasterDefinition) => void
}

function MastersSection({ section, onMasterClick }: MastersSectionProps) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        {section.title}
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {section.masters.map((master) => (
          <MasterCard 
            key={master.doctype} 
            master={master} 
            onClick={() => onMasterClick(master)}
          />
        ))}
      </div>
    </div>
  )
}

// Master Card Component
interface MasterCardProps {
  master: MasterDefinition
  onClick: () => void
}

function MasterCard({ master, onClick }: MasterCardProps) {
  const featureLabels: Record<string, string> = {
    'list': 'View list',
    'create': 'Create new',
    'edit': 'Edit entries',
    'delete': 'Delete entries',
    'view': 'View only',
  }

  return (
    <button
      onClick={onClick}
      className="bg-white rounded-lg border border-gray-200 p-5 text-left hover:border-indigo-300 hover:shadow-md transition-all duration-200 w-full focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
    >
      <div className="flex items-start justify-between">
        <div className="flex-shrink-0">
          <div className="h-10 w-10 bg-indigo-100 rounded-lg flex items-center justify-center">
            <MasterIcon icon={master.icon} />
          </div>
        </div>
        <div className="ml-4 flex-1">
          <h3 className="text-base font-medium text-gray-900">
            {master.label}
          </h3>
          <p className="mt-1 text-sm text-gray-500 line-clamp-2">
            {master.description}
          </p>
          <div className="mt-3 flex flex-wrap gap-1">
            {master.features.map((feature) => (
              <span 
                key={feature}
                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600"
              >
                {featureLabels[feature] || feature}
              </span>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-4 flex items-center text-indigo-600 text-sm font-medium">
        <span>View {master.label}</span>
        <svg 
          className="ml-1 h-4 w-4" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M9 5l7 7-7 7" 
          />
        </svg>
      </div>
    </button>
  )
}

// Master Icon Component
function MasterIcon({ icon }: { icon: MasterDefinition['icon'] }) {
  const paths: Record<MasterDefinition['icon'], string> = {
    'cog': 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
    'tag': 'M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z',
    'bell': 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9',
    'qrcode': 'M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z',
    'user': 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    'collection': 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
    'folder': 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z',
    'document': 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
  }

  return (
    <svg 
      className="h-5 w-5 text-indigo-600" 
      fill="none" 
      stroke="currentColor" 
      viewBox="0 0 24 24"
    >
      <path 
        strokeLinecap="round" 
        strokeLinejoin="round" 
        strokeWidth={2} 
        d={paths[icon] || paths['document']} 
      />
    </svg>
  )
}

// Empty State Component
function EmptyState({ 
  title, 
  description 
}: { 
  title: string
  description: string 
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
      <svg 
        className="mx-auto h-12 w-12 text-gray-400" 
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" 
        />
      </svg>
      <h3 className="mt-4 text-lg font-medium text-gray-900">{title}</h3>
      <p className="mt-2 text-sm text-gray-500">{description}</p>
    </div>
  )
}

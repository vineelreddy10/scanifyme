import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppLayout, PageHeader } from '../components/ui/AppLayout'
import { CaseStatusBadge, StatusBadge } from '../components/ui/StatusBadge'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { PageLoading } from '../components/ui/LoadingSpinner'
import { ChecklistWidget } from '../components/ChecklistWidget'
import {
  getOwnerDashboardSummary,
  getOwnerRecentActivity,
  getOwnerOnboardingState,
  getOwnerNextActions,
  type OwnerDashboardSummary,
  type OwnerRecentActivity,
  type OnboardingState,
  type OnboardingAction,
} from '../api/frappe'

const Dashboard = () => {
  const navigate = useNavigate()
  const [summary, setSummary] = useState<OwnerDashboardSummary | null>(null)
  const [activity, setActivity] = useState<OwnerRecentActivity | null>(null)
  const [onboarding, setOnboarding] = useState<OnboardingState | null>(null)
  const [nextActions, setNextActions] = useState<OnboardingAction[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboard()
  }, [])

  useEffect(() => {
    getOwnerOnboardingState()
      .then(state => {
        setOnboarding(state)
        return getOwnerNextActions()
      })
      .then(actions => setNextActions(actions))
      .catch(() => { /* Owner may not have profile yet */ })
  }, [])

  const loadDashboard = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [summaryData, activityData] = await Promise.all([
        getOwnerDashboardSummary(),
        getOwnerRecentActivity(5),
      ])
      setSummary(summaryData)
      setActivity(activityData)
    } catch (err: any) {
      console.error('Failed to load dashboard:', err)
      setError(err?.message || 'Failed to load dashboard data')
    } finally {
      setIsLoading(false)
    }
  }

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return '—'
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
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
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
        title="My Dashboard"
        description="Overview of your items, recoveries, and activity"
      />

      {error && (
        <div className="mb-6">
          <ErrorBanner message={error} onRetry={loadDashboard} />
        </div>
      )}

      {summary && (
        <>
          {/* Onboarding Checklist Widget */}
          {(!onboarding?.onboarding_completed) && nextActions.length > 0 && (
            <div className="mb-8">
              <ChecklistWidget
                title="Setup Progress"
                completionPercent={onboarding?.completion_percent ?? 0}
                actions={nextActions}
              />
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            <div className="bg-white overflow-hidden shadow rounded-xl border">
              <div className="p-5">
                <h3 className="text-sm font-medium text-gray-500">Total Items</h3>
                <p className="mt-2 text-3xl font-bold text-indigo-600">{summary.items.total ?? 0}</p>
                <p className="text-xs text-gray-400 mt-1">
                  {summary.items.active ?? 0} active, {summary.items.lost ?? 0} lost, {summary.items.recovered ?? 0} recovered
                </p>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-xl border">
              <div className="p-5">
                <h3 className="text-sm font-medium text-gray-500">Recovery Cases</h3>
                <p className="mt-2 text-3xl font-bold text-purple-600">{summary.recovery_cases.total ?? 0}</p>
                <p className="text-xs text-gray-400 mt-1">
                  {summary.recovery_cases.active_workflow ?? 0} active, {summary.recovery_cases.recovered ?? 0} recovered
                </p>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-xl border">
              <div className="p-5">
                <h3 className="text-sm font-medium text-gray-500">Open Cases</h3>
                <p className="mt-2 text-3xl font-bold text-yellow-600">{summary.recovery_cases.open ?? 0}</p>
                <p className="text-xs text-gray-400 mt-1">
                  {summary.recovery_cases.responded ?? 0} responded, {summary.recovery_cases.return_planned ?? 0} planned
                </p>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-xl border">
              <div className="p-5">
                <h3 className="text-sm font-medium text-gray-500">Unread Notifications</h3>
                <p className="mt-2 text-3xl font-bold text-blue-600">{summary.notifications.unread ?? 0}</p>
                <p className="text-xs text-gray-400 mt-1">In-app alerts</p>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-xl border">
              <div className="p-5">
                <h3 className="text-sm font-medium text-gray-500">Reward Items</h3>
                <p className="mt-2 text-3xl font-bold text-green-600">{summary.rewards.enabled_items ?? 0}</p>
                <p className="text-xs text-gray-400 mt-1">With rewards enabled</p>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-xl border">
              <div className="p-5">
                <h3 className="text-sm font-medium text-gray-500">Activated QR</h3>
                <p className="mt-2 text-3xl font-bold text-emerald-600">{summary.qr_tags.activated ?? 0}</p>
                <p className="text-xs text-gray-400 mt-1">Tags in use</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div className="bg-white shadow rounded-xl border">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">Recent Recovery Cases</h2>
                  <button
                    onClick={() => navigate('/recovery')}
                    className="text-sm text-indigo-600 hover:text-indigo-800"
                  >
                    View All
                  </button>
                </div>
                {(!activity?.recent_cases || activity.recent_cases.length === 0) ? (
                  <p className="text-gray-500 text-sm">No recovery cases yet.</p>
                ) : (
                  <div className="space-y-3">
                    {activity.recent_cases.map((c) => (
                      <button
                        key={c.name}
                        onClick={() => navigate(`/recovery/${c.name}`)}
                        className="w-full text-left p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <p className="font-medium text-gray-900 text-sm truncate flex-1 mr-2">
                            {c.case_title || '—'}
                          </p>
                          <CaseStatusBadge status={c.status || 'Open'} />
                        </div>
                        <div className="flex items-center justify-between mt-1">
                          <p className="text-xs text-gray-500">
                            {c.finder_name || 'Anonymous'} · {formatDate(c.last_activity_on)}
                          </p>
                          <p className="text-xs text-gray-400">{c.handover_status || '—'}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="bg-white shadow rounded-xl border">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">Recent Notifications</h2>
                  <button
                    onClick={() => navigate('/notifications')}
                    className="text-sm text-indigo-600 hover:text-indigo-800"
                  >
                    View All
                  </button>
                </div>
                {(!activity?.recent_notifications || activity.recent_notifications.length === 0) ? (
                  <p className="text-gray-500 text-sm">No notifications yet.</p>
                ) : (
                  <div className="space-y-3">
                    {activity.recent_notifications.map((n) => (
                      <button
                        key={n.name}
                        onClick={() => {
                          if (n.route) {
                            const route = n.route.replace(/^\/frontend/, '')
                            navigate(route)
                          } else if (n.recovery_case) {
                            navigate(`/recovery/${n.recovery_case}`)
                          } else {
                            navigate('/notifications')
                          }
                        }}
                        className={`w-full text-left p-3 rounded-lg transition-colors ${
                          n.is_read ? 'bg-gray-50 hover:bg-gray-100' : 'bg-blue-50 hover:bg-blue-100'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              {!n.is_read && (
                                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full flex-shrink-0" />
                              )}
                              <p className={`text-sm font-medium truncate ${n.is_read ? 'text-gray-700' : 'text-gray-900'}`}>
                                {n.title || n.event_type || '—'}
                              </p>
                            </div>
                            <p className="text-xs text-gray-500 mt-0.5 truncate">{formatDate(n.triggered_on)}</p>
                          </div>
                          <div className="flex flex-col items-end gap-1 ml-2">
                            <StatusBadge variant="default">
                              {n.event_type ? n.event_type.split(' ').slice(0, 2).join(' ') : '—'}
                            </StatusBadge>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {activity?.recent_scans && activity.recent_scans.length > 0 && (
            <div className="bg-white shadow rounded-xl border mb-8">
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Scans</h2>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="text-left text-gray-500 border-b">
                        <th className="pb-2 font-medium">Token</th>
                        <th className="pb-2 font-medium">Status</th>
                        <th className="pb-2 font-medium">Scanned At</th>
                        <th className="pb-2 font-medium">Case</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {activity.recent_scans.map((s) => (
                        <tr key={s.name} className="hover:bg-gray-50">
                          <td className="py-2 font-mono text-xs text-gray-700">{s.token || '—'}</td>
                          <td className="py-2">
                            <StatusBadge 
                              variant={s.status === 'Valid' ? 'success' : s.status === 'Invalid' ? 'danger' : 'default'}
                            >
                              {s.status || '—'}
                            </StatusBadge>
                          </td>
                          <td className="py-2 text-gray-500">{formatDate(s.scanned_on)}</td>
                          <td className="py-2 text-gray-500">{s.recovery_case ? 'Yes' : '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      <div className="bg-white shadow rounded-xl border">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <button
              onClick={() => navigate('/activate-qr')}
              className="flex items-center justify-center p-4 bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 transition-colors text-sm font-medium"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h2M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
              </svg>
              Activate QR Code
            </button>
            <button
              onClick={() => navigate('/items')}
              className="flex items-center justify-center p-4 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors text-sm font-medium"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
              View Items
            </button>
            <button
              onClick={() => navigate('/recovery')}
              className="flex items-center justify-center p-4 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 transition-colors text-sm font-medium"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
              Recovery Cases
            </button>
            <button
              onClick={() => navigate('/notifications')}
              className="flex items-center justify-center p-4 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              Notifications
            </button>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}

export default Dashboard

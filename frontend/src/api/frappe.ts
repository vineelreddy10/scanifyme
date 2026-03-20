import { FrappeContext } from 'frappe-react-sdk'
import { useContext } from 'react'

export const useFrappe = () => {
  const context = useContext(FrappeContext)
  if (!context) {
    throw new Error('useFrappe must be used within FrappeProvider')
  }
  return context
}

export interface CurrentUser {
  email: string
  first_name: string
  last_name: string
  full_name: string
  user_image: string | null
  username: string
}

export interface ScanifyMeSettings {
  name: string
  site_name: string
  default_privacy_level: 'High' | 'Medium' | 'Low'
  allow_anonymous_messages: boolean
  allow_location_sharing: boolean
  default_reward_message: string
  max_messages_per_hour: number
  max_scans_per_minute: number
}

export interface QRBatch {
  name: string
  batch_name: string
  batch_prefix: string | null
  batch_size: number
  status: 'Draft' | 'Generated' | 'Printed' | 'Distributed' | 'Closed'
  created_by: string
  created_on: string
}

export interface QRCodeTag {
  name: string
  qr_uid: string
  qr_token: string
  qr_url: string
  batch: string
  status: 'Generated' | 'Printed' | 'In Stock' | 'Assigned' | 'Activated' | 'Suspended' | 'Retired'
  registered_item: string | null
  created_on: string
}

export interface CreateQRBatchParams {
  batch_name: string
  batch_size: number
  batch_prefix?: string
}

export interface RegisteredItem {
  name: string
  item_name: string
  status: 'Draft' | 'Active' | 'Lost' | 'Recovered' | 'Archived'
  public_label: string | null
  activation_date: string | null
  last_scan_at: string | null
  item_category: string | null
  item_category_name?: string | null
  qr_code_tag: string | null
  qr_uid?: string | null
}

export interface ItemDetails {
  id: string
  item_name: string
  status: string
  public_label: string | null
  recovery_note: string | null
  reward_note: string | null
  reward_enabled?: boolean
  reward_amount_text?: string | null
  reward_visibility?: string | null
  activation_date: string | null
  last_scan_at: string | null
  item_category: string | null
  item_category_name: string | null
  qr_code: {
    uid: string
    status: string
  } | null
  photos: {
    image: string
    visibility: string
    caption: string | null
  }[]
}

export interface ItemCategory {
  name: string
  category_name: string
  category_code: string
  description: string | null
  icon: string | null
}

export interface ActivateQRResult {
  success: boolean
  message: string
  qr_tag: {
    name: string
    qr_uid: string
    qr_token?: string
    status: string
  }
  needs_item_creation: boolean
  linked_item?: string
  linked_item_name?: string
}

export interface CreateItemParams {
  item_name: string
  qr_code_tag: string
  item_category?: string
  public_label?: string
  recovery_note?: string
  reward_note?: string
  photos?: Array<{
    image: string
    visibility: string
    caption?: string
  }>
}

async function frappeCall<T>(method: string, args: Record<string, unknown> = {}): Promise<T> {
  // Use same-origin API calls - empty string means relative to current host
  // Only use VITE_FRAPPE_URL if it's a valid non-empty absolute URL
  const baseURL = (typeof import.meta.env.VITE_FRAPPE_URL === 'string' && 
                   import.meta.env.VITE_FRAPPE_URL && 
                   import.meta.env.VITE_FRAPPE_URL !== '/')
    ? import.meta.env.VITE_FRAPPE_URL 
    : ''
  const url = baseURL ? `${baseURL}/api/method/${method}` : `/api/method/${method}`
  
  // Get CSRF token from window (set by Frappe during page load)
  const csrfToken = typeof window !== 'undefined' ? (window as any).csrf_token : ''
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  
  // Add CSRF token if available
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

export const getCurrentUser = async (): Promise<CurrentUser | null> => {
  try {
    return await frappeCall<CurrentUser>('scanifyme.api.get_user_role')
  } catch (e) {
    return null
  }
}

export const createQRBatch = async (params: CreateQRBatchParams): Promise<string> => {
  return await frappeCall<string>('scanifyme.qr_management.api.qr_api.create_qr_batch', {
    batch_name: params.batch_name,
    batch_size: params.batch_size,
    batch_prefix: params.batch_prefix || null,
  })
}

export const getQRBatches = async (limit = 20): Promise<QRBatch[]> => {
  return await frappeCall<QRBatch[]>('scanifyme.qr_management.api.qr_api.get_qr_batches', {
    limit,
  })
}

export const getQRTags = async (batch?: string, status?: string, limit = 20): Promise<QRCodeTag[]> => {
  return await frappeCall<QRCodeTag[]>('scanifyme.qr_management.api.qr_api.get_qr_tags', {
    batch: batch || null,
    status: status || null,
    limit,
  })
}

export const activateQR = async (token: string): Promise<ActivateQRResult> => {
  return await frappeCall<ActivateQRResult>('scanifyme.items.api.items_api.activate_qr', {
    token,
  })
}

export const createItem = async (params: CreateItemParams): Promise<string> => {
  return await frappeCall<string>('scanifyme.items.api.items_api.create_item', {
    item_name: params.item_name,
    qr_code_tag: params.qr_code_tag,
    item_category: params.item_category || null,
    public_label: params.public_label || null,
    recovery_note: params.recovery_note || null,
    reward_note: params.reward_note || null,
    photos: params.photos ? JSON.stringify(params.photos) : null,
  })
}

export const getUserItems = async (status?: string, limit = 20): Promise<RegisteredItem[]> => {
  return await frappeCall<RegisteredItem[]>('scanifyme.items.api.items_api.get_user_items', {
    status: status || null,
    limit,
  })
}

export const getItemDetails = async (item: string): Promise<ItemDetails | null> => {
  return await frappeCall<ItemDetails | null>('scanifyme.items.api.items_api.get_item_details', {
    item,
  })
}

export const updateItemStatus = async (item: string, status: string): Promise<{ success: boolean; message: string }> => {
  return await frappeCall<{ success: boolean; message: string }>('scanifyme.items.api.items_api.update_item_status', {
    item,
    status,
  })
}

export const getItemCategories = async (): Promise<ItemCategory[]> => {
  return await frappeCall<ItemCategory[]>('scanifyme.items.api.items_api.get_item_categories')
}

export interface RewardSettings {
  item: string
  reward_enabled: boolean
  reward_amount_text: string | null
  reward_note: string | null
  reward_terms: string | null
  reward_visibility: string | null
}

export interface RewardStatus {
  case: string
  reward_offered: boolean
  reward_display_text: string | null
  reward_status: string | null
  reward_internal_note: string | null
  reward_last_updated_on: string | null
}

export const getItemRewardSettings = async (item: string): Promise<RewardSettings> => {
  return await frappeCall<RewardSettings>('scanifyme.items.api.items_api.get_item_reward_settings', {
    item,
  })
}

export const updateItemRewardSettings = async (
  item: string,
  rewardEnabled: boolean,
  rewardAmountText?: string | null,
  rewardNote?: string | null,
  rewardTerms?: string | null,
  rewardVisibility: string = 'Public'
): Promise<{ success: boolean; message: string }> => {
  return await frappeCall<{ success: boolean; message: string }>(
    'scanifyme.items.api.items_api.update_item_reward_settings',
    {
      item,
      reward_enabled: rewardEnabled,
      reward_amount_text: rewardAmountText || null,
      reward_note: rewardNote || null,
      reward_terms: rewardTerms || null,
      reward_visibility: rewardVisibility,
    }
  )
}

export const getCaseRewardStatus = async (caseId: string): Promise<RewardStatus> => {
  return await frappeCall<RewardStatus>('scanifyme.recovery.api.recovery_api.get_case_reward_status', {
    case_id: caseId,
  })
}

export const updateRecoveryCaseRewardStatus = async (
  caseId: string,
  rewardStatus: string,
  rewardInternalNote?: string | null
): Promise<{ success: boolean; message: string }> => {
  return await frappeCall<{ success: boolean; message: string }>(
    'scanifyme.recovery.api.recovery_api.update_recovery_case_reward_status',
    {
      case_id: caseId,
      reward_status: rewardStatus,
      reward_internal_note: rewardInternalNote || null,
    }
  )
}

// ===== Dashboard / Analytics Types =====

export interface OwnerDashboardSummary {
  items: {
    total: number
    active: number
    lost: number
    recovered: number
    draft: number
  }
  recovery_cases: {
    total: number
    open: number
    responded: number
    return_planned: number
    recovered: number
    closed: number
    active_workflow: number
  }
  qr_tags: {
    activated: number
  }
  rewards: {
    enabled_items: number
  }
  notifications: {
    unread: number
  }
}

export interface OwnerRecentActivity {
  recent_cases: Array<{
    name: string
    case_title: string
    status: string
    opened_on: string | null
    last_activity_on: string | null
    finder_name: string | null
    handover_status: string | null
  }>
  recent_notifications: Array<{
    name: string
    title: string | null
    event_type: string
    is_read: number
    triggered_on: string
    route: string | null
    recovery_case: string | null
  }>
  recent_scans: Array<{
    name: string
    token: string
    scanned_on: string | null
    status: string
    registered_item: string | null
    recovery_case: string | null
  }>
  recent_locations: Array<{
    name: string
    recovery_case: string
    latitude: number | null
    longitude: number | null
    shared_on: string | null
    note: string | null
  }>
}

export interface AdminOperationalSummary {
  qr_batches: {
    total: number
    by_status: Record<string, number>
  }
  qr_tags: {
    total: number
    by_status: Record<string, number>
  }
  registered_items: {
    total: number
    by_status: Record<string, number>
  }
  recovery_cases: {
    total: number
    by_status: Record<string, number>
    active_workflow: number
  }
  scans: {
    total: number
    valid: number
    invalid: number
    recovery_initiated: number
  }
  notifications: {
    total: number
    unread: number
    by_channel: Record<string, number>
    by_status: Record<string, number>
  }
  location_shares: {
    total: number
  }
  handover: {
    by_status: Record<string, number>
  }
  rewards: {
    enabled_items: number
    cases_with_rewards: number
  }
  owner_profiles: {
    total: number
  }
  finder_sessions: {
    active: number
    expired: number
  }
}

// ===== Dashboard API Functions =====

export const getOwnerDashboardSummary = async (): Promise<OwnerDashboardSummary> => {
  return await frappeCall<OwnerDashboardSummary>(
    'scanifyme.reports.api.dashboard_api.get_owner_dashboard_summary'
  )
}

export const getOwnerRecentActivity = async (limit: number = 10): Promise<OwnerRecentActivity> => {
  return await frappeCall<OwnerRecentActivity>(
    'scanifyme.reports.api.dashboard_api.get_owner_recent_activity',
    { limit }
  )
}

export const getAdminOperationalSummary = async (): Promise<AdminOperationalSummary> => {
  return await frappeCall<AdminOperationalSummary>(
    'scanifyme.reports.api.dashboard_api.get_admin_operational_summary'
  )
}
// ===== Onboarding Types =====

export interface OnboardingState {
  owner_profile: string
  account_created: boolean
  profile_completed: boolean
  qr_activated: boolean
  item_registered: boolean
  recovery_note_added: boolean
  notifications_configured: boolean
  reward_reviewed: boolean
  onboarding_completed: boolean
  completion_percent: number
  last_updated_on: string | null
}

export interface OnboardingAction {
  action_key: string
  title: string
  description: string
  route: string
  priority: number
}

export interface RecoveryReadiness {
  item: string
  item_name: string
  is_ready: boolean
  readiness_percent: number
  checks: Array<{
    check_key: string
    label: string
    passed: boolean
    message: string
  }>
  missing: string[]
  next_action: {
    action_key: string
    title: string
    description: string
    route: string
  } | null
}

// ===== Onboarding API Functions =====

export const getOwnerOnboardingState = async (): Promise<OnboardingState> => {
  return await frappeCall<OnboardingState>(
    'scanifyme.onboarding.api.onboarding_api.get_owner_onboarding_state'
  )
}

export const recomputeOnboardingState = async (): Promise<OnboardingState> => {
  return await frappeCall<OnboardingState>(
    'scanifyme.onboarding.api.onboarding_api.recompute_onboarding_state'
  )
}

export const getOwnerNextActions = async (): Promise<OnboardingAction[]> => {
  return await frappeCall<OnboardingAction[]>(
    'scanifyme.onboarding.api.onboarding_api.get_owner_next_actions'
  )
}

export const getItemRecoveryReadiness = async (item: string): Promise<RecoveryReadiness> => {
  return await frappeCall<RecoveryReadiness>(
    'scanifyme.onboarding.api.onboarding_api.get_item_recovery_readiness',
    { item }
  )
}

// ===== Admin Onboarding APIs =====

export interface OnboardingOverview {
  total_owners: number
  completed: number
  in_progress: number
  avg_completion_percent: number
  breakdown: {
    not_started: number
    getting_started: number
    halfway: number
    almost_done: number
  }
}

export interface IncompleteOwnerSummary {
  owner_profile: string
  completion_percent: number
  onboarding_completed: boolean
  missing_steps: string[]
  last_updated_on: string | null
}

export const getOnboardingOverview = async (): Promise<OnboardingOverview> => {
  return await frappeCall<OnboardingOverview>(
    'scanifyme.onboarding.api.admin_onboarding_api.get_onboarding_overview'
  )
}

export const getIncompleteOnboardingSummary = async (
  minCompletion?: number,
  maxCompletion?: number,
  limit: number = 50
): Promise<IncompleteOwnerSummary[]> => {
  return await frappeCall<IncompleteOwnerSummary[]>(
    'scanifyme.onboarding.api.admin_onboarding_api.get_incomplete_onboarding_summary',
    {
      min_completion: minCompletion ?? null,
      max_completion: maxCompletion ?? null,
      limit,
    }
  )
}

// ===== Activation Error Types =====

export interface ActivationError {
  error_code: 'INVALID_TOKEN' | 'ALREADY_ACTIVATED' | 'SUSPENDED_TAG' | 'RETIRED_TAG' | 'INVALID_STATUS' | 'UNKNOWN'
  user_title: string
  user_message: string
  user_action: string
}

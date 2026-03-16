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
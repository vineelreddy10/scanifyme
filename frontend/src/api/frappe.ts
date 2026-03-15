import { FrappeContext, getRequestURL } from 'frappe-react-sdk'
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

async function frappeCall<T>(method: string, args: Record<string, unknown> = {}): Promise<T> {
  const url = getRequestURL('api/method/' + method)
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
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

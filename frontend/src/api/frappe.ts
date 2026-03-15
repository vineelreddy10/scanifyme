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

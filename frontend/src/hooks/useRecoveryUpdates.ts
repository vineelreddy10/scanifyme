import { useState, useEffect, useCallback, useRef } from 'react'

interface UseRecoveryUpdatesOptions {
  caseId?: string
  pollInterval?: number
  enabled?: boolean
}

interface RecoveryUpdate {
  cases?: unknown[]
  messages?: unknown[]
  lastUpdated: Date
}

export function useRecoveryUpdates(options: UseRecoveryUpdatesOptions = {}) {
  const { caseId, pollInterval = 30000, enabled = true } = options
  
  const [update, setUpdate] = useState<RecoveryUpdate | null>(null)
  const [isPolling, setIsPolling] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  
  const fetchUpdates = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()
    
    try {
      const url = caseId 
        ? `/api/method/scanifyme.recovery.api.recovery_api.get_recovery_case_messages`
        : `/api/method/scanifyme.recovery.api.recovery_api.get_owner_recovery_cases`
      
      const csrfToken = typeof window !== 'undefined' ? (window as any).csrf_token : ''
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(csrfToken ? { 'X-Frappe-CSRF-Token': csrfToken } : {}),
        },
        body: JSON.stringify(caseId ? { case_id: caseId } : {}),
        credentials: 'include',
        signal: abortControllerRef.current.signal,
      })
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.statusText}`)
      }
      
      const data = await response.json()
      
      setUpdate({
        cases: caseId ? undefined : data.message,
        messages: caseId ? data.message : undefined,
        lastUpdated: new Date(),
      })
      setError(null)
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== 'AbortError') {
        console.warn('Polling fetch failed:', err.message)
        setError(err.message)
      }
    }
  }, [caseId])
  
  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsPolling(false)
  }, [])
  
  const startPolling = useCallback(() => {
    if (intervalRef.current) return
    
    setIsPolling(true)
    fetchUpdates()
    
    intervalRef.current = setInterval(() => {
      fetchUpdates()
    }, pollInterval)
  }, [fetchUpdates, pollInterval])
  
  useEffect(() => {
    if (!enabled) {
      stopPolling()
      return
    }
    
    startPolling()
    
    return () => {
      stopPolling()
    }
  }, [enabled, startPolling, stopPolling])
  
  return {
    update,
    isPolling,
    isRealtimeAvailable,
    error,
    refresh: fetchUpdates,
    stopPolling,
    startPolling,
  }
}

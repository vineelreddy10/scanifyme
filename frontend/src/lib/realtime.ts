/**
 * Realtime Configuration
 * 
 * Controls socket.io connection for real-time updates.
 * Default: DISABLED - pages work via standard API polling.
 * 
 * To enable realtime:
 * 1. Set VITE_USE_REALTIME=true in .env.local
 * 2. Ensure socket server is running on configured port
 * 3. Rebuild the frontend: cd frontend && yarn build
 */

export interface RealtimeConfig {
  enabled: boolean
  port: number | undefined
  reconnectAttempts: number
  reconnectDelay: number
}

export const REALTIME_CONFIG: RealtimeConfig = {
  enabled: import.meta.env.VITE_USE_REALTIME === 'true',
  port: (() => {
    if (import.meta.env.VITE_USE_REALTIME === 'true') {
      return parseInt(import.meta.env.VITE_SOCKET_PORT || '9000', 10)
    }
    return undefined
  })(),
  reconnectAttempts: 3,
  reconnectDelay: 1000,
}

export function isRealtimeEnabled(): boolean {
  return REALTIME_CONFIG.enabled && REALTIME_CONFIG.port !== undefined
}

export function getRealtimePort(): number | undefined {
  return REALTIME_CONFIG.port
}

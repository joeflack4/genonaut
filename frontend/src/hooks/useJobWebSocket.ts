import { useState, useEffect, useRef, useCallback } from 'react'

export interface JobStatusUpdate {
  job_id: number
  status: 'started' | 'processing' | 'completed' | 'failed'
  progress?: number
  content_id?: number
  output_paths?: string[]
  error?: string
  timestamp?: string
}

export interface UseJobWebSocketOptions {
  onStatusUpdate?: (update: JobStatusUpdate) => void
  onError?: (error: Event) => void
  autoReconnect?: boolean
  reconnectDelay?: number
  maxReconnectAttempts?: number
}

/**
 * Hook for connecting to WebSocket job status updates.
 *
 * @example
 * const { connect, disconnect, status } = useJobWebSocket(jobId, {
 *   onStatusUpdate: (update) => console.log('Job update:', update),
 *   autoReconnect: true
 * });
 *
 * useEffect(() => {
 *   connect();
 *   return () => disconnect();
 * }, [connect, disconnect]);
 */
export function useJobWebSocket(
  jobId: number | null,
  options: UseJobWebSocketOptions = {}
) {
  const {
    onStatusUpdate,
    onError,
    autoReconnect = true,
    reconnectDelay = 3000,
    maxReconnectAttempts = 5
  } = options

  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const [lastUpdate, setLastUpdate] = useState<JobStatusUpdate | null>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const [reconnectLimitReached, setReconnectLimitReached] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const shouldConnectRef = useRef(false)
  const reconnectAttemptsRef = useRef(0)
  const closedIntentionallyRef = useRef(false)

  const disconnect = useCallback(() => {
    shouldConnectRef.current = false
    closedIntentionallyRef.current = true

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      const ws = wsRef.current
      wsRef.current = null

      // Remove event handlers before closing to reduce console noise
      // This is especially helpful in React Strict Mode where effects run twice
      ws.onopen = null
      ws.onmessage = null
      ws.onerror = null
      ws.onclose = null

      // Close the connection if it's open or connecting
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close()
      }
    }

    setConnectionStatus('disconnected')
    reconnectAttemptsRef.current = 0
    setReconnectAttempts(0)
    setReconnectLimitReached(false)
  }, [])

  const connect = useCallback(() => {
    if (!jobId) return

    // Don't create a new connection if one is already open or connecting
    const currentState = wsRef.current?.readyState
    if (currentState === WebSocket.OPEN || currentState === WebSocket.CONNECTING) {
      return
    }

    shouldConnectRef.current = true
    closedIntentionallyRef.current = false
    setConnectionStatus('connecting')

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host.replace(':5173', ':8001') // Replace Vite dev port with API port
    const wsUrl = `${protocol}//${host}/ws/jobs/${jobId}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log(`WebSocket connected for job ${jobId}`)
      setConnectionStatus('connected')
      reconnectAttemptsRef.current = 0
      setReconnectAttempts(0)
      setReconnectLimitReached(false)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as JobStatusUpdate

        // Ignore connection confirmation messages
        if ('type' in data && (data.type === 'connection' || data.type === 'ping' || data.type === 'pong')) {
          return
        }

        if (typeof data.status !== 'string') {
          return
        }

        console.log('Job status update:', data)
        setLastUpdate(data)

        if (onStatusUpdate) {
          onStatusUpdate(data)
        }

        // Auto-disconnect on terminal statuses and prevent reconnection
        if (data.status === 'completed' || data.status === 'failed') {
          shouldConnectRef.current = false // Prevent auto-reconnect
          setTimeout(() => disconnect(), 1000)
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    }

    ws.onerror = (event) => {
      // Suppress errors if we intentionally closed the connection
      if (closedIntentionallyRef.current) {
        return
      }

      console.error('WebSocket error:', event)
      setConnectionStatus('error')

      if (onError) {
        onError(event)
      }
    }

    ws.onclose = () => {
      // Suppress logs if we intentionally closed the connection
      if (!closedIntentionallyRef.current) {
        console.log(`WebSocket disconnected for job ${jobId}`)
      }

      setConnectionStatus('disconnected')
      wsRef.current = null

      // Auto-reconnect if enabled and we should still be connected (not intentionally closed)
      if (autoReconnect && shouldConnectRef.current && !closedIntentionallyRef.current) {
        const attempts = reconnectAttemptsRef.current + 1
        reconnectAttemptsRef.current = attempts
        setReconnectAttempts(attempts)

        if (maxReconnectAttempts < 0 || attempts <= maxReconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Reconnecting WebSocket for job ${jobId} (attempt ${attempts})...`)
            connect()
          }, reconnectDelay)
        } else {
          console.warn(`WebSocket reconnect limit reached for job ${jobId}; falling back to polling only.`)
          setReconnectLimitReached(true)
        }
      }
    }
  }, [jobId, onStatusUpdate, onError, autoReconnect, reconnectDelay, maxReconnectAttempts, disconnect])

  // Ping/pong to keep connection alive
  useEffect(() => {
    if (connectionStatus !== 'connected' || !wsRef.current) return

    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000) // Ping every 30 seconds

    return () => clearInterval(pingInterval)
  }, [connectionStatus])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    connect,
    disconnect,
    status: connectionStatus,
    lastUpdate,
    isConnected: connectionStatus === 'connected',
    reconnectAttempts,
    reconnectLimitReached
  }
}

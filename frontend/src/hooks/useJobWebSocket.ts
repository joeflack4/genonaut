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
    reconnectDelay = 3000
  } = options

  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const [lastUpdate, setLastUpdate] = useState<JobStatusUpdate | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const shouldConnectRef = useRef(false)

  const disconnect = useCallback(() => {
    shouldConnectRef.current = false

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setConnectionStatus('disconnected')
  }, [])

  const connect = useCallback(() => {
    if (!jobId) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    shouldConnectRef.current = true
    setConnectionStatus('connecting')

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host.replace(':5173', ':8001') // Replace Vite dev port with API port
    const wsUrl = `${protocol}//${host}/ws/jobs/${jobId}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log(`WebSocket connected for job ${jobId}`)
      setConnectionStatus('connected')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as JobStatusUpdate

        // Ignore connection confirmation messages
        if ('type' in data && data.type === 'connection') {
          return
        }

        console.log('Job status update:', data)
        setLastUpdate(data)

        if (onStatusUpdate) {
          onStatusUpdate(data)
        }

        // Auto-disconnect on terminal statuses
        if (data.status === 'completed' || data.status === 'failed') {
          setTimeout(() => disconnect(), 1000)
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    }

    ws.onerror = (event) => {
      console.error('WebSocket error:', event)
      setConnectionStatus('error')

      if (onError) {
        onError(event)
      }
    }

    ws.onclose = () => {
      console.log(`WebSocket disconnected for job ${jobId}`)
      setConnectionStatus('disconnected')
      wsRef.current = null

      // Auto-reconnect if enabled and we should still be connected
      if (autoReconnect && shouldConnectRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log(`Reconnecting WebSocket for job ${jobId}...`)
          connect()
        }, reconnectDelay)
      }
    }
  }, [jobId, onStatusUpdate, onError, autoReconnect, reconnectDelay, disconnect])

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
    isConnected: connectionStatus === 'connected'
  }
}

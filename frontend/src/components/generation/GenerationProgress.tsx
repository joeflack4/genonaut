import { useState, useEffect, useRef, useCallback } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  LinearProgress,
  Button,
  Alert,
  Chip,
  Stack,
  Paper,
  CircularProgress,
  Card,
  CardMedia,
  CardActionArea,
} from '@mui/material'
import {
  Cancel as CancelIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as HourglassIcon,
} from '@mui/icons-material'
import { useJobWebSocket, type JobStatusUpdate } from '../../hooks/useJobWebSocket'
import { useGenerationJobService } from '../../hooks/useGenerationJobService'
import type { GenerationJobResponse } from '../../services/generation-job-service'
import type { ComfyUIGenerationResponse } from '../../services/comfyui-service'
import { getImageUrl } from '../../utils/image-url'
import { ApiError } from '../../services/api-client'
import { debugLog } from '../../utils/debug'

type TerminalStatus = 'completed' | 'failed' | 'cancelled'

type GenerationRun = GenerationJobResponse | ComfyUIGenerationResponse

type NormalizedStatus = 'pending' | 'started' | 'running' | 'processing' | TerminalStatus

type NormalizedGeneration = GenerationRun & { status: NormalizedStatus }

const normalizeStatus = (status: GenerationRun['status']): NormalizedStatus => {
  if (typeof status !== 'string') {
    return 'pending'
  }

  const value = status.toLowerCase()

  if (value === 'cancelled' || value === 'canceled') {
    return 'cancelled'
  }

  if (value === 'failed' || value === 'error') {
    return 'failed'
  }

  if (value === 'completed' || value === 'success' || value === 'succeeded') {
    return 'completed'
  }

  if (value === 'processing') {
    return 'processing'
  }

  if (value === 'running' || value === 'in_progress') {
    return 'running'
  }

  if (value === 'started' || value === 'starting') {
    return 'started'
  }

  // Treat queue states as pending
  if (value === 'pending' || value === 'queued' || value === 'queue' || value === 'waiting') {
    return 'pending'
  }

  return 'pending'
}

const normalizeGeneration = (generation: GenerationRun): NormalizedGeneration => ({
  ...generation,
  status: normalizeStatus(generation.status),
})

const arraysMatch = (left: unknown[] | undefined, right: unknown[] | undefined) => {
  if (!left && !right) return true
  if (!left || !right) return false
  if (left.length !== right.length) return false
  return left.every((value, index) => value === right[index])
}

const isTerminal = (status: NormalizedStatus): status is TerminalStatus => (
  status === 'completed' || status === 'failed' || status === 'cancelled'
)

const hasMeaningfulChange = (prev: NormalizedGeneration | null, next: NormalizedGeneration) => {
  if (!prev) {
    debugLog.generation('[hasMeaningfulChange] No previous generation, accepting update')
    return true
  }

  const changes = {
    status: prev.status !== next.status,
    content_id: prev.content_id !== next.content_id,
    error_message: prev.error_message !== next.error_message,
    updated_at: prev.updated_at !== next.updated_at,
    completed_at: prev.completed_at !== next.completed_at,
    started_at: prev.started_at !== next.started_at,
    output_paths: !arraysMatch(prev.output_paths, next.output_paths),
    thumbnail_paths: !arraysMatch(prev.thumbnail_paths, next.thumbnail_paths),
  }

  const hasChange = Object.values(changes).some(Boolean)

  if (hasChange) {
    debugLog.generation('[hasMeaningfulChange] Changes detected:', {
      changes,
      prev: { id: prev.id, status: prev.status, updated_at: prev.updated_at },
      next: { id: next.id, status: next.status, updated_at: next.updated_at },
    })
  }

  return hasChange
}

interface GenerationProgressProps {
  generation: GenerationRun
  onStatusFinalized?: (status: TerminalStatus, generation: GenerationRun) => void
  onGenerationUpdate?: (generation: GenerationRun) => void
  onClear?: () => void
}

const STATUS_CONFIG = {
  pending: {
    label: 'Pending',
    color: 'default' as const,
    icon: <HourglassIcon />,
  },
  started: {
    label: 'In Progress',
    color: 'primary' as const,
    icon: <CircularProgress size={16} />,
  },
  running: {
    label: 'Running',
    color: 'primary' as const,
    icon: <CircularProgress size={16} />,
  },
  processing: {
    label: 'Processing',
    color: 'primary' as const,
    icon: <CircularProgress size={16} />,
  },
  completed: {
    label: 'Completed',
    color: 'success' as const,
    icon: <CheckCircleIcon />,
  },
  failed: {
    label: 'Failed',
    color: 'error' as const,
    icon: <ErrorIcon />,
  },
  cancelled: {
    label: 'Cancelled',
    color: 'secondary' as const,
    icon: <CancelIcon />,
  },
}

export function GenerationProgress({ generation: initialGeneration, onStatusFinalized, onGenerationUpdate, onClear }: GenerationProgressProps) {
  const [isCancelling, setIsCancelling] = useState(false)
  const [currentGeneration, setCurrentGeneration] = useState<NormalizedGeneration>(normalizeGeneration(initialGeneration))
  const lastBroadcastRef = useRef<NormalizedGeneration | null>(null)
  const initialGenerationRef = useRef(initialGeneration)
  const navigate = useNavigate()
  const location = useLocation()

  const { cancelGenerationJob, getGenerationJob } = useGenerationJobService()

  // Keep ref updated
  useEffect(() => {
    initialGenerationRef.current = initialGeneration
  }, [initialGeneration])

  // Stable status update callback to prevent unnecessary WebSocket reconnections
  const handleStatusUpdate = useCallback((update: JobStatusUpdate) => {
    debugLog.generation('WebSocket update received:', update)
    // Update current generation with WebSocket data
    setCurrentGeneration(prev => {
      if (!prev) {
        return normalizeGeneration({
          ...initialGenerationRef.current,
          status: update.status,
          ...(update.content_id && { content_id: update.content_id }),
          ...(update.output_paths && { output_paths: update.output_paths }),
          ...(update.error && { error_message: update.error }),
        })
      }

      const nextGeneration = normalizeGeneration({
        ...prev,
        status: update.status,
        ...(update.content_id && { content_id: update.content_id }),
        ...(update.output_paths && { output_paths: update.output_paths }),
        ...(update.error && { error_message: update.error }),
      })

      if (isTerminal(prev.status) && !isTerminal(nextGeneration.status)) {
        debugLog.generationDebug('[GenerationProgress] Ignoring websocket downgrade', {
          previousStatus: prev.status,
          incomingStatus: nextGeneration.status,
        })
        return prev
      }

      debugLog.generationDebug('[GenerationProgress] Applying websocket update', {
        previousStatus: prev.status,
        nextStatus: nextGeneration.status,
      })
      return nextGeneration
    })
  }, [])

  // Use WebSocket for real-time updates
  const {
    connect,
    disconnect,
    lastUpdate,
    status: socketStatus,
    reconnectLimitReached,
  } = useJobWebSocket(initialGeneration.id, {
    onStatusUpdate: handleStatusUpdate
  })

  // Reset local state when a new generation id is supplied OR when parent provides fresher data
  useEffect(() => {
    debugLog.generation('[Effect:PropSync] Parent prop changed', {
      id: initialGeneration.id,
      status: initialGeneration.status,
      updated_at: initialGeneration.updated_at,
    })

    setCurrentGeneration(prev => {
      const next = normalizeGeneration(initialGeneration)

      // If different job ID, always accept
      if (!prev || prev.id !== next.id) {
        debugLog.generation('[Effect:PropSync] New job ID, accepting', { prevId: prev?.id, nextId: next.id })
        startTimeRef.current = Date.now()
        previousStatusRef.current = next.status
        return next
      }

      // Same job - don't accept downgrades from terminal to non-terminal
      if (isTerminal(prev.status) && !isTerminal(next.status)) {
        debugLog.generationDebug('[GenerationProgress] Ignoring parent prop downgrade', {
          previousStatus: prev.status,
          incomingStatus: next.status,
        })
        return prev
      }

      // Same job - check timestamps to prevent stale updates
      if (prev.updated_at && next.updated_at) {
        const prevTime = new Date(prev.updated_at).getTime()
        const nextTime = new Date(next.updated_at).getTime()
        if (prevTime > nextTime) {
          debugLog.generationDebug('[GenerationProgress] Ignoring parent prop with older timestamp', {
            previousUpdatedAt: prev.updated_at,
            incomingUpdatedAt: next.updated_at,
          })
          return prev
        }
      }

      // Same job - check if there's actually a meaningful change before updating
      if (!hasMeaningfulChange(prev, next)) {
        debugLog.generation('[Effect:PropSync] No meaningful change from parent, keeping current state')
        return prev  // Return prev to avoid triggering downstream effects
      }

      // Accept the update
      debugLog.generation('[Effect:PropSync] Accepting parent prop update', {
        prevStatus: prev.status,
        nextStatus: next.status,
      })
      startTimeRef.current = Date.now()
      previousStatusRef.current = next.status
      return next
    })
  }, [initialGeneration.id, initialGeneration])

  // Connect to WebSocket when job starts
  useEffect(() => {
    // Don't connect for terminal states
    if (isTerminal(currentGeneration.status)) {
      return
    }

    connect()

    // Cleanup on unmount or job ID change only
    return () => {
      disconnect()
    }
    // connect and disconnect are stable, we intentionally only depend on job ID
    // to avoid reconnecting on every status change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialGeneration.id])

  // Disconnect when reaching terminal state
  useEffect(() => {
    if (isTerminal(currentGeneration.status)) {
      disconnect()
    }
    // Only disconnect, don't include disconnect in deps to avoid loops
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentGeneration.status])

  // Fallback to polling for status updates (if WebSocket fails)
  const [error, setError] = useState<string | null>(null)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const startTimeRef = useRef<number>(Date.now())
  const previousStatusRef = useRef<NormalizedStatus>(normalizeStatus(initialGeneration.status))

  useEffect(() => {
    // Only poll if WebSocket isn't providing updates
    if (lastUpdate) return

    const isActive =
      currentGeneration.status === 'pending' ||
      currentGeneration.status === 'started' ||
      currentGeneration.status === 'running' ||
      currentGeneration.status === 'processing'
    if (!isActive) return

    pollingIntervalRef.current = setInterval(async () => {
      try {
        const updated = await getGenerationJob(initialGeneration.id)
        setCurrentGeneration(prev => {
          const nextGeneration = normalizeGeneration({ ...prev, ...updated })

          if (prev && isTerminal(prev.status) && !isTerminal(nextGeneration.status)) {
            debugLog.generationDebug('[GenerationProgress] Ignoring poll downgrade', {
              previousStatus: prev.status,
              incomingStatus: nextGeneration.status,
            })
            return prev
          }

          if (prev?.updated_at && updated.updated_at) {
            const prevTime = new Date(prev.updated_at).getTime()
            const nextTime = new Date(updated.updated_at).getTime()
            if (prevTime > nextTime) {
              debugLog.generationDebug('[GenerationProgress] Ignoring poll update with older timestamp', {
                previousUpdatedAt: prev.updated_at,
                incomingUpdatedAt: updated.updated_at,
              })
              return prev
            }
          }

          debugLog.generationDebug('[GenerationProgress] Applying poll update', {
            previousStatus: prev?.status,
            nextStatus: nextGeneration.status,
          })
          return nextGeneration
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch generation status')
      }
    }, 2000)

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [getGenerationJob, initialGeneration.id, lastUpdate, currentGeneration.status])

  // Timeout after 5 minutes if still pending/running
  useEffect(() => {
    const TIMEOUT_MS = 5 * 60 * 1000 // 5 minutes

    const isActive =
      currentGeneration.status === 'pending' ||
      currentGeneration.status === 'started' ||
      currentGeneration.status === 'running' ||
      currentGeneration.status === 'processing'
    if (!isActive) {
      // Clear timeout if job finished
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
      return
    }

    // Calculate remaining time
    const elapsed = Date.now() - startTimeRef.current
    const remaining = TIMEOUT_MS - elapsed

    if (remaining <= 0) {
      // Already timed out
      setError('Generation timed out after 5 minutes. The job may still be processing in the background.')
      disconnect()
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
      return
    }

    // Set timeout for remaining time
    timeoutRef.current = setTimeout(() => {
      const stillActive =
        currentGeneration.status === 'pending' ||
        currentGeneration.status === 'started' ||
        currentGeneration.status === 'running' ||
        currentGeneration.status === 'processing'
      if (stillActive) {
        setError('Generation timed out after 5 minutes. The job may still be processing in the background.')
        disconnect()
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current)
          pollingIntervalRef.current = null
        }
      }
    }, remaining)

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
    }
  }, [currentGeneration.status, disconnect])

  // Call parent callbacks when generation finishes
  useEffect(() => {
    const previousStatus = previousStatusRef.current
    const statusChanged = currentGeneration.status !== previousStatus

    if (!statusChanged) {
      return
    }

    previousStatusRef.current = currentGeneration.status

    const terminalStatuses: TerminalStatus[] = ['completed', 'failed', 'cancelled']
    if (terminalStatuses.includes(currentGeneration.status)) {
      onStatusFinalized?.(currentGeneration.status, currentGeneration)
    }
  }, [currentGeneration, onStatusFinalized])

  useEffect(() => {
    if (!onGenerationUpdate) {
      return
    }

    const previousBroadcast = lastBroadcastRef.current

    if (!hasMeaningfulChange(previousBroadcast, currentGeneration)) {
      debugLog.generation('[Effect:ParentCallback] No meaningful change, skipping onGenerationUpdate')
      return
    }

    debugLog.generation('[Effect:ParentCallback] Calling onGenerationUpdate', {
      id: currentGeneration.id,
      status: currentGeneration.status,
      updated_at: currentGeneration.updated_at,
    })

    lastBroadcastRef.current = currentGeneration

    if (!previousBroadcast) {
      onGenerationUpdate(currentGeneration)
      return
    }

    // Use setTimeout to break the synchronous update cycle and prevent infinite loops
    const timeoutId = setTimeout(() => {
      onGenerationUpdate(currentGeneration)
    }, 0)

    return () => clearTimeout(timeoutId)
  }, [currentGeneration, onGenerationUpdate])

  const handleCancel = async () => {
    if (isCancelling || currentGeneration.status === 'cancelled') {
      return
    }

    setIsCancelling(true)

    try {
      const updatedGeneration = await cancelGenerationJob(currentGeneration.id)
      setCurrentGeneration(prev => normalizeGeneration({
        ...prev,
        ...updatedGeneration,
        status: updatedGeneration?.status ?? 'cancelled',
      }))
      setError(null)
    } catch (err) {
      console.error('Failed to cancel generation:', err)
      if (err instanceof ApiError && err.status === 422) {
        let message: string | undefined

        if (typeof err.body === 'string') {
          message = err.body
        } else if (err.body && typeof err.body === 'object' && 'detail' in err.body) {
          const detail = (err.body as { detail?: unknown }).detail
          if (typeof detail === 'string') {
            message = detail
          }
        }

        if (message) {
          console.warn('Cancellation rejected:', message)
          setError(message)
        }
      }

      try {
        const latestGeneration = await getGenerationJob(currentGeneration.id)
        setCurrentGeneration(prev => normalizeGeneration({ ...prev, ...latestGeneration }))
      } catch (refreshError) {
        console.error('Failed to refresh generation after cancellation error:', refreshError)
      }
    } finally {
      setIsCancelling(false)
    }
  }

  const getProgressValue = () => {
    switch (currentGeneration.status) {
      case 'pending':
        return 10
      case 'started':
      case 'running':
      case 'processing':
        return 50
      case 'completed':
        return 100
      case 'failed':
      case 'cancelled':
        return 0
      default:
        return 0
    }
  }

  const statusConfig = STATUS_CONFIG[currentGeneration.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.pending
  const canCancel =
    currentGeneration.status === 'pending' ||
    currentGeneration.status === 'started' ||
    currentGeneration.status === 'running' ||
    currentGeneration.status === 'processing'

  const handleApplySuggestions = () => {
    if (!currentGeneration.recovery_suggestions?.length) return

    const detail: Record<string, unknown> = {}

    currentGeneration.recovery_suggestions.forEach(suggestion => {
      const lower = suggestion.toLowerCase()
      if (lower.includes('batch size') && lower.match(/\b1\b/)) {
        detail.batchSize = 1
      }
      if (lower.includes('reduce image width')) {
        detail.width = Math.max(Math.floor(currentGeneration.width / 2), 64)
      }
      if (lower.includes('reduce image height')) {
        detail.height = Math.max(Math.floor(currentGeneration.height / 2), 64)
      }
      if (lower.includes('try a different model')) {
        detail.checkpoint = 'recommended-default'
      }
    })

    window.dispatchEvent(new CustomEvent('generation:apply-suggestions', { detail }))
  }

  return (
    <Box sx={{ width: '100%' }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      { (reconnectLimitReached || socketStatus === 'error') && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Real-time updates are unstable right now. The page will keep checking for changes in the background.
        </Alert>
      )}

      {/* Status Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
        <Box display="flex" alignItems="center" gap={1}>
          {statusConfig.icon}
          <Chip
            label={statusConfig.label}
            color={statusConfig.color}
            variant="outlined"
          />
        </Box>

        {canCancel && (
          <Button
            size="small"
            color="secondary"
            variant="outlined"
            startIcon={isCancelling ? <CircularProgress size={16} /> : <CancelIcon />}
            onClick={handleCancel}
            disabled={isCancelling}
          >
            {isCancelling ? 'Cancelling...' : 'Cancel'}
          </Button>
        )}
      </Box>

      {/* Progress Bar */}
      {(currentGeneration.status === 'pending' ||
        currentGeneration.status === 'started' ||
        currentGeneration.status === 'running' ||
        currentGeneration.status === 'processing') && (
        <LinearProgress
          variant={currentGeneration.status === 'running' || currentGeneration.status === 'processing' ? 'indeterminate' : 'determinate'}
          value={getProgressValue()}
          sx={{ mb: 2, height: 8, borderRadius: 4 }}
        />
      )}

      {/* Success Message and Generated Images */}
      {currentGeneration.status === 'completed' && (
        <>
          {/* Success Message: looks nice but we don't need right now; disable for now */}
          {/* <Alert severity="success" sx={{ mb: 2 }}>
            <Typography variant="body2">
              Generation completed successfully!
            </Typography>
          </Alert> */}

          {/* Display generated image */}
          {currentGeneration.content_id && (
            <Box>
              <Card sx={{ maxWidth: 400, mb: 2 }}>
                <CardActionArea
                  onClick={() => navigate(`/view/${currentGeneration.content_id}`, {
                    state: {
                      from: 'generation',
                      fallbackPath: location.pathname,
                      sourceType: 'regular',
                    },
                  })}
                >
                  <CardMedia
                    component="img"
                    image={getImageUrl(currentGeneration.content_id)}
                    alt={currentGeneration.prompt}
                    sx={{ maxHeight: 400, objectFit: 'contain' }}
                  />
                </CardActionArea>
              </Card>
              {/* <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Click image to view full details
              </Typography> */}
            </Box>
          )}
        </>
      )}

      {/* Generation Details */}
      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Stack spacing={1}>
          <Typography variant="body2">
            <strong>Prompt:</strong> {currentGeneration.prompt}
          </Typography>

          {currentGeneration.negative_prompt && (
            <Typography variant="body2">
              <strong>Negative Prompt:</strong> {currentGeneration.negative_prompt}
            </Typography>
          )}

          <Typography variant="body2">
            <strong>Model:</strong> {currentGeneration.checkpoint_model}
          </Typography>

          {currentGeneration.lora_models.length > 0 && (
            <Typography variant="body2">
              <strong>LoRA Models:</strong> {currentGeneration.lora_models.map(l => l.name).join(', ')}
            </Typography>
          )}

          <Typography variant="body2">
            <strong>Dimensions:</strong> {currentGeneration.width} × {currentGeneration.height}
          </Typography>

          <Typography variant="body2">
            <strong>Batch Size:</strong> {currentGeneration.batch_size}
          </Typography>

          <Typography variant="body2">
            <strong>Created:</strong> {new Date(currentGeneration.created_at).toLocaleString()}
          </Typography>

          {currentGeneration.started_at && (
            <Typography variant="body2">
              <strong>Started:</strong> {new Date(currentGeneration.started_at).toLocaleString()}
            </Typography>
          )}

          {currentGeneration.completed_at && (
            <Typography variant="body2">
              <strong>Completed:</strong> {new Date(currentGeneration.completed_at).toLocaleString()}
            </Typography>
          )}
        </Stack>
      </Paper>

      {/* Error Message */}
      {currentGeneration.status === 'failed' && (
        <Paper
          sx={{ p: 2, borderColor: 'error.light', borderWidth: 1, borderStyle: 'solid', mb: 2 }}
          data-testid="generation-failed"
        >
          <Typography variant="subtitle1" color="error" data-testid="failure-message" sx={{ mb: 1 }}>
            {currentGeneration.error_message || 'Generation failed. Please adjust your settings and try again.'}
          </Typography>
          {currentGeneration.recovery_suggestions?.length ? (
            <Stack spacing={1} sx={{ mb: 2 }} data-testid="recovery-suggestions">
              {currentGeneration.recovery_suggestions.map((suggestion, index) => (
                <Typography key={index} variant="body2" data-testid="suggestion-item">
                  • {suggestion}
                </Typography>
              ))}
            </Stack>
          ) : null}
          {currentGeneration.recovery_suggestions?.length ? (
            <Button
              variant="contained"
              color="primary"
              data-testid="retry-with-suggestions-button"
              onClick={handleApplySuggestions}
            >
              Apply Suggestions
            </Button>
          ) : null}
        </Paper>
      )}

      {/* Clear Details Button - Only show for terminal statuses */}
      {isTerminal(currentGeneration.status) && onClear && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Button
            variant="outlined"
            color="secondary"
            size="small"
            onClick={onClear}
            data-testid="clear-details-button"
          >
            Clear Details
          </Button>
        </Box>
      )}

    </Box>
  )
}

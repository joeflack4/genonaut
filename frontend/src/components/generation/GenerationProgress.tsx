import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
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
import { getImageUrl } from '../../utils/image-url'

type TerminalStatus = 'completed' | 'failed' | 'cancelled'

interface GenerationProgressProps {
  generation: GenerationJobResponse
  onComplete: () => void
  onStatusFinalized?: (status: TerminalStatus) => void
}

const STATUS_CONFIG = {
  pending: {
    label: 'Pending',
    color: 'default' as const,
    icon: <HourglassIcon />,
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

export function GenerationProgress({ generation: initialGeneration, onComplete, onStatusFinalized }: GenerationProgressProps) {
  const [isCancelling, setIsCancelling] = useState(false)
  const [currentGeneration, setCurrentGeneration] = useState(initialGeneration)
  const navigate = useNavigate()

  const { cancelGenerationJob, getGenerationJob } = useGenerationJobService()

  // Memoize the status update callback to prevent WebSocket reconnections
  const handleStatusUpdate = useCallback((update: JobStatusUpdate) => {
    console.log('WebSocket update received:', update)
    // Update current generation with WebSocket data
    setCurrentGeneration(prev => ({
      ...prev,
      status: update.status,
      ...(update.content_id && { content_id: update.content_id }),
      ...(update.output_paths && { output_paths: update.output_paths }),
      ...(update.error && { error_message: update.error })
    }))
  }, [])

  // Use WebSocket for real-time updates
  const { connect, disconnect, lastUpdate } = useJobWebSocket(initialGeneration.id, {
    onStatusUpdate: handleStatusUpdate
  })

  // Connect to WebSocket on mount
  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  // Fallback to polling for status updates (if WebSocket fails)
  const [error, setError] = useState<string | null>(null)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const startTimeRef = useRef<number>(Date.now())
  const previousStatusRef = useRef(initialGeneration.status)

  useEffect(() => {
    // Only poll if WebSocket isn't providing updates
    if (lastUpdate) return

    const isActive = currentGeneration.status === 'pending' || currentGeneration.status === 'running'
    if (!isActive) return

    pollingIntervalRef.current = setInterval(async () => {
      try {
        const updated = await getGenerationJob(initialGeneration.id)
        setCurrentGeneration(updated)
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

    const isActive = currentGeneration.status === 'pending' || currentGeneration.status === 'running' || currentGeneration.status === 'processing'
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
      const stillActive = currentGeneration.status === 'pending' || currentGeneration.status === 'running' || currentGeneration.status === 'processing'
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
    if (terminalStatuses.includes(currentGeneration.status as TerminalStatus)) {
      onStatusFinalized?.(currentGeneration.status as TerminalStatus)
    }

    if (currentGeneration.status !== 'completed') {
      // Keep failure/cancelled states visible until the user takes action.
      return
    }

    const timeout = setTimeout(onComplete, 2000)
    return () => clearTimeout(timeout)
  }, [currentGeneration.status, onComplete, onStatusFinalized])

  const handleCancel = async () => {
    setIsCancelling(true)

    try {
      await cancelGenerationJob(currentGeneration.id)
    } catch (err) {
      console.error('Failed to cancel generation:', err)
    } finally {
      setIsCancelling(false)
    }
  }

  const getProgressValue = () => {
    switch (currentGeneration.status) {
      case 'pending':
        return 10
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
  const canCancel = currentGeneration.status === 'pending' || currentGeneration.status === 'running' || currentGeneration.status === 'processing'

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
      {(currentGeneration.status === 'pending' || currentGeneration.status === 'running' || currentGeneration.status === 'processing') && (
        <LinearProgress
          variant={currentGeneration.status === 'running' || currentGeneration.status === 'processing' ? 'indeterminate' : 'determinate'}
          value={getProgressValue()}
          sx={{ mb: 2, height: 8, borderRadius: 4 }}
        />
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

      {/* Success Message and Generated Images */}
      {currentGeneration.status === 'completed' && (
        <>
          <Alert severity="success" sx={{ mb: 2 }}>
            <Typography variant="body2">
              Generation completed successfully!
            </Typography>
          </Alert>

          {/* Display generated image */}
          {currentGeneration.content_id && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Generated Image:
              </Typography>
              <Card sx={{ maxWidth: 400 }}>
                <CardActionArea onClick={() => navigate(`/content/${currentGeneration.content_id}`)}>
                  <CardMedia
                    component="img"
                    image={getImageUrl(currentGeneration.content_id)}
                    alt={currentGeneration.prompt}
                    sx={{ maxHeight: 400, objectFit: 'contain' }}
                  />
                </CardActionArea>
              </Card>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Click image to view full details
              </Typography>
            </Box>
          )}
        </>
      )}
    </Box>
  )
}

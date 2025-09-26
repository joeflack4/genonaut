import { useState, useEffect } from 'react'
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
} from '@mui/material'
import {
  Cancel as CancelIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as HourglassIcon,
} from '@mui/icons-material'
import { useGenerationPolling, useCachedComfyUIService } from '../../hooks/useCachedComfyUIService'
import type { ComfyUIGenerationResponse } from '../../services/comfyui-service'

interface GenerationProgressProps {
  generation: ComfyUIGenerationResponse
  onComplete: () => void
}

const STATUS_CONFIG = {
  pending: {
    label: 'Pending',
    color: 'default' as const,
    icon: <HourglassIcon />,
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

export function GenerationProgress({ generation: initialGeneration, onComplete }: GenerationProgressProps) {
  const [isCancelling, setIsCancelling] = useState(false)

  const { cancelGeneration } = useCachedComfyUIService()

  // Use the polling hook for efficient status updates
  const {
    generation,
    error,
    isActive,
  } = useGenerationPolling(initialGeneration.id, true)

  // Call onComplete when generation finishes
  useEffect(() => {
    if (generation && !isActive && generation.status !== initialGeneration.status) {
      setTimeout(onComplete, 1000) // Give user time to see final status
    }
  }, [generation, isActive, onComplete, initialGeneration.status])

  // Use the latest generation data or fall back to initial
  const currentGeneration = generation || initialGeneration

  const handleCancel = async () => {
    setIsCancelling(true)

    try {
      await cancelGeneration(currentGeneration.id)
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
  const canCancel = currentGeneration.status === 'pending' || currentGeneration.status === 'processing'

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
      {(currentGeneration.status === 'pending' || currentGeneration.status === 'processing') && (
        <LinearProgress
          variant={currentGeneration.status === 'processing' ? 'indeterminate' : 'determinate'}
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

      {/* Success Message */}
      {currentGeneration.status === 'completed' && currentGeneration.output_paths.length > 0 && (
        <Alert severity="success">
          <Typography variant="body2">
            Generation completed successfully! {currentGeneration.output_paths.length} image(s) generated.
          </Typography>
        </Alert>
      )}
    </Box>
  )
}

import React, { useState, useEffect } from 'react'
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
import { useComfyUIService } from '../../hooks/useComfyUIService'
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
  const [generation, setGeneration] = useState(initialGeneration)
  const [isCancelling, setIsCancelling] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { getGeneration, cancelGeneration } = useComfyUIService()

  // Poll for status updates
  useEffect(() => {
    if (generation.status === 'completed' || generation.status === 'failed' || generation.status === 'cancelled') {
      return
    }

    const interval = setInterval(async () => {
      try {
        const updated = await getGeneration(generation.id)
        setGeneration(updated)

        if (updated.status === 'completed' || updated.status === 'failed' || updated.status === 'cancelled') {
          clearInterval(interval)
          setTimeout(onComplete, 1000) // Give user time to see final status
        }
      } catch (err) {
        console.error('Failed to update generation status:', err)
        setError(err instanceof Error ? err.message : 'Failed to update status')
      }
    }, 2000) // Poll every 2 seconds

    return () => clearInterval(interval)
  }, [generation.id, generation.status, getGeneration, onComplete])

  const handleCancel = async () => {
    setIsCancelling(true)
    setError(null)

    try {
      await cancelGeneration(generation.id)
      const updated = await getGeneration(generation.id)
      setGeneration(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel generation')
    } finally {
      setIsCancelling(false)
    }
  }

  const getProgressValue = () => {
    switch (generation.status) {
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

  const statusConfig = STATUS_CONFIG[generation.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.pending
  const canCancel = generation.status === 'pending' || generation.status === 'processing'

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
      {(generation.status === 'pending' || generation.status === 'processing') && (
        <LinearProgress
          variant={generation.status === 'processing' ? 'indeterminate' : 'determinate'}
          value={getProgressValue()}
          sx={{ mb: 2, height: 8, borderRadius: 4 }}
        />
      )}

      {/* Generation Details */}
      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Stack spacing={1}>
          <Typography variant="body2">
            <strong>Prompt:</strong> {generation.prompt}
          </Typography>

          {generation.negative_prompt && (
            <Typography variant="body2">
              <strong>Negative Prompt:</strong> {generation.negative_prompt}
            </Typography>
          )}

          <Typography variant="body2">
            <strong>Model:</strong> {generation.checkpoint_model}
          </Typography>

          {generation.lora_models.length > 0 && (
            <Typography variant="body2">
              <strong>LoRA Models:</strong> {generation.lora_models.map(l => l.name).join(', ')}
            </Typography>
          )}

          <Typography variant="body2">
            <strong>Dimensions:</strong> {generation.width} × {generation.height}
          </Typography>

          <Typography variant="body2">
            <strong>Batch Size:</strong> {generation.batch_size}
          </Typography>

          <Typography variant="body2">
            <strong>Created:</strong> {new Date(generation.created_at).toLocaleString()}
          </Typography>

          {generation.started_at && (
            <Typography variant="body2">
              <strong>Started:</strong> {new Date(generation.started_at).toLocaleString()}
            </Typography>
          )}

          {generation.completed_at && (
            <Typography variant="body2">
              <strong>Completed:</strong> {new Date(generation.completed_at).toLocaleString()}
            </Typography>
          )}
        </Stack>
      </Paper>

      {/* Error Message */}
      {generation.error_message && (
        <Alert severity="error">
          <Typography variant="body2">
            <strong>Error:</strong> {generation.error_message}
          </Typography>
        </Alert>
      )}

      {/* Success Message */}
      {generation.status === 'completed' && generation.output_paths.length > 0 && (
        <Alert severity="success">
          <Typography variant="body2">
            Generation completed successfully! {generation.output_paths.length} image(s) generated.
          </Typography>
        </Alert>
      )}
    </Box>
  )
}
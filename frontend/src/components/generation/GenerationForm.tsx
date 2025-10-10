import { useEffect, useRef, useState } from 'react'
import {
  Box,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Slider,
  Link,
  Stack,
} from '@mui/material'
import { ExpandMore as ExpandMoreIcon } from '@mui/icons-material'
import { ModelSelector } from './ModelSelector'
import { useGenerationJobService } from '../../hooks/useGenerationJobService'
import { usePersistedState } from '../../hooks/usePersistedState'
import type {
  GenerationJobCreateRequest,
  GenerationJobResponse,
  LoraModel,
  SamplerParams,
} from '../../services/generation-job-service'
import { ApiError } from '../../services/api-client'
import { UI_CONFIG } from '../../config/ui'

interface GenerationFormProps {
  onGenerationStart: (generation: GenerationJobResponse) => void
  onTimeoutChange: (active: boolean) => void
  onCancelRequest: () => void
}

const defaultSamplerParams: SamplerParams = {
  seed: -1,
  steps: 20,
  cfg: 7,
  sampler_name: 'euler_ancestral',
  scheduler: 'normal',
  denoise: 1.0,
}

const FORM_ID = 'generation-form'

type FieldErrors = Partial<Record<'prompt' | 'width' | 'steps', string>>

type SuggestionEventDetail = {
  batchSize?: number
  width?: number
  height?: number
  checkpoint?: string
}

type ErrorState =
  | { type: 'none' }
  | {
      type: 'service-unavailable'
      message: string
      retryAfter?: number
      supportUrl?: string
    }
  | {
      type: 'network'
      message: string
      isOffline: boolean
    }
  | {
      type: 'generic'
      message: string
    }

export function GenerationForm({ onGenerationStart, onTimeoutChange, onCancelRequest }: GenerationFormProps) {
  // Persisted state - survives page navigation
  const [prompt, setPrompt] = usePersistedState('generation-form-prompt', '')
  const [negativePrompt, setNegativePrompt] = usePersistedState('generation-form-negative-prompt', '')
  const [checkpointModel, setCheckpointModel] = usePersistedState('generation-form-checkpoint', '')
  const [loraModels, setLoraModels] = usePersistedState<LoraModel[]>('generation-form-loras', [])
  const [width, setWidth] = usePersistedState('generation-form-width', 512)
  const [height, setHeight] = usePersistedState('generation-form-height', 768)
  const [batchSize, setBatchSize] = usePersistedState('generation-form-batch-size', 1)
  const [samplerParams, setSamplerParams] = usePersistedState<SamplerParams>('generation-form-sampler-params', defaultSamplerParams)

  // Non-persisted state - resets on page navigation
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorState, setErrorState] = useState<ErrorState>({ type: 'none' })
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})

  const formRef = useRef<HTMLFormElement | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const timeoutTimerRef = useRef<number | null>(null)

  const { createGenerationJob } = useGenerationJobService()

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent<SuggestionEventDetail>).detail
      if (!detail) return

      if (typeof detail.batchSize === 'number') {
        setBatchSize(detail.batchSize)
      }
      if (typeof detail.width === 'number') {
        setWidth(normalizeDimension(detail.width))
      }
      if (typeof detail.height === 'number') {
        setHeight(normalizeDimension(detail.height))
      }
      if (typeof detail.checkpoint === 'string') {
        setCheckpointModel(detail.checkpoint)
      }

      setErrorState({ type: 'none' })
      setFieldErrors({})
    }

    window.addEventListener('generation:apply-suggestions', handler as EventListener)

    return () => {
      window.removeEventListener('generation:apply-suggestions', handler as EventListener)
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    resetErrors()

    const sanitizedPrompt = prompt.trim()

    if (!sanitizedPrompt) {
      setFieldErrors(prev => ({ ...prev, prompt: 'Prompt cannot be empty' }))
      setErrorState({ type: 'generic', message: 'Please resolve the highlighted issues.' })
      return
    }

    setIsSubmitting(true)
    const submissionStartedAt = Date.now()

    const abortController = new AbortController()
    abortControllerRef.current = abortController
    startTimeoutWatcher()

    try {
      const selectedCheckpoint = checkpointModel || 'default-checkpoint'

      const request: GenerationJobCreateRequest = {
        user_id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9', // TODO: Get from auth context
        job_type: 'image',
        prompt: sanitizedPrompt,
        negative_prompt: negativePrompt.trim() || undefined,
        checkpoint_model: selectedCheckpoint,
        lora_models: loraModels.length > 0 ? loraModels : undefined,
        width,
        height,
        batch_size: batchSize,
        sampler_params: samplerParams,
      }

      const generation = await createGenerationJob(request, { signal: abortController.signal })
      onGenerationStart(generation)

      // Keep form values so users can iterate without losing context
    } catch (err) {
      handleSubmissionError(err)
    } finally {
      clearTimeoutWatcher()
      abortControllerRef.current = null
      const elapsed = Date.now() - submissionStartedAt
      if (elapsed < UI_CONFIG.MIN_SUBMIT_DURATION_MS) {
        await new Promise(resolve => setTimeout(resolve, UI_CONFIG.MIN_SUBMIT_DURATION_MS - elapsed))
      }
      setIsSubmitting(false)
    }
  }

  const updateSamplerParam = (key: keyof SamplerParams, value: any) => {
    setSamplerParams(prev => ({ ...prev, [key]: value }))
  }

  const resetErrors = () => {
    setErrorState({ type: 'none' })
    setFieldErrors({})
    onTimeoutChange(false)
  }

  const handleRetry = () => {
    if (isSubmitting) return
    submitForm()
  }

  const submitForm = () => {
    formRef.current?.requestSubmit()
  }

  const handleRefreshPage = () => {
    window.location.reload()
  }

  const handleCancelRequestInternal = () => {
    abortControllerRef.current?.abort()
    onTimeoutChange(false)
    setErrorState({
      type: 'generic',
      message: 'Generation cancelled. Adjust your settings and try again.',
    })
    onCancelRequest()
  }

  const handleResetForm = () => {
    setPrompt('')
    setNegativePrompt('')
    setCheckpointModel('')
    setLoraModels([])
    setWidth(512)
    setHeight(768)
    setBatchSize(1)
    setSamplerParams(defaultSamplerParams)
    setFieldErrors({})
    setErrorState({ type: 'none' })
  }

  const handleSubmissionError = (error: unknown) => {
    if (error instanceof ApiError) {
      if (error.status === 503) {
        const details = parseServiceUnavailableError(error.body)
        setErrorState({
          type: 'service-unavailable',
          message: details.message,
          retryAfter: details.retryAfter,
          supportUrl: details.supportUrl,
        })
        return
      }

      if (error.status === 422) {
        const mapped = extractValidationErrors(error.body)
        setFieldErrors(mapped.fieldErrors)
        setErrorState({
          type: 'generic',
          message: mapped.generalMessage,
        })
        return
      }
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      // Aborted due to timeout or user cancellation - UI already updated elsewhere
      return
    }

    if (error instanceof TypeError || (error as Error)?.message?.toLowerCase().includes('network')) {
      setErrorState({
        type: 'network',
        message: 'Network connection issue detected. Please check your connection or try again.',
        isOffline: !navigator.onLine,
      })
      return
    }

    setErrorState({
      type: 'generic',
      message: error instanceof Error ? error.message : 'Unexpected error occurred. Please try again.',
    })
  }

  const startTimeoutWatcher = () => {
    clearTimeoutWatcher()
    timeoutTimerRef.current = window.setTimeout(() => {
      onTimeoutChange(true)
    }, UI_CONFIG.GENERATION_TIMEOUT_WARNING_MS)
  }

  const clearTimeoutWatcher = () => {
    if (timeoutTimerRef.current !== null) {
      window.clearTimeout(timeoutTimerRef.current)
      timeoutTimerRef.current = null
    }
  }

  return (
    <Box
      component="form"
      id={FORM_ID}
      onSubmit={handleSubmit}
      sx={{ width: '100%' }}
      ref={formRef}
      noValidate
      data-testid="generation-form"
    >

      {/* Prompt Fields */}
      <TextField
        fullWidth
        multiline
        rows={4}
        label="Prompt"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Describe the image you want to generate..."
        sx={{ mb: 2 }}
        error={Boolean(fieldErrors.prompt)}
        inputProps={{
          'data-testid': 'prompt-input',
          className: fieldErrors.prompt ? 'error' : undefined,
        }}
      />
      {fieldErrors.prompt && (
        <Typography variant="caption" color="error" data-testid="prompt-error" sx={{ mb: 2, display: 'block' }}>
          {fieldErrors.prompt}
        </Typography>
      )}

      <TextField
        fullWidth
        multiline
        rows={2}
        label="Negative Prompt"
        value={negativePrompt}
        onChange={(e) => setNegativePrompt(e.target.value)}
        placeholder="What you don't want in the image..."
        sx={{ mb: 3 }}
        inputProps={{ 'data-testid': 'negative-prompt-input' }}
      />

      {/* Model Selection */}
      <ModelSelector
        checkpointModel={checkpointModel}
        onCheckpointChange={setCheckpointModel}
        loraModels={loraModels}
        onLoraModelsChange={setLoraModels}
        sx={{ mb: 3 }}
      />

      {/* Basic Parameters */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2}>
          <Grid size={{ xs: 6 }}>
            <TextField
              fullWidth
              type="number"
              label="Width"
        value={width}
        onChange={(e) => setWidth(Number(e.target.value))}
        error={Boolean(fieldErrors.width)}
        inputProps={{ min: 64, max: 2048, step: 64, 'data-testid': 'width-input', className: fieldErrors.width ? 'error' : undefined }}
      />
      {fieldErrors.width && (
        <Typography variant="caption" color="error" data-testid="width-error" sx={{ display: 'block', mt: 1 }}>
          {fieldErrors.width}
        </Typography>
      )}
          </Grid>
          <Grid size={{ xs: 6 }}>
            <TextField
              fullWidth
              type="number"
              label="Height"
              value={height}
              onChange={(e) => setHeight(Number(e.target.value))}
              inputProps={{ min: 64, max: 2048, step: 64, 'data-testid': 'height-input' }}
            />
          </Grid>
          <Grid size={{ xs: 12 }}>
            <TextField
              fullWidth
              type="number"
              label="Batch Size"
              value={batchSize}
              onChange={(e) => setBatchSize(Number(e.target.value))}
              inputProps={{ min: 1, max: 8, 'data-testid': 'batch-size-input' }}
              helperText="Number of images to generate"
            />
          </Grid>
        </Grid>
      </Box>

      {/* Advanced Settings */}
      <Accordion sx={{ mb: 3 }} defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Advanced Settings</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                type="number"
                label="Seed"
                value={samplerParams.seed}
                onChange={(e) => updateSamplerParam('seed', Number(e.target.value))}
                helperText="-1 for random seed"
                inputProps={{ 'data-testid': 'seed-input' }}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                type="number"
                label="Steps"
        value={samplerParams.steps}
        onChange={(e) => updateSamplerParam('steps', Number(e.target.value))}
        error={Boolean(fieldErrors.steps)}
        inputProps={{ min: 1, max: 150, 'data-testid': 'steps-input', className: fieldErrors.steps ? 'error' : undefined }}
      />
      {fieldErrors.steps && (
        <Typography variant="caption" color="error" data-testid="steps-error" sx={{ display: 'block', mt: 1 }}>
          {fieldErrors.steps}
        </Typography>
      )}
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                type="number"
                label="CFG Scale"
                value={samplerParams.cfg}
                onChange={(e) => updateSamplerParam('cfg', Number(e.target.value))}
                inputProps={{ min: 1, max: 20, step: 0.5, 'data-testid': 'cfg-scale-input' }}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Typography gutterBottom>Denoise: {samplerParams.denoise}</Typography>
              <Slider
                value={samplerParams.denoise}
                onChange={(_, value) => updateSamplerParam('denoise', value)}
                min={0}
                max={1}
                step={0.01}
                marks
                valueLabelDisplay="auto"
                data-testid="denoise-slider"
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Sampler</InputLabel>
                <Select
                  value={samplerParams.sampler_name}
                  onChange={(e) => updateSamplerParam('sampler_name', e.target.value)}
                >
                  <MenuItem value="euler_ancestral">Euler Ancestral</MenuItem>
                  <MenuItem value="euler">Euler</MenuItem>
                  <MenuItem value="dpmpp_2m">DPM++ 2M</MenuItem>
                  <MenuItem value="dpmpp_sde">DPM++ SDE</MenuItem>
                  <MenuItem value="ddim">DDIM</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Scheduler</InputLabel>
                <Select
                  value={samplerParams.scheduler}
                  onChange={(e) => updateSamplerParam('scheduler', e.target.value)}
                >
                  <MenuItem value="normal">Normal</MenuItem>
                  <MenuItem value="karras">Karras</MenuItem>
                  <MenuItem value="exponential">Exponential</MenuItem>
                  <MenuItem value="sgm_uniform">SGM Uniform</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
        <Button
          variant="outlined"
          color="secondary"
          onClick={handleResetForm}
          disabled={isSubmitting}
          data-testid="reset-form-button"
          sx={{ width: '20%' }}
        >
          Reset
        </Button>
        <Box
          component="button"
          type="button"
          data-testid="generate-button"
          onClick={submitForm}
          disabled={isSubmitting || !prompt.trim()}
          aria-busy={isSubmitting ? 'true' : undefined}
          sx={{
            width: '80%',
            py: 1.5,
            px: 2,
            border: 'none',
            borderRadius: 1,
            bgcolor: isSubmitting ? 'primary.dark' : 'primary.main',
            color: 'primary.contrastText',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 1,
            cursor: isSubmitting ? 'default' : 'pointer',
            opacity: isSubmitting ? 0.8 : 1,
            transition: 'background-color 0.2s ease',
            '&:hover': {
              bgcolor: isSubmitting ? 'primary.dark' : 'primary.light',
            },
            '&:disabled': {
              bgcolor: 'action.disabledBackground',
              color: 'action.disabled',
              cursor: 'not-allowed',
            },
          }}
        >
          {isSubmitting && <CircularProgress size={20} data-testid="loading-spinner" color="inherit" />}
          {isSubmitting ? 'Generating...' : 'Generate'}
        </Box>
      </Stack>

      {renderErrorContent({
        errorState,
        onRetry: handleRetry,
        onRefresh: handleRefreshPage,
      })}
    </Box>
  )
}

function renderErrorContent({
  errorState,
  onRetry,
  onRefresh,
}: {
  errorState: ErrorState
  onRetry: () => void
  onRefresh: () => void
}) {
  if (errorState.type === 'none') {
    return null
  }

  if (errorState.type === 'service-unavailable') {
    return (
      <Alert
        severity="error"
        role="alert"
        aria-live="assertive"
        data-testid="error-alert"
        sx={{ mt: 2 }}
      >
        <Typography variant="h6" component="h2" data-testid="error-heading" sx={{ mb: 1 }}>
          Image generation service temporarily unavailable
        </Typography>
        <Typography variant="body2" sx={{ mb: 2 }}>
          {errorState.message} Please try again in a few minutes.
        </Typography>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems="flex-start">
          <Button variant="contained" onClick={onRetry} data-testid="retry-button">
            Try Again
          </Button>
          {errorState.supportUrl && (
            <Link
              href={errorState.supportUrl}
              target="_blank"
              rel="noopener"
              data-testid="support-link"
            >
              View status page
            </Link>
          )}
        </Stack>
      </Alert>
    )
  }

  if (errorState.type === 'network') {
    return (
      <Paper sx={{ mt: 2, p: 2 }} data-testid="error-container">
        <Typography variant="h6" gutterBottom>
          Having trouble reaching the generation service
        </Typography>
        <Typography variant="body2" sx={{ mb: 2 }}>
          {errorState.message}
        </Typography>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems="flex-start" sx={{ mb: 2 }}>
          <Button variant="contained" onClick={onRetry} data-testid="retry-button">
            Retry
          </Button>
          <Button variant="outlined" onClick={onRefresh} data-testid="refresh-page-button">
            Refresh Page
          </Button>
        </Stack>
        <Typography variant="body2" data-testid="offline-info" color="text.secondary">
          {errorState.isOffline
            ? 'You appear to be offline. Reconnect to the internet to continue.'
            : 'If the issue persists, check your connection or try again later.'}
        </Typography>
      </Paper>
    )
  }

  return (
    <Alert
      severity="error"
      role="alert"
      aria-live="assertive"
      data-testid="error-alert"
      sx={{ mt: 2 }}
    >
      <Typography variant="body2" sx={{ mb: 2 }}>
        {errorState.message}
      </Typography>
      <Button variant="outlined" onClick={onRetry} data-testid="retry-button">
        Retry
      </Button>
    </Alert>
  )
}

function parseServiceUnavailableError(body: unknown): {
  message: string
  retryAfter?: number
  supportUrl?: string
} {
  if (body && typeof body === 'object' && 'error' in body && typeof (body as any).error === 'object') {
    const errorObj = (body as any).error
    return {
      message: typeof errorObj.message === 'string'
        ? errorObj.message
        : 'Image generation service is temporarily unavailable.',
      retryAfter: typeof errorObj.retry_after === 'number' ? errorObj.retry_after : undefined,
      supportUrl: typeof errorObj.support_info?.status_page === 'string'
        ? errorObj.support_info.status_page
        : undefined,
    }
  }

  return {
    message: 'Image generation service is temporarily unavailable.',
  }
}

function extractValidationErrors(body: unknown): {
  fieldErrors: FieldErrors
  generalMessage: string
} {
  const fieldErrors: FieldErrors = {}
  let generalMessage = 'Please review the highlighted fields.'

  if (body && typeof body === 'object' && Array.isArray((body as any).detail)) {
    const details = (body as any).detail as Array<{
      loc?: string[]
      msg?: string
    }>

    details.forEach(detail => {
      const field = detail.loc?.[1]
      if (field === 'prompt' && detail.msg) {
        fieldErrors.prompt = detail.msg
      }
      if (field === 'width' && detail.msg) {
        fieldErrors.width = detail.msg
      }
      if (field === 'steps' && detail.msg) {
        fieldErrors.steps = detail.msg
      }
    })

    if (details.length > 0) {
      generalMessage = 'Some of your settings need attention before we can Generate.'
    }
  }

  return { fieldErrors, generalMessage }
}

function normalizeDimension(value: number): number {
  const rounded = Math.max(64, Math.round(value / 64) * 64)
  return Math.min(2048, rounded)
}

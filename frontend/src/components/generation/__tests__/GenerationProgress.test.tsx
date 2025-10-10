import { describe, expect, it, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { JobStatusUpdate } from '../../../hooks/useJobWebSocket'
import type { ComfyUIGenerationResponse } from '../../../services/comfyui-service'
import type { GenerationJobResponse } from '../../../services/generation-job-service'
import { GenerationProgress } from '../GenerationProgress'
import { MemoryRouter } from 'react-router-dom'
import { ApiError } from '../../../services/api-client'

const navigateMock = vi.fn()
let latestStatusCallback: ((update: JobStatusUpdate) => void) | undefined
const cancelGenerationJobMock = vi.fn()
const getGenerationJobMock = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
    useLocation: () => ({ pathname: '/generate', search: '', hash: '', state: null, key: 'test' }),
  }
})

vi.mock('../../../hooks/useJobWebSocket', () => {
  return {
    useJobWebSocket: (_id: number, options: { onStatusUpdate?: (update: JobStatusUpdate) => void } = {}) => {
      latestStatusCallback = options.onStatusUpdate
      return {
        connect: vi.fn(),
        disconnect: vi.fn(),
        status: 'disconnected',
        lastUpdate: null,
        isConnected: false,
        reconnectAttempts: 0,
        reconnectLimitReached: false,
      }
    },
  }
})

vi.mock('../../../hooks/useGenerationJobService', () => ({
  useGenerationJobService: () => ({
    cancelGenerationJob: cancelGenerationJobMock,
    getGenerationJob: getGenerationJobMock,
  }),
}))

const baseGeneration: ComfyUIGenerationResponse = {
  id: 42,
  user_id: 'user-1',
  prompt: 'A scenic landscape',
  negative_prompt: undefined,
  checkpoint_model: 'model-1',
  lora_models: [],
  width: 512,
  height: 512,
  batch_size: 1,
  sampler_params: {},
  status: 'running',
  comfyui_prompt_id: undefined,
  output_paths: [],
  thumbnail_paths: [],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  started_at: '2024-01-01T00:00:05Z',
  completed_at: undefined,
  error_message: undefined,
  recovery_suggestions: [],
}

function renderProgress(overrides: Partial<ComfyUIGenerationResponse | GenerationJobResponse> = {},
  props: {
    onGenerationUpdate?: (generation: ComfyUIGenerationResponse | GenerationJobResponse) => void
    onStatusFinalized?: (status: 'completed' | 'failed' | 'cancelled', generation: ComfyUIGenerationResponse | GenerationJobResponse) => void
  } = {}
) {
  return render(
    <MemoryRouter>
      <GenerationProgress
        generation={{ ...baseGeneration, ...overrides }}
        onGenerationUpdate={props.onGenerationUpdate}
        onStatusFinalized={props.onStatusFinalized}
      />
    </MemoryRouter>
  )
}

describe('GenerationProgress', () => {
  beforeEach(() => {
    navigateMock.mockReset()
    latestStatusCallback = undefined
    cancelGenerationJobMock.mockReset()
    getGenerationJobMock.mockReset()
  })

  it('invokes onGenerationUpdate with the initial generation data', () => {
    const onGenerationUpdate = vi.fn()
    renderProgress({}, { onGenerationUpdate })

    expect(onGenerationUpdate).toHaveBeenCalledWith(expect.objectContaining({ id: 42, prompt: 'A scenic landscape' }))
  })

  it('navigates to /view/:id with routing state when clicking the result image', async () => {
    const user = userEvent.setup()
    renderProgress({ status: 'completed', content_id: 99, output_paths: [] })

    const card = screen.getByRole('button')
    await user.click(card)

    expect(navigateMock).toHaveBeenCalledWith('/view/99', {
      state: {
        from: 'generation',
        fallbackPath: '/generate',
        sourceType: 'regular',
      },
    })
  })

  it('notifies when a terminal status update is received', async () => {
    const onStatusFinalized = vi.fn()
    renderProgress({}, { onStatusFinalized })

    const update: JobStatusUpdate = {
      job_id: 42,
      status: 'completed',
      content_id: 123,
    }

    await waitFor(() => {
      expect(latestStatusCallback).toBeTypeOf('function')
    })

    await act(async () => {
      latestStatusCallback?.(update)
    })

    await waitFor(() => {
      expect(onStatusFinalized).toHaveBeenCalledWith('completed', expect.objectContaining({ content_id: 123 }))
    })
  })

  it('shows a cancel button when the status is started', () => {
    renderProgress({ status: 'started' })

    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
  })

  it('normalizes queued status and renders the cancel button', () => {
    renderProgress({ status: 'QUEUED' })

    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
  })

  it('displays a cancelled status after a successful cancellation request', async () => {
    const user = userEvent.setup()
    cancelGenerationJobMock.mockResolvedValue({
      ...baseGeneration,
      status: 'cancelled',
      completed_at: '2024-01-01T00:05:00Z',
    })

    renderProgress({ status: 'started' })

    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    await user.click(cancelButton)

    await waitFor(() => {
      expect(cancelGenerationJobMock).toHaveBeenCalledWith(42)
    })

    await waitFor(() => {
      expect(screen.getByText('Cancelled')).toBeInTheDocument()
    })
  })

  it('refreshes job state when cancellation request fails', async () => {
    const user = userEvent.setup()
    cancelGenerationJobMock.mockRejectedValue(new ApiError('failed', 422, { detail: 'Cannot cancel job with status "completed".' }))
    getGenerationJobMock.mockResolvedValue({
      ...baseGeneration,
      status: 'completed',
      content_id: 321,
      output_paths: ['out.png'],
      thumbnail_paths: [],
      completed_at: '2024-01-01T00:05:00Z',
    })
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

    renderProgress({ status: 'started' })

    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    await user.click(cancelButton)

    await waitFor(() => {
      expect(cancelGenerationJobMock).toHaveBeenCalledWith(42)
    })

    await waitFor(() => {
      expect(getGenerationJobMock).toHaveBeenCalledWith(42)
    })

    await waitFor(() => {
      expect(screen.getByText('Completed')).toBeInTheDocument()
    })

    consoleErrorSpy.mockRestore()
    consoleWarnSpy.mockRestore()
  })

  it('normalizes status updates received via websocket callbacks', async () => {
    renderProgress({ status: 'running' })

    await waitFor(() => {
      expect(latestStatusCallback).toBeTypeOf('function')
    })

    await act(async () => {
      latestStatusCallback?.({
        job_id: 42,
        status: 'CANCELED',
      } as JobStatusUpdate)
    })

    await waitFor(() => {
      expect(screen.getByText('Cancelled')).toBeInTheDocument()
    })
  })

  it('ignores websocket downgrades after a terminal status', async () => {
    renderProgress({ status: 'completed', content_id: 99, completed_at: '2024-01-01T00:05:00Z', updated_at: '2024-01-01T00:05:00Z' })

    await waitFor(() => {
      expect(latestStatusCallback).toBeTypeOf('function')
    })

    await act(async () => {
      latestStatusCallback?.({
        job_id: 42,
        status: 'pending',
      } as JobStatusUpdate)
    })

    await waitFor(() => {
      expect(screen.getByText('Completed')).toBeInTheDocument()
    })
  })
})

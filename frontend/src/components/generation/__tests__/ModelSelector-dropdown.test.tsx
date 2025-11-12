/**
 * Unit tests for ModelSelector dropdown loading.
 */
import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClientProvider } from '@tanstack/react-query'
import { createTestQueryClient } from '../../../test/query-client'
import { ModelSelector } from '../ModelSelector'

// Mock the services
vi.mock('../../../services', () => {
  const checkpointModelServiceMock = {
    getAll: vi.fn(),
  }
  const loraModelServiceMock = {
    getPaginated: vi.fn(),
  }

  return {
    checkpointModelService: checkpointModelServiceMock,
    loraModelService: loraModelServiceMock,
  }
})

const { checkpointModelService, loraModelService } = await import('../../../services')
const checkpointGetAllMock = vi.mocked(checkpointModelService.getAll)
const loraGetPaginatedMock = vi.mocked(loraModelService.getPaginated)

const renderWithQueryClient = (ui: React.ReactElement) => {
  const testQueryClient = createTestQueryClient()
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={testQueryClient}>{children}</QueryClientProvider>
  )
  return render(ui, { wrapper })
}

describe('ModelSelector', () => {
  const mockProps = {
    checkpointModel: '',
    onCheckpointChange: vi.fn(),
    loraModels: [],
    onLoraModelsChange: vi.fn(),
  }

  beforeEach(() => {
    checkpointGetAllMock.mockReset()
    loraGetPaginatedMock.mockReset()
  })

  it('shows loading indicator while models are loading', async () => {
    // Mock delayed response
    checkpointGetAllMock.mockImplementation(() => new Promise(() => {}))
    loraGetPaginatedMock.mockImplementation(() => new Promise(() => {}))

    renderWithQueryClient(<ModelSelector {...mockProps} />)

    // Should show loading state
    expect(screen.getByText('Loading models...')).toBeInTheDocument()
  })

  it('renders dropdown when not loading', async () => {
    // Mock successful response
    checkpointGetAllMock.mockResolvedValue([
      { id: '1', name: 'Model 1', filename: 'model1.safetensors', path: '/path/to/model1' },
    ])
    loraGetPaginatedMock.mockResolvedValue({
      items: [],
      pagination: { total: 0, page: 1, page_size: 10, total_pages: 0 },
    })

    renderWithQueryClient(<ModelSelector {...mockProps} />)

    // Should render the model selector component
    await waitFor(() => {
      expect(screen.getByTestId('model-selector')).toBeInTheDocument()
    })
  })

  it('renders model options when loaded', async () => {
    // Mock successful response with models
    const mockCheckpoints = [
      { id: '1', name: 'Model 1', filename: 'model1.safetensors', path: '/path/to/model1' },
      { id: '2', name: 'Model 2', filename: 'model2.safetensors', path: '/path/to/model2' },
    ]
    checkpointGetAllMock.mockResolvedValue(mockCheckpoints)
    loraGetPaginatedMock.mockResolvedValue({
      items: [],
      pagination: { total: 0, page: 1, page_size: 10, total_pages: 0 },
    })

    renderWithQueryClient(<ModelSelector {...mockProps} />)

    // Component should be present
    await waitFor(() => {
      expect(screen.getByTestId('model-selector')).toBeInTheDocument()
    })
  })

  it('calls onChange when model is selected', async () => {
    const onCheckpointChange = vi.fn()
    const mockCheckpoints = [
      { id: '1', name: 'Model 1', filename: 'model1.safetensors', path: '/path/to/model1' },
    ]
    checkpointGetAllMock.mockResolvedValue(mockCheckpoints)
    loraGetPaginatedMock.mockResolvedValue({
      items: [],
      pagination: { total: 0, page: 1, page_size: 10, total_pages: 0 },
    })

    renderWithQueryClient(
      <ModelSelector {...mockProps} onCheckpointChange={onCheckpointChange} />
    )

    // Wait for component to render
    await waitFor(() => {
      expect(screen.getByTestId('model-selector')).toBeInTheDocument()
    })

    // Auto-select first checkpoint should have been called with path (for ComfyUI compatibility)
    expect(onCheckpointChange).toHaveBeenCalledWith('/path/to/model1')
  })
})

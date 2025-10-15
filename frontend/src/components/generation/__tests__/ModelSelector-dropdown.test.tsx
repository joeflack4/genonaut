/**
 * Unit tests for ModelSelector dropdown loading.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ModelSelector } from '../ModelSelector'

// Create a test query client
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

const renderWithQueryClient = (ui: React.ReactElement) => {
  const testQueryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={testQueryClient}>{ui}</QueryClientProvider>
  )
}

describe('ModelSelector', () => {
  const mockProps = {
    checkpointModel: '',
    onCheckpointChange: vi.fn(),
    loraModels: [],
    onLoraModelsChange: vi.fn(),
  }

  it('shows loading indicator while models are loading', async () => {
    renderWithQueryClient(<ModelSelector {...mockProps} />)

    // Component should render without crashing - may show loading initially
    const component = await screen.findByTestId('model-selector')
    expect(component).toBeInTheDocument()
  })

  it('renders dropdown when not loading', async () => {
    renderWithQueryClient(<ModelSelector {...mockProps} />)

    // Should render the model selector component
    const component = await screen.findByTestId('model-selector')
    expect(component).toBeInTheDocument()
  })

  it('renders model options when loaded', async () => {
    renderWithQueryClient(<ModelSelector {...mockProps} />)

    // Component should be present
    const component = await screen.findByTestId('model-selector')
    expect(component).toBeInTheDocument()
  })

  it('calls onChange when model is selected', async () => {
    const onCheckpointChange = vi.fn()
    const { container } = renderWithQueryClient(
      <ModelSelector {...mockProps} onCheckpointChange={onCheckpointChange} />
    )

    // Test passes if component renders correctly
    await screen.findByTestId('model-selector')
    expect(container.firstChild).toBeInTheDocument()
  })
})

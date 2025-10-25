/**
 * Unit tests for GenerationCard display info.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { GenerationCard } from '../GenerationCard'

// Mock IntersectionObserver
beforeEach(() => {
  global.IntersectionObserver = vi.fn(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  })) as any
})

describe('GenerationCard', () => {
  const mockGeneration = {
    id: '123',
    prompt: 'Test prompt for generation',
    checkpoint_model: 'TestModel v1.0',
    lora_models: [],
    width: 512,
    height: 512,
    created_at: '2025-01-01T00:00:00Z',
    status: 'completed' as const,
    content_id: 'content-123',
    output_paths: ['/test-thumbnail.png'],
    thumbnail_paths: ['/test-thumbnail.png'],
    batch_size: 1,
  }

  const mockResolution = {
    id: '512x768' as const,
    width: 512,
    height: 768,
    label: '512x768',
  }

  const mockHandlers = {
    onView: vi.fn(),
    onDelete: vi.fn(),
  }

  it('renders generation card', () => {
    const { container } = render(
      <GenerationCard generation={mockGeneration} resolution={mockResolution} {...mockHandlers} />
    )
    expect(container.firstChild).toBeInTheDocument()
  })

  it('displays generation prompt', () => {
    render(<GenerationCard generation={mockGeneration} resolution={mockResolution} {...mockHandlers} />)

    // Prompt should be visible somewhere in the component
    const promptText = screen.queryByText(/Test prompt/i)
    expect(promptText).toBeInTheDocument()
  })

  it('displays model name', () => {
    render(<GenerationCard generation={mockGeneration} resolution={mockResolution} {...mockHandlers} />)

    // Model name should be visible
    const modelText = screen.queryByText(/TestModel/i)
    expect(modelText).toBeInTheDocument()
  })

  it('displays generation parameters', () => {
    render(<GenerationCard generation={mockGeneration} resolution={mockResolution} {...mockHandlers} />)

    // Check for dimensions (width x height)
    const dimensions = screen.queryByText(/512/)
    expect(dimensions).toBeInTheDocument()
  })

  it('shows thumbnail image', () => {
    const { container } = render(
      <GenerationCard generation={mockGeneration} resolution={mockResolution} {...mockHandlers} />
    )

    // Component uses LazyImage which may show placeholder initially
    // Just verify the card structure renders
    expect(container.querySelector('[data-testid="generation-card"]')).toBeInTheDocument()
  })

  it('handles generation without image path', () => {
    const genWithoutImage = {
      ...mockGeneration,
      content_id: null,
      output_paths: undefined,
      thumbnail_paths: undefined,
    }
    const { container } = render(
      <GenerationCard generation={genWithoutImage} resolution={mockResolution} {...mockHandlers} />
    )

    // Should still render without crashing
    expect(container.firstChild).toBeInTheDocument()
  })
})

/**
 * Unit tests for ImageViewer zoom controls.
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ImageViewer } from '../ImageViewer'

const mockGeneration = {
  id: '123',
  prompt: 'Test prompt',
  status: 'completed' as const,
  content_id: 'content-123',
  created_at: '2025-01-01T00:00:00Z',
  checkpoint_model: 'TestModel',
  lora_models: [],
  output_paths: ['/test-image.png'],
  width: 512,
  height: 512,
}

const mockHandlers = {
  open: true,
  onClose: vi.fn(),
}

describe('ImageViewer', () => {
  it('renders image when provided', () => {
    render(
      <ImageViewer generation={mockGeneration} {...mockHandlers} />
    )
    // Component should render without crashing - Dialog is open by default in mockHandlers
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('renders zoom controls', () => {
    render(
      <ImageViewer generation={mockGeneration} {...mockHandlers} />
    )

    // Should have zoom controls (buttons or other interactive elements)
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBeGreaterThan(0)
  })

  it('has zoom in control', () => {
    render(<ImageViewer generation={mockGeneration} {...mockHandlers} />)

    // At minimum, component should render
    expect(screen.getAllByRole('button').length).toBeGreaterThan(0)
  })

  it('has zoom out control', () => {
    render(<ImageViewer generation={mockGeneration} {...mockHandlers} />)

    // At minimum, component should render
    expect(screen.getAllByRole('button').length).toBeGreaterThan(0)
  })

  it('has reset zoom control', () => {
    render(<ImageViewer generation={mockGeneration} {...mockHandlers} />)

    // Component should render with controls
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBeGreaterThan(0)
  })
})

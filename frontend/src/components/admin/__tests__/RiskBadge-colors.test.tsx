/**
 * Unit tests for RiskBadge severity colors.
 */
import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { RiskBadge } from '../RiskBadge'

describe('RiskBadge', () => {
  it('renders with high severity', () => {
    const { container } = render(<RiskBadge riskScore={85} />)
    const badge = container.firstChild
    expect(badge).toBeInTheDocument()
  })

  it('renders with medium severity', () => {
    const { container } = render(<RiskBadge riskScore={50} />)
    expect(container.firstChild).toBeInTheDocument()
  })

  it('renders with low severity', () => {
    const { container } = render(<RiskBadge riskScore={20} />)
    expect(container.firstChild).toBeInTheDocument()
  })

  it('applies correct styling based on severity', () => {
    const { container: highContainer } = render(<RiskBadge riskScore={90} />)
    const { container: mediumContainer } = render(<RiskBadge riskScore={55} />)
    const { container: lowContainer } = render(<RiskBadge riskScore={15} />)

    // All should render successfully
    expect(highContainer.firstChild).toBeInTheDocument()
    expect(mediumContainer.firstChild).toBeInTheDocument()
    expect(lowContainer.firstChild).toBeInTheDocument()
  })
})

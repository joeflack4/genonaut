import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook } from '@testing-library/react'
import { vi } from 'vitest'
import { createTestQueryClient } from '../../test/query-client'
import { useServeRecommendation } from '../useServeRecommendation'

vi.mock('../../services', () => {
  const recommendationService = {
    markRecommendationServed: vi.fn(),
  }

  return {
    recommendationService,
  }
})

const { recommendationService } = await import('../../services')
const markServedMock = vi.mocked(recommendationService.markRecommendationServed)

describe('useServeRecommendation', () => {
  it('marks a recommendation as served', async () => {
    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    markServedMock.mockResolvedValue({ id: 7 })

    const { result } = renderHook(() => useServeRecommendation(1), { wrapper })

    await result.current.mutateAsync(7)

    expect(markServedMock).toHaveBeenCalledWith(7)
  })
})

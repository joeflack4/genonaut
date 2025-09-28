import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { vi } from 'vitest'
import { useGalleryStats } from '../useGalleryStats'

vi.mock('../../services', () => ({
  unifiedGalleryService: {
    getUnifiedStats: vi.fn(),
  },
}))

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

const { unifiedGalleryService } = await import('../../services')
const mockUnifiedGalleryService = vi.mocked(unifiedGalleryService)

describe('useGalleryStats', () => {
  const wrapper = createWrapper()

  beforeEach(() => {
    mockUnifiedGalleryService.getUnifiedStats.mockReset()
  })

  it('fetches user and total gallery counts', async () => {
    mockUnifiedGalleryService.getUnifiedStats.mockResolvedValueOnce({
      userRegularCount: 50,
      userAutoCount: 30,
      communityRegularCount: 1200,
      communityAutoCount: 800,
    })

    const { result } = renderHook(() => useGalleryStats('1'), { wrapper })

    await waitFor(() => {
      expect(result.current.data).toEqual({
        userGalleryCount: 50,
        userAutoGalleryCount: 30,
        totalGalleryCount: 1200,
        totalAutoGalleryCount: 800,
      })
    })

    expect(mockUnifiedGalleryService.getUnifiedStats).toHaveBeenCalledTimes(1)
    expect(mockUnifiedGalleryService.getUnifiedStats).toHaveBeenCalledWith('1')
  })
})

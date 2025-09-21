import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { useContentStats } from '../useContentStats'

vi.mock('../../services', () => ({
  contentService: {
    listContent: vi.fn(),
  },
}))

const wrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

const { contentService } = await import('../../services')
const mockContentService = vi.mocked(contentService)

describe('useContentStats', () => {
  beforeEach(() => {
    mockContentService.listContent.mockReset()
  })

  it('fetches user and total content counts', async () => {
    // Mock user content response (creator_id=1)
    mockContentService.listContent.mockResolvedValueOnce({
      items: [{ id: 1, title: 'User Content' }],
      total: 1,
      limit: 1,
      skip: 0,
    })

    // Mock total content response
    mockContentService.listContent.mockResolvedValueOnce({
      items: [{ id: 1, title: 'Content 1' }],
      total: 3,
      limit: 1,
      skip: 0,
    })

    const { result } = renderHook(() => useContentStats(1), { wrapper })

    await waitFor(() => {
      expect(result.current.data).toEqual({
        userContentCount: 1,
        totalContentCount: 3,
      })
    })

    expect(mockContentService.listContent).toHaveBeenCalledTimes(2)
    expect(mockContentService.listContent).toHaveBeenNthCalledWith(1, {
      creator_id: 1,
      limit: 1,
    })
    expect(mockContentService.listContent).toHaveBeenNthCalledWith(2, {
      limit: 1,
    })
  })
})
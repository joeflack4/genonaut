import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { vi } from 'vitest'
import { useGalleryStats } from '../useGalleryStats'

vi.mock('../../services', () => ({
  galleryService: {
    listGallery: vi.fn(),
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

const { galleryService } = await import('../../services')
const mockGalleryService = vi.mocked(galleryService)

describe('useGalleryStats', () => {
  const wrapper = createWrapper()

  beforeEach(() => {
    mockGalleryService.listGallery.mockReset()
  })

  it('fetches user and total gallery counts', async () => {
    mockGalleryService.listGallery.mockResolvedValueOnce({
      items: [{ id: 1, title: 'User Gallery Item' }],
      total: 1,
      limit: 1,
      skip: 0,
    })

    mockGalleryService.listGallery.mockResolvedValueOnce({
      items: [{ id: 1, title: 'Gallery Item 1' }],
      total: 3,
      limit: 1,
      skip: 0,
    })

    const { result } = renderHook(() => useGalleryStats(1), { wrapper })

    await waitFor(() => {
      expect(result.current.data).toEqual({
        userGalleryCount: 1,
        totalGalleryCount: 3,
      })
    })

    expect(mockGalleryService.listGallery).toHaveBeenCalledTimes(2)
    expect(mockGalleryService.listGallery).toHaveBeenNthCalledWith(1, {
      creator_id: 1,
      limit: 1,
    })
    expect(mockGalleryService.listGallery).toHaveBeenNthCalledWith(2, {
      limit: 1,
    })
  })
})

import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, vi } from 'vitest'
import { createTestQueryClient } from '../../test/query-client'
import { useGalleryList } from '../useGalleryList'

vi.mock('../../services', () => {
  const listGalleryMock = vi.fn()

  return {
    galleryService: {
      listGallery: listGalleryMock,
    },
  }
})

const { galleryService } = await import('../../services')
const listGalleryMock = vi.mocked(galleryService.listGallery)

describe('useGalleryList', () => {
  beforeEach(() => {
    listGalleryMock.mockReset()
  })

  it('fetches paginated content with provided params', async () => {
    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const response = {
      items: [],
      total: 0,
      limit: 20,
      skip: 0,
    }

    listGalleryMock.mockResolvedValue(response)

    const params = { skip: 0, limit: 20, search: 'abstract' }

    const { result } = renderHook(() => useGalleryList(params), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(listGalleryMock).toHaveBeenCalledWith(params)
    expect(result.current.data).toEqual(response)
  })
})

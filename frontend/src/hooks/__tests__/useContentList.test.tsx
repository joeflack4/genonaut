import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, vi } from 'vitest'
import { createTestQueryClient } from '../../test/query-client'
import { useContentList } from '../useContentList'

vi.mock('../../services', () => {
  const listContentMock = vi.fn()

  return {
    contentService: {
      listContent: listContentMock,
    },
  }
})

const { contentService } = await import('../../services')
const listContentMock = vi.mocked(contentService.listContent)

describe('useContentList', () => {
  beforeEach(() => {
    listContentMock.mockReset()
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

    listContentMock.mockResolvedValue(response)

    const params = { skip: 0, limit: 20, search: 'abstract' }

    const { result } = renderHook(() => useContentList(params), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(listContentMock).toHaveBeenCalledWith(params)
    expect(result.current.data).toEqual(response)
  })
})

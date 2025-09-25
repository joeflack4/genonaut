import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, vi } from 'vitest'
import { createTestQueryClient } from '../../test/query-client'
import { useUserStats } from '../useUserStats'

vi.mock('../../services', () => {
  const userService = {
    getUserStats: vi.fn(),
  }

  return {
    userService,
  }
})

const { userService } = await import('../../services')
const getUserStatsMock = vi.mocked(userService.getUserStats)

describe('useUserStats', () => {
  beforeEach(() => {
    getUserStatsMock.mockReset()
  })

  it('fetches stats for a user', async () => {
    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    getUserStatsMock.mockResolvedValue({
      totalRecommendations: 12,
      servedRecommendations: 5,
      generatedContent: 7,
      lastActiveAt: '2024-01-10T12:00:00Z',
    })

    const { result } = renderHook(() => useUserStats(1), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(getUserStatsMock).toHaveBeenCalledWith("1")
    expect(result.current.data).toMatchObject({
      totalRecommendations: 12,
      servedRecommendations: 5,
    })
  })
})

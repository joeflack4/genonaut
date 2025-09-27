import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, vi } from 'vitest'
import { createTestQueryClient } from '../../test/query-client'
import { useRecommendations } from '../useRecommendations'

vi.mock('../../services', () => {
  const getRecommendationsMock = vi.fn()

  return {
    recommendationService: {
      getUserRecommendations: getRecommendationsMock,
    },
  }
})

const { recommendationService } = await import('../../services')
const getRecommendationsMock = vi.mocked(recommendationService.getUserRecommendations)

describe('useRecommendations', () => {
  beforeEach(() => {
    getRecommendationsMock.mockReset()
  })

  it('fetches recommendations for the given user id', async () => {
    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const recommendations = [
      { id: 1, userId: '121e194b-4caa-4b81-ad4f-86ca3919d5b9', contentId: 42, algorithm: 'collaborative', score: 0.9, servedAt: null, createdAt: '2024-01-01' },
    ]

    getRecommendationsMock.mockResolvedValue(recommendations)

    const { result } = renderHook(() => useRecommendations('121e194b-4caa-4b81-ad4f-86ca3919d5b9'), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(getRecommendationsMock).toHaveBeenCalledWith('121e194b-4caa-4b81-ad4f-86ca3919d5b9')
    expect(result.current.data).toEqual(recommendations)
  })

  it('does not fetch when disabled', async () => {
    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useRecommendations('121e194b-4caa-4b81-ad4f-86ca3919d5b9', false), { wrapper })

    expect(result.current.isLoading).toBe(false)
    expect(getRecommendationsMock).not.toHaveBeenCalled()
  })
})

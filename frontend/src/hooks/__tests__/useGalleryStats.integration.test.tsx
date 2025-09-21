import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { useGalleryStats } from '../useGalleryStats'

// This is an integration test that calls the real API
// It should only run when the backend API is available

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

describe('useGalleryStats integration', () => {
  const shouldSkip =
    process.env.CI === 'true' ||
    (!process.env.VITE_API_BASE_URL?.includes('localhost') &&
      !process.env.VITE_API_BASE_URL?.includes('0.0.0.0'))

  // eslint-disable-next-line vitest/no-conditional-tests
  it.skipIf(shouldSkip)('fetches real gallery stats from API', async () => {
    const { result } = renderHook(() => useGalleryStats(1), { wrapper })

    await waitFor(
      () => {
        expect(result.current.isSuccess).toBe(true)
      },
      { timeout: 10000 }
    )

    expect(result.current.data).toBeDefined()
    expect(result.current.data?.userGalleryCount).toBeGreaterThanOrEqual(0)
    expect(result.current.data?.totalGalleryCount).toBeGreaterThanOrEqual(0)

    expect(result.current.data?.userGalleryCount).toBe(1)
    expect(result.current.data?.totalGalleryCount).toBe(3)
  }, 15000)
})

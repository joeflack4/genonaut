import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { useContentStats } from '../useContentStats'

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

describe('useContentStats integration', () => {
  // Skip this test if we're in CI or the API is not available locally
  const shouldSkip = process.env.CI === 'true' ||
    (!process.env.VITE_API_BASE_URL?.includes('localhost') &&
     !process.env.VITE_API_BASE_URL?.includes('0.0.0.0'))

  // eslint-disable-next-line vitest/no-conditional-tests
  it.skipIf(shouldSkip)('fetches real content stats from API', async () => {
    const { result } = renderHook(() => useContentStats(1), { wrapper })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    }, { timeout: 10000 })

    expect(result.current.data).toBeDefined()
    expect(result.current.data?.userContentCount).toBeGreaterThanOrEqual(0)
    expect(result.current.data?.totalContentCount).toBeGreaterThanOrEqual(0)

    // Based on the current test data, we expect these specific values
    expect(result.current.data?.userContentCount).toBe(1)
    expect(result.current.data?.totalContentCount).toBe(3)
  }, 15000)
})
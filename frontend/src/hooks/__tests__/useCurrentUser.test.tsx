import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { createTestQueryClient } from '../../test/query-client'
import { useCurrentUser } from '../useCurrentUser'

vi.mock('../../services', () => ({
  userService: {
    getCurrentUser: vi.fn(),
  },
}))

const { userService } = await import('../../services')

const mockUser = {
  id: 1,
  name: 'Admin',
  email: 'admin@example.com',
  isActive: true,
}

describe('useCurrentUser', () => {
  it('returns the current user data', async () => {
    vi.mocked(userService.getCurrentUser).mockResolvedValue(mockUser)

    const queryClient = createTestQueryClient()

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useCurrentUser(), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockUser)
    expect(userService.getCurrentUser).toHaveBeenCalledTimes(1)
  })
})

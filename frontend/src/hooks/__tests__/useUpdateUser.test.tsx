import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook } from '@testing-library/react'
import { vi } from 'vitest'
import { currentUserQueryKey } from '../useCurrentUser'
import { useUpdateUser } from '../useUpdateUser'

vi.mock('../../services', () => {
  const userService = {
    updateUser: vi.fn(),
  }

  return {
    userService,
  }
})

const { userService } = await import('../../services')
const updateUserMock = vi.mocked(userService.updateUser)

describe('useUpdateUser', () => {
  it('updates the user and invalidates cache', async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    queryClient.setQueryData(currentUserQueryKey, { id: 1, name: 'Admin' })

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    updateUserMock.mockResolvedValue({ id: 1, name: 'Updated Admin' })

    const { result } = renderHook(() => useUpdateUser(), { wrapper })

    await result.current.mutateAsync({ id: 1, payload: { name: 'Updated Admin' } })

    expect(updateUserMock).toHaveBeenCalledWith(1, { name: 'Updated Admin' })
    expect(queryClient.getQueryState(currentUserQueryKey)?.isInvalidated).toBe(true)
  })
})

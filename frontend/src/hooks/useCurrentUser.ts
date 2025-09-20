import { useQuery } from '@tanstack/react-query'
import { userService } from '../services'
import type { User } from '../types/domain'

export const currentUserQueryKey = ['current-user']

export function useCurrentUser() {
  return useQuery<User>({
    queryKey: currentUserQueryKey,
    queryFn: () => userService.getCurrentUser(),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })
}

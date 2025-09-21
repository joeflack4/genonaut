import { useQuery } from '@tanstack/react-query'
import { userService } from '../services'
import type { UserStats } from '../types/domain'

export const userStatsQueryKey = (userId: number) => ['user-stats', userId]

export function useUserStats(userId: number, enabled = true) {
  return useQuery<UserStats>({
    queryKey: userStatsQueryKey(userId),
    queryFn: () => userService.getUserStats(userId),
    enabled,
  })
}

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { userService } from '../services'
import { currentUserQueryKey } from './useCurrentUser'
import type { ApiUserUpdateRequest } from '../types/api'
import type { User } from '../types/domain'

interface UpdateUserArgs {
  id: number
  payload: ApiUserUpdateRequest
}

export function useUpdateUser() {
  const queryClient = useQueryClient()

  return useMutation<User, unknown, UpdateUserArgs>({
    mutationFn: ({ id, payload }) => userService.updateUser(id, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: currentUserQueryKey })
    },
  })
}

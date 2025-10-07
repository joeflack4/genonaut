import { useQuery } from '@tanstack/react-query'
import { checkpointModelService } from '../services'
import type { CheckpointModel } from '../types/domain'

export const checkpointModelsQueryKey = () => ['checkpoint-models']

export function useCheckpointModels(enabled = true) {
  return useQuery<CheckpointModel[]>({
    queryKey: checkpointModelsQueryKey(),
    queryFn: () => checkpointModelService.getAll(),
    enabled,
  })
}

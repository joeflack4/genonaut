import { useQuery } from '@tanstack/react-query'
import { loraModelService } from '../services'
import type { PaginatedLoraModels } from '../types/domain'
import type { LoraModelQueryParams } from '../services/lora-model-service'

export const loraModelsQueryKey = (params?: LoraModelQueryParams) =>
  ['lora-models', params]

export function useLoraModels(params?: LoraModelQueryParams, enabled = true) {
  return useQuery<PaginatedLoraModels>({
    queryKey: loraModelsQueryKey(params),
    queryFn: () => loraModelService.getPaginated(params),
    enabled,
  })
}

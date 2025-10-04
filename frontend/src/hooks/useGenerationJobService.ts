import { useMemo } from 'react'
import { ApiClient } from '../services/api-client'
import { GenerationJobService } from '../services/generation-job-service'

// Singleton instances to avoid recreating services
let apiClientInstance: ApiClient | null = null
let generationJobServiceInstance: GenerationJobService | null = null

export function useGenerationJobService() {
  return useMemo(() => {
    if (!apiClientInstance) {
      apiClientInstance = new ApiClient()
    }

    if (!generationJobServiceInstance) {
      generationJobServiceInstance = new GenerationJobService(apiClientInstance)
    }

    return {
      createGenerationJob: generationJobServiceInstance.createGenerationJob.bind(generationJobServiceInstance),
      getGenerationJob: generationJobServiceInstance.getGenerationJob.bind(generationJobServiceInstance),
      listGenerationJobs: generationJobServiceInstance.listGenerationJobs.bind(generationJobServiceInstance),
      cancelGenerationJob: generationJobServiceInstance.cancelGenerationJob.bind(generationJobServiceInstance),
      listAvailableModels: generationJobServiceInstance.listAvailableModels.bind(generationJobServiceInstance),
      refreshModels: generationJobServiceInstance.refreshModels.bind(generationJobServiceInstance),
    }
  }, [])
}

import { useMemo } from 'react'
import { ApiClient } from '../services/api-client'
import { ComfyUIService } from '../services/comfyui-service'

// Singleton instances to avoid recreating services
let apiClientInstance: ApiClient | null = null
let comfyUIServiceInstance: ComfyUIService | null = null

export function useComfyUIService() {
  return useMemo(() => {
    if (!apiClientInstance) {
      apiClientInstance = new ApiClient()
    }

    if (!comfyUIServiceInstance) {
      comfyUIServiceInstance = new ComfyUIService(apiClientInstance)
    }

    return {
      createGeneration: comfyUIServiceInstance.createGeneration.bind(comfyUIServiceInstance),
      getGeneration: comfyUIServiceInstance.getGeneration.bind(comfyUIServiceInstance),
      listGenerations: comfyUIServiceInstance.listGenerations.bind(comfyUIServiceInstance),
      cancelGeneration: comfyUIServiceInstance.cancelGeneration.bind(comfyUIServiceInstance),
      listAvailableModels: comfyUIServiceInstance.listAvailableModels.bind(comfyUIServiceInstance),
      refreshModels: comfyUIServiceInstance.refreshModels.bind(comfyUIServiceInstance),
    }
  }, [])
}
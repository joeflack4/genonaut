import { ApiClient } from './api-client'
import type { ApiLoraModel, ApiLoraModelListResponse } from '../types/api'
import type { LoraModel, PaginatedLoraModels } from '../types/domain'

export interface LoraModelQueryParams {
  page?: number
  pageSize?: number
  checkpointId?: string
}

export class LoraModelService {
  private readonly api: ApiClient

  constructor(api: ApiClient) {
    this.api = api
  }

  async getAll(): Promise<LoraModel[]> {
    const response = await this.api.get<ApiLoraModelListResponse>('/api/v1/lora-models/')
    return response.items.map(this.transformModel)
  }

  async getPaginated(params: LoraModelQueryParams = {}): Promise<PaginatedLoraModels> {
    const queryParams = new URLSearchParams()

    if (params.page) queryParams.append('page', params.page.toString())
    if (params.pageSize) queryParams.append('page_size', params.pageSize.toString())
    if (params.checkpointId) queryParams.append('checkpoint_id', params.checkpointId)

    const response = await this.api.get<ApiLoraModelListResponse>(
      `/api/v1/lora-models/?${queryParams.toString()}`
    )

    return {
      items: response.items.map(this.transformModel),
      total: response.total,
      pagination: response.pagination ? {
        page: response.pagination.page,
        pageSize: response.pagination.page_size,
        total: response.pagination.total,
        totalPages: response.pagination.total_pages,
      } : {
        page: 1,
        pageSize: 10,
        total: response.total,
        totalPages: Math.ceil(response.total / 10),
      }
    }
  }

  async getById(id: string): Promise<LoraModel> {
    const apiModel = await this.api.get<ApiLoraModel>(`/api/v1/lora-models/${id}`)
    return this.transformModel(apiModel)
  }

  private transformModel(apiModel: ApiLoraModel): LoraModel {
    return {
      id: apiModel.id,
      path: apiModel.path,
      filename: apiModel.filename,
      name: apiModel.name,
      version: apiModel.version,
      compatibleArchitectures: apiModel.compatible_architectures,
      family: apiModel.family,
      description: apiModel.description,
      rating: apiModel.rating,
      tags: apiModel.tags,
      triggerWords: apiModel.trigger_words,
      optimalCheckpoints: apiModel.optimal_checkpoints,
      modelMetadata: apiModel.model_metadata,
      createdAt: apiModel.created_at,
      updatedAt: apiModel.updated_at,
      isCompatible: apiModel.is_compatible,
      isOptimal: apiModel.is_optimal,
    }
  }
}

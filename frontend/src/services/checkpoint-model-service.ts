import { ApiClient } from './api-client'
import type { ApiCheckpointModel, ApiCheckpointModelListResponse } from '../types/api'
import type { CheckpointModel } from '../types/domain'

export class CheckpointModelService {
  private readonly api: ApiClient

  constructor(api: ApiClient) {
    this.api = api
  }

  async getAll(): Promise<CheckpointModel[]> {
    const response = await this.api.get<ApiCheckpointModelListResponse>('/api/v1/checkpoint-models/')
    return response.items.map(this.transformModel)
  }

  async getById(id: string): Promise<CheckpointModel> {
    const apiModel = await this.api.get<ApiCheckpointModel>(`/api/v1/checkpoint-models/${id}`)
    return this.transformModel(apiModel)
  }

  private transformModel(apiModel: ApiCheckpointModel): CheckpointModel {
    return {
      id: apiModel.id,
      path: apiModel.path,
      filename: apiModel.filename,
      name: apiModel.name,
      version: apiModel.version,
      architecture: apiModel.architecture,
      family: apiModel.family,
      description: apiModel.description,
      rating: apiModel.rating,
      tags: apiModel.tags,
      modelMetadata: apiModel.model_metadata,
      createdAt: apiModel.created_at,
      updatedAt: apiModel.updated_at,
    }
  }
}

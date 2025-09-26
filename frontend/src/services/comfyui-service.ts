import type { ApiClient } from './api-client'

export interface LoraModel {
  name: string
  strength_model: number
  strength_clip: number
}

export interface SamplerParams {
  seed?: number
  steps?: number
  cfg?: number
  sampler_name?: string
  scheduler?: string
  denoise?: number
}

export interface ComfyUIGenerationCreateRequest {
  user_id: string
  prompt: string
  negative_prompt?: string
  checkpoint_model: string
  lora_models?: LoraModel[]
  width?: number
  height?: number
  batch_size?: number
  sampler_params?: SamplerParams
}

export interface ComfyUIGenerationResponse {
  id: number
  user_id: string
  prompt: string
  negative_prompt?: string
  checkpoint_model: string
  lora_models: LoraModel[]
  width: number
  height: number
  batch_size: number
  sampler_params: SamplerParams
  status: string
  comfyui_prompt_id?: string
  output_paths: string[]
  thumbnail_paths: string[]
  created_at: string
  updated_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
  recovery_suggestions?: string[]
}

export interface AvailableModel {
  id: number
  name: string
  type: string
  file_path: string
  description?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ComfyUIGenerationListResponse {
  items: ComfyUIGenerationResponse[]
  pagination: {
    page: number
    page_size: number
    total_count: number
    has_next: boolean
    has_previous: boolean
    next_cursor?: string
    prev_cursor?: string
  }
}

export interface AvailableModelListResponse {
  items: AvailableModel[]
  total: number
}

export interface ComfyUIGenerationListParams {
  user_id?: string
  status?: string
  created_after?: string
  created_before?: string
  page?: number
  page_size?: number
}

export interface ModelListParams {
  model_type?: string
  is_active?: boolean
  search?: string
}

export class ComfyUIService {
  private apiClient: ApiClient

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient
  }

  async createGeneration(
    request: ComfyUIGenerationCreateRequest,
    options?: { signal?: AbortSignal }
  ): Promise<ComfyUIGenerationResponse> {
    return this.apiClient.post<ComfyUIGenerationResponse>('/api/comfyui/generations', request, {
      signal: options?.signal,
    })
  }

  async getGeneration(id: number): Promise<ComfyUIGenerationResponse> {
    return this.apiClient.get<ComfyUIGenerationResponse>(`/api/comfyui/generations/${id}`)
  }

  async listGenerations(params?: ComfyUIGenerationListParams): Promise<ComfyUIGenerationListResponse> {
    const query = new URLSearchParams()
    if (params?.user_id) query.append('user_id', params.user_id)
    if (params?.status) query.append('status', params.status)
    if (params?.created_after) query.append('created_after', params.created_after)
    if (params?.created_before) query.append('created_before', params.created_before)
    if (params?.page) query.append('page', params.page.toString())
    if (params?.page_size) query.append('page_size', params.page_size.toString())

    const queryString = query.toString()
    const url = queryString ? `/api/comfyui/generations?${queryString}` : '/api/comfyui/generations'

    return this.apiClient.get<ComfyUIGenerationListResponse>(url)
  }

  async cancelGeneration(id: number): Promise<{ message: string }> {
    return this.apiClient.delete<{ message: string }>(`/api/comfyui/generations/${id}`)
  }

  async listAvailableModels(params?: ModelListParams): Promise<AvailableModelListResponse> {
    const query = new URLSearchParams()
    if (params?.model_type) query.append('model_type', params.model_type)
    if (params?.is_active !== undefined) query.append('is_active', params.is_active.toString())
    if (params?.search) query.append('search', params.search)

    const queryString = query.toString()
    const url = queryString ? `/api/comfyui/models?${queryString}` : '/api/comfyui/models'

    return this.apiClient.get<AvailableModelListResponse>(url)
  }

  async refreshModels(): Promise<{ message: string }> {
    return this.apiClient.post<{ message: string }>('/api/comfyui/models/refresh')
  }
}

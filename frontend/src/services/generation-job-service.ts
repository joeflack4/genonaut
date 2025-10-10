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

export interface GenerationJobCreateRequest {
  user_id: string
  job_type: 'text' | 'image' | 'video' | 'audio'
  prompt: string
  params?: Record<string, any>
  negative_prompt?: string
  checkpoint_model?: string
  lora_models?: LoraModel[]
  width?: number
  height?: number
  batch_size?: number
  sampler_params?: SamplerParams
}

export interface GenerationJobResponse {
  id: number
  user_id: string
  job_type: 'text' | 'image' | 'video' | 'audio'
  prompt: string
  params: Record<string, any>
  status: 'pending' | 'running' | 'processing' | 'started' | 'completed' | 'failed' | 'cancelled'
  content_id?: number
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
  updated_at: string
  celery_task_id?: string

  // ComfyUI-specific fields
  negative_prompt?: string
  checkpoint_model?: string
  lora_models?: LoraModel[]
  width?: number
  height?: number
  batch_size?: number
  comfyui_prompt_id?: string

  // Backward compatibility: output_paths and thumbnail_paths
  output_paths?: string[]
  thumbnail_paths?: string[]

  // Error recovery suggestions
  recovery_suggestions?: string[]
}

export interface GenerationJobListResponse {
  items: GenerationJobResponse[]
  total: number
  skip: number
  limit: number
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

export interface AvailableModelListResponse {
  items: AvailableModel[]
  total: number
}

export interface GenerationJobListParams {
  user_id?: string
  status?: string
  job_type?: string
  skip?: number
  limit?: number
}

export interface ModelListParams {
  model_type?: string
  is_active?: boolean
  search?: string
}

export class GenerationJobService {
  private apiClient: ApiClient

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient
  }

  async createGenerationJob(
    request: GenerationJobCreateRequest,
    options?: { signal?: AbortSignal }
  ): Promise<GenerationJobResponse> {
    return this.apiClient.post<GenerationJobResponse>('/api/v1/generation-jobs/', request, {
      signal: options?.signal,
    })
  }

  async getGenerationJob(id: number): Promise<GenerationJobResponse> {
    return this.apiClient.get<GenerationJobResponse>(`/api/v1/generation-jobs/${id}`)
  }

  async listGenerationJobs(params?: GenerationJobListParams): Promise<GenerationJobListResponse> {
    const query = new URLSearchParams()
    if (params?.user_id) query.append('user_id', params.user_id)
    if (params?.status) query.append('status', params.status)
    if (params?.job_type) query.append('job_type', params.job_type)
    if (params?.skip !== undefined) query.append('skip', params.skip.toString())
    if (params?.limit !== undefined) query.append('limit', params.limit.toString())

    const queryString = query.toString()
    const url = queryString ? `/api/v1/generation-jobs/?${queryString}` : '/api/v1/generation-jobs/'

    return this.apiClient.get<GenerationJobListResponse>(url)
  }

  async cancelGenerationJob(id: number, reason?: string): Promise<GenerationJobResponse> {
    return this.apiClient.post<GenerationJobResponse>(`/api/v1/generation-jobs/${id}/cancel`, {
      reason,
    })
  }

  async listAvailableModels(params?: ModelListParams): Promise<AvailableModelListResponse> {
    const query = new URLSearchParams()
    if (params?.model_type) query.append('model_type', params.model_type)
    if (params?.is_active !== undefined) query.append('is_active', params.is_active.toString())
    if (params?.search) query.append('search', params.search)

    const queryString = query.toString()
    const url = queryString ? `/api/v1/comfyui/models/?${queryString}` : '/api/v1/comfyui/models/'

    return this.apiClient.get<AvailableModelListResponse>(url)
  }

  async refreshModels(): Promise<{ message: string }> {
    return this.apiClient.post<{ message: string }>('/api/v1/comfyui/models/refresh')
  }
}

import { ApiClient } from './api-client'
import { GalleryService } from './gallery-service'
import { GalleryAutoService } from './gallery-auto-service'
import { UnifiedGalleryService } from './unified-gallery-service'
import { RecommendationService } from './recommendation-service'
import { UserService } from './user-service'
import { ComfyUIService } from './comfyui-service'
import { GenerationJobService } from './generation-job-service'
import { NotificationService } from './notification-service'
import { FlaggedContentService } from './flagged-content-service'
import { CheckpointModelService } from './checkpoint-model-service'
import { LoraModelService } from './lora-model-service'
import { TagService } from './tag-service'
import { searchHistoryService } from './search-history-service'

const apiClient = new ApiClient()

export const userService = new UserService(apiClient)
export const galleryService = new GalleryService(apiClient)
export const galleryAutoService = new GalleryAutoService(apiClient)
export const unifiedGalleryService = new UnifiedGalleryService(apiClient)
export const recommendationService = new RecommendationService(apiClient)
export const comfyUIService = new ComfyUIService(apiClient)
export const generationJobService = new GenerationJobService(apiClient)
export const notificationService = new NotificationService(apiClient)
export const flaggedContentService = new FlaggedContentService(apiClient)
export const checkpointModelService = new CheckpointModelService(apiClient)
export const loraModelService = new LoraModelService(apiClient)
export const tagService = new TagService(apiClient)
export { searchHistoryService }

export type { GalleryListParams } from './gallery-service'
export type { GalleryAutoListParams } from './gallery-auto-service'
export type {
  ComfyUIGenerationCreateRequest,
  ComfyUIGenerationResponse,
  ComfyUIGenerationListParams,
  LoraModel,
  SamplerParams,
  AvailableModel
} from './comfyui-service'
export type {
  GenerationJobCreateRequest,
  GenerationJobResponse,
  GenerationJobListParams
} from './generation-job-service'
export type {
  NotificationResponse,
  NotificationListResponse,
  NotificationListParams
} from './notification-service'
export type {
  TagListParams,
  TagSearchParams,
  TagRateParams,
  TagFavoriteParams,
  TagRatingsParams,
  TagSortOption
} from './tag-service'
export type {
  SearchHistoryItem,
  SearchHistoryListResponse,
  SearchHistoryPaginatedResponse,
  PaginationMetadata,
  DeleteResponse,
  ClearHistoryResponse
} from './search-history-service'

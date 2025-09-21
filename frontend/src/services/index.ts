import { ApiClient } from './api-client'
import { ContentService } from './content-service'
import { RecommendationService } from './recommendation-service'
import { UserService } from './user-service'

const apiClient = new ApiClient()

export const userService = new UserService(apiClient)
export const contentService = new ContentService(apiClient)
export const recommendationService = new RecommendationService(apiClient)

export type { ContentListParams } from './content-service'

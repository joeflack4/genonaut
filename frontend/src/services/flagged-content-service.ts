import { ApiClient } from './api-client'
import type {
  ApiFlaggedContent,
  ApiEnhancedPaginatedResponse,
  ApiScanRequest,
  ApiScanResponse,
  ApiReviewRequest,
  ApiBulkDeleteRequest,
  ApiBulkDeleteResponse,
  ApiFlaggedContentStats,
} from '../types/api'
import type {
  FlaggedContent,
  FlaggedContentFilters,
  EnhancedPaginatedResult,
  ScanRequest,
  ScanResponse,
  ReviewRequest,
  BulkDeleteRequest,
  BulkDeleteResponse,
  FlaggedContentStats,
} from '../types/domain'

export class FlaggedContentService {
  private readonly api: ApiClient

  constructor(api: ApiClient) {
    this.api = api
  }

  /**
   * Scan existing content for flagged words
   */
  async scanContent(request: ScanRequest): Promise<ScanResponse> {
    const apiRequest: ApiScanRequest = {
      content_types: request.contentTypes,
      force_rescan: request.forceRescan,
    }

    const response = await this.api.post<ApiScanResponse>(
      '/api/v1/admin/flagged-content/scan',
      apiRequest
    )

    return {
      itemsScanned: response.items_scanned,
      itemsFlagged: response.items_flagged,
      processingTimeMs: response.processing_time_ms,
    }
  }

  /**
   * List flagged content with filters and pagination
   */
  async listFlaggedContent(
    filters: FlaggedContentFilters = {}
  ): Promise<EnhancedPaginatedResult<FlaggedContent>> {
    const searchParams = new URLSearchParams()

    if (filters.page !== undefined) {
      searchParams.set('page', String(filters.page))
    }

    if (filters.pageSize !== undefined) {
      searchParams.set('page_size', String(filters.pageSize))
    }

    if (filters.sortField) {
      searchParams.set('sort_by', filters.sortField)
    }

    if (filters.sortOrder) {
      searchParams.set('sort_order', filters.sortOrder)
    }

    if (filters.creatorId) {
      searchParams.set('creator_id', filters.creatorId)
    }

    if (filters.contentSource && filters.contentSource !== 'all') {
      searchParams.set('content_source', filters.contentSource)
    }

    if (filters.minRiskScore !== undefined) {
      searchParams.set('min_risk_score', String(filters.minRiskScore))
    }

    if (filters.maxRiskScore !== undefined) {
      searchParams.set('max_risk_score', String(filters.maxRiskScore))
    }

    if (filters.reviewed !== undefined) {
      searchParams.set('reviewed', String(filters.reviewed))
    }

    const query = searchParams.toString()
    const response = await this.api.get<ApiEnhancedPaginatedResponse<ApiFlaggedContent>>(
      `/api/v1/admin/flagged-content/${query ? `?${query}` : ''}`
    )

    return {
      items: response.items.map(this.transformFlaggedContent),
      pagination: {
        page: response.pagination.page,
        pageSize: response.pagination.page_size,
        totalCount: response.pagination.total_count,
        totalPages: response.pagination.total_pages,
        hasNext: response.pagination.has_next,
        hasPrevious: response.pagination.has_previous,
        nextCursor: response.pagination.next_cursor,
        prevCursor: response.pagination.prev_cursor,
      },
    }
  }

  /**
   * Get a single flagged content item by ID
   */
  async getFlaggedContent(id: number): Promise<FlaggedContent> {
    const response = await this.api.get<ApiFlaggedContent>(
      `/api/v1/admin/flagged-content/${id}`
    )
    return this.transformFlaggedContent(response)
  }

  /**
   * Review a flagged content item
   */
  async reviewFlaggedContent(id: number, request: ReviewRequest): Promise<FlaggedContent> {
    const apiRequest: ApiReviewRequest = {
      reviewed: request.reviewed,
      reviewed_by: request.reviewedBy,
      notes: request.notes,
    }

    const response = await this.api.put<ApiFlaggedContent>(
      `/api/v1/admin/flagged-content/${id}/review`,
      apiRequest
    )

    return this.transformFlaggedContent(response)
  }

  /**
   * Delete a flagged content item (and its associated content)
   */
  async deleteFlaggedContent(id: number): Promise<void> {
    await this.api.delete(`/api/v1/admin/flagged-content/${id}`)
  }

  /**
   * Bulk delete multiple flagged content items
   */
  async bulkDeleteFlaggedContent(request: BulkDeleteRequest): Promise<BulkDeleteResponse> {
    const apiRequest: ApiBulkDeleteRequest = {
      ids: request.ids,
    }

    const response = await this.api.post<ApiBulkDeleteResponse>(
      '/api/v1/admin/flagged-content/bulk-delete',
      apiRequest
    )

    return {
      deletedCount: response.deleted_count,
      errors: response.errors,
    }
  }

  /**
   * Get statistics about flagged content
   */
  async getStatistics(): Promise<FlaggedContentStats> {
    const response = await this.api.get<ApiFlaggedContentStats>(
      '/api/v1/admin/flagged-content/statistics/summary'
    )

    return {
      totalFlagged: response.total_flagged,
      unreviewedCount: response.unreviewed_count,
      averageRiskScore: response.average_risk_score,
      highRiskCount: response.high_risk_count,
      bySource: response.by_source,
    }
  }

  /**
   * Transform API flagged content to domain model
   */
  private transformFlaggedContent(item: ApiFlaggedContent): FlaggedContent {
    return {
      id: item.id,
      contentItemId: item.content_item_id,
      contentItemAutoId: item.content_item_auto_id,
      contentSource: item.content_source,
      flaggedText: item.flagged_text,
      flaggedWords: item.flagged_words,
      totalProblemWords: item.total_problem_words,
      totalWords: item.total_words,
      problemPercentage: item.problem_percentage,
      riskScore: item.risk_score,
      creatorId: item.creator_id,
      flaggedAt: item.flagged_at,
      reviewed: item.reviewed,
      reviewedAt: item.reviewed_at,
      reviewedBy: item.reviewed_by,
      notes: item.notes,
    }
  }
}

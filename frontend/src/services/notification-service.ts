import type { ApiClient } from './api-client'

export type KnownNotificationType = 'job_completed' | 'job_failed' | 'job_cancelled' | 'system' | 'recommendation'

export interface NotificationResponse {
  id: number
  user_id: string
  title: string
  message: string
  notification_type: KnownNotificationType | string
  read_status: boolean
  related_job_id?: number
  related_content_id?: number
  created_at: string
  read_at?: string
}

export interface NotificationListResponse {
  items: NotificationResponse[]
  total: number
  skip: number
  limit: number
}

export interface UnreadCountResponse {
  unread_count: number
}

export interface NotificationListParams {
  user_id: string
  skip?: number
  limit?: number
  unread_only?: boolean
  notification_types?: KnownNotificationType[]
}

export class NotificationService {
  private apiClient: ApiClient

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient
  }

  async getNotifications(params: NotificationListParams): Promise<NotificationListResponse> {
    const query = new URLSearchParams()
    query.append('user_id', params.user_id)
    if (params.skip !== undefined) query.append('skip', params.skip.toString())
    if (params.limit !== undefined) query.append('limit', params.limit.toString())
    if (params.unread_only !== undefined) query.append('unread_only', params.unread_only.toString())
    if (params.notification_types?.length) {
      for (const notificationType of params.notification_types) {
        query.append('notification_types', notificationType)
      }
    }

    return this.apiClient.get<NotificationListResponse>(`/api/v1/notifications/?${query.toString()}`)
  }

  async getNotification(id: number, userId: string): Promise<NotificationResponse> {
    return this.apiClient.get<NotificationResponse>(
      `/api/v1/notifications/${id}?user_id=${userId}`
    )
  }

  async getUnreadCount(userId: string): Promise<UnreadCountResponse> {
    return this.apiClient.get<UnreadCountResponse>(
      `/api/v1/notifications/unread/count?user_id=${userId}`
    )
  }

  async markAsRead(id: number, userId: string): Promise<NotificationResponse> {
    return this.apiClient.put<NotificationResponse>(
      `/api/v1/notifications/${id}/read?user_id=${userId}`,
      {}
    )
  }

  async markAsUnread(id: number, userId: string): Promise<NotificationResponse> {
    return this.apiClient.put<NotificationResponse>(
      `/api/v1/notifications/${id}/unread?user_id=${userId}`,
      {}
    )
  }

  async markAllAsRead(userId: string): Promise<{ success: boolean; message: string }> {
    return this.apiClient.put<{ success: boolean; message: string }>(
      `/api/v1/notifications/read-all?user_id=${userId}`,
      {}
    )
  }

  async deleteNotification(id: number, userId: string): Promise<{ success: boolean; message: string }> {
    return this.apiClient.delete<{ success: boolean; message: string }>(
      `/api/v1/notifications/${id}?user_id=${userId}`
    )
  }
}

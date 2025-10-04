import { useMemo } from 'react'
import { ApiClient } from '../services/api-client'
import { NotificationService } from '../services/notification-service'

// Singleton instances to avoid recreating services
let apiClientInstance: ApiClient | null = null
let notificationServiceInstance: NotificationService | null = null

export function useNotificationService() {
  return useMemo(() => {
    if (!apiClientInstance) {
      apiClientInstance = new ApiClient()
    }

    if (!notificationServiceInstance) {
      notificationServiceInstance = new NotificationService(apiClientInstance)
    }

    return {
      getNotifications: notificationServiceInstance.getNotifications.bind(notificationServiceInstance),
      getNotification: notificationServiceInstance.getNotification.bind(notificationServiceInstance),
      getUnreadCount: notificationServiceInstance.getUnreadCount.bind(notificationServiceInstance),
      markAsRead: notificationServiceInstance.markAsRead.bind(notificationServiceInstance),
      markAllAsRead: notificationServiceInstance.markAllAsRead.bind(notificationServiceInstance),
      deleteNotification: notificationServiceInstance.deleteNotification.bind(notificationServiceInstance),
    }
  }, [])
}

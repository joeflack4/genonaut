import { useEffect, useRef } from 'react'
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  Typography,
  Tooltip,
} from '@mui/material'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { useNotificationService } from '../../hooks/useNotificationService'
import { useCurrentUser } from '../../hooks'
import { ADMIN_USER_ID } from '../../constants/config'
import {
  getNotificationTypeLabel,
  isKnownNotificationType,
  mapNotificationTypeToFilter,
} from '../../constants/notifications'
import type { NotificationResponse } from '../../services/notification-service'

export function NotificationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const notificationId = Number(id)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { getNotification, markAsRead, markAsUnread } = useNotificationService()
  const { data: currentUser } = useCurrentUser()

  const userId = currentUser?.id ?? ADMIN_USER_ID
  const hasAutoMarkedRef = useRef(false)

  const notificationQuery = useQuery({
    queryKey: ['notification', userId, notificationId],
    enabled: Number.isFinite(notificationId),
    queryFn: () => getNotification(notificationId, userId),
    staleTime: 30_000,
  })

  const notification = notificationQuery.data

  const markAsReadMutation = useMutation({
    mutationFn: (notificationToMark: NotificationResponse) => markAsRead(notificationToMark.id, userId),
    onSuccess: (updated) => {
      queryClient.setQueryData(['notification', userId, updated.id], updated)
      queryClient.invalidateQueries({ queryKey: ['notifications', userId], exact: false })
    },
  })

  const markAsUnreadMutation = useMutation({
    mutationFn: (notificationId: number) => markAsUnread(notificationId, userId),
    onSuccess: (updated) => {
      hasAutoMarkedRef.current = true
      queryClient.setQueryData(['notification', userId, updated.id], updated)
      queryClient.invalidateQueries({ queryKey: ['notifications', userId], exact: false })
    },
  })

  useEffect(() => {
    if (!notification || notification.read_status || hasAutoMarkedRef.current || markAsReadMutation.isPending) {
      return
    }
    hasAutoMarkedRef.current = true
    markAsReadMutation.mutate(notification)
  }, [notification, markAsReadMutation])

  const handleMarkUnread = async () => {
    if (!notification || markAsUnreadMutation.isPending) {
      return
    }

    try {
      await markAsUnreadMutation.mutateAsync(notification.id)
    } catch (error) {
      console.error('Failed to mark notification as unread:', error)
    }
  }

  const handleBackToList = () => {
    navigate('/notifications')
  }

  const handleViewRelatedContent = (notificationItem: NotificationResponse) => {
    if (notificationItem.related_content_id) {
      navigate(`/view/${notificationItem.related_content_id}`, {
        state: {
          from: 'notifications',
          fallbackPath: '/notifications',
        },
      })
      return
    }

    if (notificationItem.related_job_id) {
      navigate('/generate')
    }
  }

  if (!Number.isFinite(notificationId)) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }} data-testid="notification-detail-invalid">
        <Typography variant="body1" color="error">
          Invalid notification identifier.
        </Typography>
        <Button variant="contained" onClick={handleBackToList} sx={{ mt: 2 }}>
          All notifications
        </Button>
      </Box>
    )
  }

  if (notificationQuery.isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }} data-testid="notification-detail-loading">
        <CircularProgress />
      </Box>
    )
  }

  if (notificationQuery.isError || !notification) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }} data-testid="notification-detail-error">
        <Typography variant="body1" color="error">
          Unable to load this notification.
        </Typography>
        <Button variant="contained" onClick={handleBackToList} sx={{ mt: 2 }}>
          All notifications
        </Button>
      </Box>
    )
  }

  const createdAt = new Date(notification.created_at).toLocaleString()
  const readAt = notification.read_at ? new Date(notification.read_at).toLocaleString() : null
  const normalizedType = mapNotificationTypeToFilter(notification.notification_type)
  const typeLabel = getNotificationTypeLabel(notification.notification_type)
  const showTypeTooltip =
    normalizedType === 'other' && notification.notification_type !== 'other' &&
    !isKnownNotificationType(notification.notification_type)

  const typeChip = (
    <Chip
      label={typeLabel}
      variant="outlined"
      data-testid="notification-detail-type"
    />
  )

  return (
    <Stack spacing={3} data-testid="notification-detail-page-root">
      <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', sm: 'center' }} gap={2}>
        <Typography component="h1" variant="h4" fontWeight={600} data-testid="notification-detail-title">
          {notification.title}
        </Typography>
        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            onClick={handleMarkUnread}
            disabled={!notification.read_status || markAsUnreadMutation.isPending}
            data-testid="notification-detail-mark-unread"
          >
            Mark as unread
          </Button>
          <Button variant="outlined" onClick={handleBackToList} data-testid="notification-detail-back">
            All notifications
          </Button>
        </Stack>
      </Stack>

      <Paper sx={{ p: 3 }} elevation={2} data-testid="notification-detail-card">
        <Stack spacing={2}>
          <Stack direction="row" spacing={1} alignItems="center">
            {showTypeTooltip ? (
              <Tooltip arrow placement="top" title={`Type: ${notification.notification_type}`}>
                {typeChip}
              </Tooltip>
            ) : (
              typeChip
            )}
            <Chip
              label={notification.read_status ? 'Read' : 'Unread'}
              color={notification.read_status ? 'default' : 'warning'}
              data-testid="notification-detail-read-status"
            />
          </Stack>

          <Typography variant="body1" data-testid="notification-detail-message">
            {notification.message}
          </Typography>

          <Stack spacing={0.5}>
            <Typography variant="body2" color="text.secondary" data-testid="notification-detail-created">
              Created: {createdAt}
            </Typography>
            {readAt && (
              <Typography variant="body2" color="text.secondary" data-testid="notification-detail-read-at">
                Read: {readAt}
              </Typography>
            )}
          </Stack>

          {(notification.related_content_id || notification.related_job_id) && (
            <Button
              variant="contained"
              onClick={() => handleViewRelatedContent(notification)}
              data-testid="notification-detail-related-action"
            >
              View related item
            </Button>
          )}
        </Stack>
      </Paper>
    </Stack>
  )
}

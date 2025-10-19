import { useMemo, useState } from 'react'
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  MenuItem,
  OutlinedInput,
  Select,
  Stack,
  Typography,
  Checkbox,
  Tooltip,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import {
  Cancel as CancelIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  MailOutline as MailOutlineIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { useNotificationService } from '../../hooks/useNotificationService'
import { useCurrentUser } from '../../hooks'
import { ADMIN_USER_ID } from '../../constants/config'
import {
  DEFAULT_NOTIFICATION_TYPES,
  KNOWN_NOTIFICATION_TYPES,
  NOTIFICATION_TYPE_LABELS,
  NOTIFICATION_TYPE_OPTIONS,
  getNotificationTypeLabel,
  isKnownNotificationType,
  mapNotificationTypeToFilter,
  type NotificationFilterType,
} from '../../constants/notifications'
import type { KnownNotificationType, NotificationResponse } from '../../services/notification-service'
import type { SelectChangeEvent } from '@mui/material/Select'

function getNotificationIcon(type: string) {
  switch (mapNotificationTypeToFilter(type)) {
    case 'job_completed':
      return <CheckCircleIcon color="success" />
    case 'job_failed':
      return <ErrorIcon color="error" />
    case 'job_cancelled':
      return <CancelIcon color="warning" />
    default:
      return <MailOutlineIcon color="primary" />
  }
}

function createQueryKey(userId: string, typesKey: string) {
  return ['notifications', userId, { types: typesKey }] as const
}

export function NotificationsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { getNotifications, markAsRead, deleteNotification } = useNotificationService()
  const { data: currentUser } = useCurrentUser()

  const userId = currentUser?.id ?? ADMIN_USER_ID

  const [selectedTypes, setSelectedTypes] = useState<NotificationFilterType[]>(DEFAULT_NOTIFICATION_TYPES)
  const [pendingDeleteId, setPendingDeleteId] = useState<number | null>(null)

  const includeOther = selectedTypes.includes('other')
  const selectedKnownTypes = useMemo(
    () => selectedTypes.filter((type): type is KnownNotificationType => type !== 'other'),
    [selectedTypes]
  )

  const shouldFilterServer =
    !includeOther && selectedKnownTypes.length > 0 && selectedKnownTypes.length !== KNOWN_NOTIFICATION_TYPES.length
  const notificationTypesParam = shouldFilterServer ? selectedKnownTypes : undefined

  const sortedTypes = useMemo(
    () => [...selectedTypes].sort(),
    [selectedTypes]
  )
  const typesKey = sortedTypes.join('|') || 'all'

  const notificationsQuery = useQuery({
    queryKey: createQueryKey(userId, typesKey),
    queryFn: () =>
      getNotifications({
        user_id: userId,
        limit: 100,
        notification_types: notificationTypesParam,
      }),
    staleTime: 30_000,
  })

  const notifications = notificationsQuery.data?.items ?? []

  const filteredNotifications = useMemo(
    () =>
      notifications.filter((notification) => {
        const filterType = mapNotificationTypeToFilter(notification.notification_type)
        return selectedTypes.includes(filterType)
      }),
    [notifications, selectedTypes]
  )

  const hasNotifications = filteredNotifications.length > 0

  const invalidateNotifications = () => {
    queryClient.invalidateQueries({ queryKey: ['notifications', userId], exact: false })
  }

  const markAsReadMutation = useMutation({
    mutationFn: (notificationId: number) => markAsRead(notificationId, userId),
    onSuccess: invalidateNotifications,
  })

  const deleteMutation = useMutation({
    mutationFn: (notificationId: number) => deleteNotification(notificationId, userId),
    onSuccess: () => {
      invalidateNotifications()
      setPendingDeleteId(null)
    },
  })

  const handleTypeChange = (event: SelectChangeEvent<NotificationFilterType[]>) => {
    const value = event.target.value
    const nextValue = (typeof value === 'string' ? value.split(',') : value) as NotificationFilterType[]
    const normalizedSelection = nextValue.length === 0 ? DEFAULT_NOTIFICATION_TYPES : nextValue

    setSelectedTypes(normalizedSelection)
    invalidateNotifications()
  }

  const handleNotificationClick = async (notification: NotificationResponse) => {
    if (!notification.read_status && !markAsReadMutation.isPending) {
      try {
        await markAsReadMutation.mutateAsync(notification.id)
      } catch (error) {
        console.error('Failed to mark notification as read:', error)
      }
    }

    navigate(`/notification/${notification.id}`)
  }

  const handleRequestDelete = (event: React.MouseEvent, notificationId: number) => {
    event.stopPropagation()
    setPendingDeleteId(notificationId)
  }

  const handleConfirmDelete = async () => {
    if (pendingDeleteId === null || deleteMutation.isPending) {
      return
    }

    try {
      await deleteMutation.mutateAsync(pendingDeleteId)
    } catch (error) {
      console.error('Failed to delete notification:', error)
    }
  }

  const handleCancelDelete = () => {
    setPendingDeleteId(null)
  }

  return (
    <Stack spacing={3} data-testid="notifications-page-root">
      <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems="flex-start" gap={2}>
        <Box>
          <Typography component="h1" variant="h4" fontWeight={600} gutterBottom data-testid="notifications-page-title">
            Notifications
          </Typography>
          <Typography variant="body2" color="text.secondary" data-testid="notifications-page-subtitle">
            View and manage your latest updates
          </Typography>
        </Box>
        <FormControl sx={{ minWidth: 240 }} size="small">
          <InputLabel id="notification-type-filter-label">Filter by type</InputLabel>
          <Select
            multiple
            value={selectedTypes}
            onChange={handleTypeChange}
            input={<OutlinedInput label="Filter by type" />}
            labelId="notification-type-filter-label"
            renderValue={(selected) =>
              selected.length === DEFAULT_NOTIFICATION_TYPES.length
                ? 'All types'
                : selected.map((type) => NOTIFICATION_TYPE_LABELS[type]).join(', ')
            }
            data-testid="notifications-type-filter"
          >
            {NOTIFICATION_TYPE_OPTIONS.map((option) => (
              <MenuItem key={option.value} value={option.value} data-testid={`notifications-filter-option-${option.value}`}>
                <Checkbox checked={selectedTypes.includes(option.value)} size="small" sx={{ mr: 1 }} />
                <ListItemText primary={option.label} />
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Stack>

      {notificationsQuery.isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }} data-testid="notifications-loading">
          <CircularProgress />
        </Box>
      ) : notificationsQuery.isError ? (
        <Box sx={{ textAlign: 'center', py: 8 }} data-testid="notifications-error">
          <Typography variant="body1" color="error">
            Unable to load notifications right now.
          </Typography>
        </Box>
      ) : !hasNotifications ? (
        <Box sx={{ textAlign: 'center', py: 8 }} data-testid="notifications-empty-state">
          <Typography variant="body1">You do not have any notifications yet.</Typography>
        </Box>
      ) : (
        <List sx={{ width: '100%' }} data-testid="notifications-list">
          {filteredNotifications.map((notification) => {
            const normalizedType = mapNotificationTypeToFilter(notification.notification_type)
            const chipLabel = getNotificationTypeLabel(notification.notification_type)
            const showTypeTooltip =
              normalizedType === 'other' && notification.notification_type !== 'other' &&
              !isKnownNotificationType(notification.notification_type)

            const typeChip = (
              <Chip
                size="small"
                label={chipLabel}
                variant="outlined"
                data-testid={`notifications-type-chip-${notification.id}`}
              />
            )

            return (
              <ListItem
                key={notification.id}
                disablePadding
                secondaryAction={
                  <IconButton
                    edge="end"
                    aria-label="delete notification"
                    onClick={(event) => handleRequestDelete(event, notification.id)}
                    data-testid={`notifications-delete-${notification.id}`}
                  >
                    <DeleteIcon />
                  </IconButton>
                }
              >
                <ListItemButton
                  onClick={() => handleNotificationClick(notification)}
                  data-testid={`notifications-list-item-${notification.id}`}
                  sx={{
                    alignItems: 'flex-start',
                    gap: 2,
                    bgcolor: notification.read_status ? 'transparent' : 'action.hover',
                    '&:hover': {
                      bgcolor: notification.read_status ? 'action.selected' : 'action.focus',
                    },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 36, mt: 0.75 }}>
                    {getNotificationIcon(notification.notification_type)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <Typography variant="subtitle1" fontWeight={notification.read_status ? 500 : 700}>
                          {notification.title}
                        </Typography>
                        {showTypeTooltip ? (
                          <Tooltip
                            arrow
                            placement="top"
                            title={`Type: ${notification.notification_type}`}
                          >
                            {typeChip}
                          </Tooltip>
                        ) : (
                          typeChip
                        )}
                        {!notification.read_status && (
                          <Chip
                            size="small"
                            color="warning"
                            label="Unread"
                            data-testid={`notifications-unread-chip-${notification.id}`}
                          />
                        )}
                      </Stack>
                    }
                    secondary={
                      <Stack spacing={0.75} mt={1}>
                        <Typography
                          variant="body2"
                          component="span"
                          color="text.primary"
                          data-testid={`notifications-message-${notification.id}`}
                        >
                          {notification.message}
                        </Typography>
                        <Typography
                          variant="caption"
                          component="span"
                          color="text.secondary"
                          data-testid={`notifications-created-${notification.id}`}
                        >
                          {new Date(notification.created_at).toLocaleString()}
                        </Typography>
                      </Stack>
                    }
                    primaryTypographyProps={{ component: 'div' }}
                    secondaryTypographyProps={{ component: 'div' }}
                  />
                </ListItemButton>
              </ListItem>
            )
          })}
        </List>
      )}

      <Dialog open={pendingDeleteId !== null} onClose={handleCancelDelete} data-testid="notifications-delete-dialog" disableRestoreFocus>
        <DialogTitle>Delete notification?</DialogTitle>
        <DialogContent>
          <Typography variant="body2">Are you sure you want to delete this notification?</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete} data-testid="notifications-delete-cancel">No</Button>
          <Button
            color="error"
            onClick={handleConfirmDelete}
            disabled={deleteMutation.isPending}
            data-testid="notifications-delete-confirm"
          >
            Yes
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}

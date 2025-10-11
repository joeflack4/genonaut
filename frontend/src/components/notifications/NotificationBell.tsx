import { useState, useEffect } from 'react'
import {
  Badge,
  IconButton,
  Menu,
  MenuItem,
  Typography,
  Box,
  Divider,
  List,
  ListItem,
  ListItemText,
  Button,
  CircularProgress,
  Tooltip,
  Chip,
  ListItemButton,
} from '@mui/material'
import {
  Notifications as NotificationsIcon,
  MailOutline as MailOutlineIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useNotificationService } from '../../hooks/useNotificationService'
import { useCurrentUser } from '../../hooks'
import { ADMIN_USER_ID } from '../../constants/config'
import {
  getNotificationTypeLabel,
  isKnownNotificationType,
  mapNotificationTypeToFilter,
} from '../../constants/notifications'
import type { NotificationResponse } from '../../services/notification-service'

export function NotificationBell() {
  const navigate = useNavigate()
  const { getNotifications, getUnreadCount, markAsRead, markAllAsRead } = useNotificationService()
  const { data: currentUser } = useCurrentUser()

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [notifications, setNotifications] = useState<NotificationResponse[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)

  const userId = currentUser?.id ?? ADMIN_USER_ID

  const open = Boolean(anchorEl)

  useEffect(() => {
    const fetchUnreadCount = async () => {
      try {
        const response = await getUnreadCount(userId)
        setUnreadCount(response.unread_count)
      } catch (err) {
        console.error('Failed to fetch unread count:', err)
      }
    }

    fetchUnreadCount()
    const interval = setInterval(fetchUnreadCount, 30000)

    return () => clearInterval(interval)
  }, [getUnreadCount, userId])

  const handleClick = async (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
    setLoading(true)

    try {
      const response = await getNotifications({
        user_id: userId,
        limit: 10,
        unread_only: false,
      })
      setNotifications(response.items)
    } catch (err) {
      console.error('Failed to fetch notifications:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleNotificationClick = async (notification: NotificationResponse) => {
    if (!notification.read_status) {
      try {
        await markAsRead(notification.id, userId)
        setUnreadCount((prev) => Math.max(0, prev - 1))
        setNotifications((prev) =>
          prev.map((item) =>
            item.id === notification.id
              ? { ...item, read_status: true, read_at: new Date().toISOString() }
              : item
          )
        )
      } catch (err) {
        console.error('Failed to mark notification as read:', err)
      }
    }

    navigate(`/notification/${notification.id}`)
    handleClose()
  }

  const handleMarkAllRead = async () => {
    try {
      await markAllAsRead(userId)
      setUnreadCount(0)
      const response = await getNotifications({
        user_id: userId,
        limit: 10,
        unread_only: false,
      })
      setNotifications(response.items)
    } catch (err) {
      console.error('Failed to mark all as read:', err)
    }
  }

  const handleViewAll = () => {
    navigate('/notifications')
    handleClose()
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'job_completed':
        return <CheckCircleIcon fontSize="small" color="success" />
      case 'job_failed':
        return <ErrorIcon fontSize="small" color="error" />
      case 'job_cancelled':
        return <CancelIcon fontSize="small" color="warning" />
      default:
        return <MailOutlineIcon fontSize="small" />
    }
  }

  return (
    <>
      <Tooltip title="Notifications" enterDelay={1500} arrow>
        <IconButton
          color="inherit"
          onClick={handleClick}
          aria-label="notifications"
          data-testid="notification-bell"
        >
          <Badge badgeContent={unreadCount} color="error">
            <NotificationsIcon />
          </Badge>
        </IconButton>
      </Tooltip>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: {
            width: 360,
            maxHeight: 500,
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ px: 2, py: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">Notifications</Typography>
          {unreadCount > 0 && (
            <Button size="small" onClick={handleMarkAllRead}>
              Mark all read
            </Button>
          )}
        </Box>
        <Divider />

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress size={24} />
          </Box>
        ) : notifications.length === 0 ? (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No notifications
            </Typography>
          </Box>
        ) : (
          <List sx={{ py: 0 }}>
            {notifications.map((notification) => {
              const normalizedType = mapNotificationTypeToFilter(notification.notification_type)
              const typeLabel = getNotificationTypeLabel(notification.notification_type)
              const showTypeTooltip =
                normalizedType === 'other' && notification.notification_type !== 'other' &&
                !isKnownNotificationType(notification.notification_type)
              const typeChip = <Chip size="small" label={typeLabel} variant="outlined" />
              const chipContent = showTypeTooltip ? (
                <Tooltip arrow placement="top" title={`Type: ${notification.notification_type}`}>
                  {typeChip}
                </Tooltip>
              ) : (
                typeChip
              )

              return (
                <ListItem
                  key={notification.id}
                  disablePadding
                  data-testid={`notification-menu-item-${notification.id}`}
                >
                  <ListItemButton
                    onClick={() => handleNotificationClick(notification)}
                    sx={{
                      alignItems: 'flex-start',
                      gap: 1,
                      bgcolor: notification.read_status ? 'transparent' : 'action.hover',
                      '&:hover': {
                        bgcolor: 'action.selected',
                      },
                    }}
                  >
                    <Box sx={{ mr: 1 }}>{getNotificationIcon(notification.notification_type)}</Box>
                    <ListItemText
                      primary={notification.title}
                      secondary={
                        <Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                            {chipContent}
                            {!notification.read_status && <Chip size="small" color="warning" label="Unread" />}
                          </Box>
                          <Typography variant="body2" component="span" sx={{ mb: 0.5 }}>
                            {notification.message}
                          </Typography>
                          <Typography variant="caption" component="span" color="text.secondary">
                            {new Date(notification.created_at).toLocaleString()}
                          </Typography>
                        </Box>
                      }
                      primaryTypographyProps={{ component: 'div', fontWeight: notification.read_status ? 'normal' : 'bold' }}
                      secondaryTypographyProps={{ component: 'div' }}
                    />
                  </ListItemButton>
                </ListItem>
              )
            })}
          </List>
        )}

        <Divider />
        <Box sx={{ px: 2, py: 1, textAlign: 'center' }}>
          <Button fullWidth onClick={handleViewAll}>
            View all notifications
          </Button>
        </Box>
      </Menu>
    </>
  )
}

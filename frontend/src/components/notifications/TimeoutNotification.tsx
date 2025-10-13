import { useEffect, useMemo, useState } from 'react'
import { Alert, AlertTitle, Button, Snackbar, Typography, useTheme } from '@mui/material'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'

import { useTimeoutNotificationContext } from '../../app/providers/timeout'
import { UI_CONFIG } from '../../config/ui'

interface TimeoutNotificationProps {
  severity?: 'error' | 'warning' | 'info' | 'success'
  autoHideDuration?: number | null
  position?: {
    vertical: 'top' | 'bottom'
    horizontal: 'left' | 'center' | 'right'
  }
}

export function TimeoutNotification({
  severity = 'error',
  autoHideDuration,
  position = UI_CONFIG.NOTIFICATIONS.POSITION,
}: TimeoutNotificationProps = {}) {
  const theme = useTheme()
  const { event, dismiss } = useTimeoutNotificationContext()
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (event) {
      setOpen(true)
    }
  }, [event])

  const handleClose = (_event?: unknown, reason?: string) => {
    if (reason === 'clickaway') {
      return
    }
    setOpen(false)
    dismiss()
  }

  const helperText = useMemo(() => {
    if (!event) {
      return ''
    }

    const segments: string[] = []

    if (event.timeoutDuration) {
      segments.push(`Timeout: ${event.timeoutDuration}`)
    }

    const contextPath = event.details?.context?.path ?? event.details?.context?.endpoint
    if (typeof contextPath === 'string' && contextPath.length > 0) {
      segments.push(`Endpoint: ${contextPath}`)
    }

    return segments.length > 0 ? segments.join('. ') + '.' : ''
  }, [event])

  // Determine auto-hide duration
  const effectiveAutoHideDuration = useMemo(() => {
    if (UI_CONFIG.NOTIFICATIONS.DISABLE_AUTO_HIDE) {
      return null
    }
    if (autoHideDuration !== undefined) {
      return autoHideDuration
    }
    return UI_CONFIG.NOTIFICATIONS.AUTO_HIDE_DURATION[severity]
  }, [severity, autoHideDuration])

  return (
    <Snackbar
      open={Boolean(event) && open}
      autoHideDuration={effectiveAutoHideDuration}
      anchorOrigin={position}
      onClose={handleClose}
      data-testid="timeout-notification-snackbar"
    >
      <Alert
        elevation={6}
        variant="filled"
        severity={severity}
        onClose={handleClose}
        icon={severity === 'error' ? <ErrorOutlineIcon /> : undefined}
        data-testid="timeout-notification-alert"
        sx={{
          alignItems: 'flex-start',
          ...(severity === 'error' && {
            backgroundColor: `${theme.palette.background.paper} !important`,
            color: theme.palette.mode === 'dark'
              ? theme.palette.common.white
              : theme.palette.text.primary,
            border: `1px solid ${theme.palette.mode === 'dark' ? '#d32f2f' : '#c62828'}`,
            '& .MuiAlert-icon': {
              color: theme.palette.mode === 'dark' ? '#d32f2f' : '#c62828',
            },
            '& .MuiAlert-message': {
              color: theme.palette.mode === 'dark'
                ? theme.palette.common.white
                : theme.palette.text.primary,
            },
          }),
        }}
        action={
          <Button
            color="inherit"
            size="small"
            onClick={() => handleClose()}
            data-testid="timeout-notification-dismiss"
            sx={{
              color: severity === 'error'
                ? theme.palette.mode === 'dark'
                  ? theme.palette.common.white
                  : theme.palette.text.primary
                : undefined,
            }}
          >
            Dismiss
          </Button>
        }
      >
        <AlertTitle
          data-testid="timeout-notification-title"
          sx={{
            color: severity === 'error'
              ? theme.palette.mode === 'dark'
                ? `${theme.palette.common.white} !important`
                : `${theme.palette.text.primary} !important`
              : undefined,
          }}
        >
          Request timed out
        </AlertTitle>
        <Typography
          variant="body2"
          component="p"
          data-testid="timeout-notification-message"
          sx={{
            color: severity === 'error'
              ? theme.palette.mode === 'dark'
                ? `${theme.palette.common.white} !important`
                : `${theme.palette.text.primary} !important`
              : undefined,
          }}
        >
          {event?.message ?? 'The server stopped responding before the request could finish.'}
        </Typography>
        {helperText ? (
          <Typography
            variant="caption"
            component="p"
            sx={{
              mt: 1,
              color: severity === 'error'
                ? theme.palette.mode === 'dark'
                  ? `${theme.palette.grey[400]} !important`
                  : `${theme.palette.text.secondary} !important`
                : undefined,
            }}
            data-testid="timeout-notification-helper"
          >
            {helperText}
          </Typography>
        ) : null}
      </Alert>
    </Snackbar>
  )
}

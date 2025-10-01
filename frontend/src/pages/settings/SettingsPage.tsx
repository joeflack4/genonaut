import { useEffect, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  CardContent,
  FormControlLabel,
  Stack,
  Switch,
  TextField,
  Typography,
} from '@mui/material'
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined'
import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined'
import { useCurrentUser, useUpdateUser } from '../../hooks'
import { useThemeMode } from '../../app/providers/theme'
import { useUiSettings } from '../../app/providers/ui'

export function SettingsPage() {
  const { data: currentUser } = useCurrentUser()
  const { mutateAsync: updateUser, isPending, isSuccess } = useUpdateUser()
  const { mode, toggleMode } = useThemeMode()
  const { showButtonLabels, toggleButtonLabels } = useUiSettings()

  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')

  useEffect(() => {
    if (!currentUser) {
      return
    }

    setDisplayName(currentUser.name ?? '')
    setEmail(currentUser.email ?? '')
  }, [currentUser])

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!currentUser) return

    await updateUser({
      id: Number(currentUser.id),
      payload: {
        name: displayName,
        email,
      },
    })
  }

  return (
    <Stack spacing={4} component="section" data-testid="settings-page-root">
      <Stack spacing={1} data-testid="settings-header">
        <Typography component="h1" variant="h4" fontWeight={600} gutterBottom data-testid="settings-title">
          Account Settings
        </Typography>
        <Typography variant="body2" color="text.secondary" data-testid="settings-subtitle">
          Update your profile details and adjust application preferences.
        </Typography>
      </Stack>

      <Card component="form" onSubmit={handleSubmit} data-testid="settings-profile-card">
        <CardContent>
          <Stack spacing={3} data-testid="settings-profile-section">
            <Typography variant="h6" component="h2" fontWeight={600} data-testid="settings-profile-title">
              Profile
            </Typography>

            <Stack spacing={2} direction={{ xs: 'column', md: 'row' }} data-testid="settings-profile-fields">
              <TextField
                label="Display name"
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                fullWidth
                inputProps={{ 'data-testid': 'settings-display-name-input' }}
              />
              <TextField
                label="Email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                fullWidth
                inputProps={{ 'data-testid': 'settings-email-input' }}
              />
            </Stack>

            <Stack direction="row" justifyContent="flex-end" data-testid="settings-profile-actions">
              <Button type="submit" variant="contained" disabled={isPending} data-testid="settings-save-button">
                Save changes
              </Button>
            </Stack>

            {isSuccess && <Alert severity="success" data-testid="settings-update-success">Profile updated!</Alert>}
          </Stack>
        </CardContent>
      </Card>

      <Card data-testid="settings-appearance-card">
        <CardContent>
          <Stack spacing={3} data-testid="settings-appearance-section">
            <Typography variant="h6" component="h2" fontWeight={600} data-testid="settings-appearance-title">
              Appearance
            </Typography>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="center" data-testid="settings-appearance-controls">
              <Button
                type="button"
                variant="outlined"
                startIcon={mode === 'dark' ? <LightModeOutlinedIcon /> : <DarkModeOutlinedIcon />}
                onClick={toggleMode}
                data-testid="settings-toggle-theme-button"
              >
                Toggle theme
              </Button>
              <Typography variant="body2" color="text.secondary" data-testid="settings-current-mode">
                Current mode: {mode}
              </Typography>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      <Card data-testid="settings-ui-card">
        <CardContent>
          <Stack spacing={3} data-testid="settings-ui-section">
            <Typography variant="h6" component="h2" fontWeight={600} data-testid="settings-ui-title">
              UI
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={showButtonLabels}
                  onChange={toggleButtonLabels}
                  name="showButtonLabels"
                  inputProps={{ 'data-testid': 'settings-button-labels-switch' }}
                />
              }
              label="Show sidebar and navbar button labels"
              data-testid="settings-button-labels-control"
            />
            <Typography variant="body2" color="text.secondary" data-testid="settings-button-labels-description">
              When disabled, only icons will be shown for navigation buttons. Hover tooltips will still be available.
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  )
}

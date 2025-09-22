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
      id: currentUser.id,
      payload: {
        name: displayName,
        email,
      },
    })
  }

  return (
    <Stack spacing={4} component="section">
      <Stack spacing={1}>
        <Typography component="h1" variant="h4" fontWeight={600} gutterBottom>
          Account Settings
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Update your profile details and adjust application preferences.
        </Typography>
      </Stack>

      <Card component="form" onSubmit={handleSubmit}>
        <CardContent>
          <Stack spacing={3}>
            <Typography variant="h6" component="h2" fontWeight={600}>
              Profile
            </Typography>

            <Stack spacing={2} direction={{ xs: 'column', md: 'row' }}>
              <TextField
                label="Display name"
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                fullWidth
              />
              <TextField
                label="Email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                fullWidth
              />
            </Stack>

            <Stack direction="row" justifyContent="flex-end">
              <Button type="submit" variant="contained" disabled={isPending}>
                Save changes
              </Button>
            </Stack>

            {isSuccess && <Alert severity="success">Profile updated!</Alert>}
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Stack spacing={3}>
            <Typography variant="h6" component="h2" fontWeight={600}>
              Appearance
            </Typography>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="center">
              <Button
                type="button"
                variant="outlined"
                startIcon={mode === 'dark' ? <LightModeOutlinedIcon /> : <DarkModeOutlinedIcon />}
                onClick={toggleMode}
              >
                Toggle theme
              </Button>
              <Typography variant="body2" color="text.secondary">
                Current mode: {mode}
              </Typography>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Stack spacing={3}>
            <Typography variant="h6" component="h2" fontWeight={600}>
              UI
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={showButtonLabels}
                  onChange={toggleButtonLabels}
                  name="showButtonLabels"
                />
              }
              label="Show sidebar and navbar button labels"
            />
            <Typography variant="body2" color="text.secondary">
              When disabled, only icons will be shown for navigation buttons. Hover tooltips will still be available.
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  )
}

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
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import BarChartIcon from '@mui/icons-material/BarChart'
import { useNavigate } from 'react-router-dom'
import { useCurrentUser, useUpdateUser } from '../../hooks'
import { useThemeMode } from '../../app/providers/theme'
import { useUiSettings } from '../../app/providers/ui'

// Define sidebar pages metadata
const sidebarPages = [
  { key: 'dashboard', label: 'Dashboard', canToggle: true },
  { key: 'gallery', label: 'Gallery', canToggle: true },
  { key: 'generate', label: 'Generate', canToggle: true },
  { key: 'tags', label: 'Tag Hierarchy', canToggle: true },
  { key: 'recommendations', label: 'Recommendations', canToggle: true },
  { key: 'flagged-content', label: 'Flagged Content', canToggle: true },
  { key: 'settings', label: 'Account Settings', canToggle: false },
]

const EARLY_FEATURES_STORAGE_KEY = 'early-features'

export function SettingsPage() {
  const navigate = useNavigate()
  const { data: currentUser } = useCurrentUser()
  const { mutateAsync: updateUser, isPending, isSuccess } = useUpdateUser()
  const { mode, toggleMode } = useThemeMode()
  const { showButtonLabels, toggleButtonLabels, visibleSidebarPages, toggleSidebarPage } = useUiSettings()

  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')

  // Early development features state
  const [earlyFeatures, setEarlyFeatures] = useState(() => {
    try {
      const stored = localStorage.getItem(EARLY_FEATURES_STORAGE_KEY)
      return stored ? JSON.parse(stored) : {
        galleryVirtualScrolling: false
      }
    } catch {
      return { galleryVirtualScrolling: false }
    }
  })

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

  const toggleEarlyFeature = (feature: string) => {
    setEarlyFeatures((prev) => {
      const updated = {
        ...prev,
        [feature]: !prev[feature as keyof typeof prev],
      }
      localStorage.setItem(EARLY_FEATURES_STORAGE_KEY, JSON.stringify(updated))
      return updated
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

      <Card data-testid="settings-sidebar-pages-card">
        <CardContent>
          <Stack spacing={3} data-testid="settings-sidebar-pages-section">
            <Typography variant="h6" component="h2" fontWeight={600} data-testid="settings-sidebar-pages-title">
              Show/Hide sidebar pages
            </Typography>

            <Typography variant="body2" color="text.secondary" data-testid="settings-sidebar-pages-description">
              Because some pages are under development, they have been toggled off here. You can toggle them on to see them, and also toggle off other pages--customize the sidebar as you like.
            </Typography>

            <Stack spacing={1.5} data-testid="settings-sidebar-pages-list">
              {sidebarPages.map((page) => (
                <FormControlLabel
                  key={page.key}
                  control={
                    <Switch
                      checked={visibleSidebarPages[page.key] ?? true}
                      onChange={() => toggleSidebarPage(page.key)}
                      name={`sidebarPage-${page.key}`}
                      disabled={!page.canToggle}
                      inputProps={{ 'data-testid': `settings-sidebar-page-${page.key}-switch` }}
                    />
                  }
                  label={page.label}
                  data-testid={`settings-sidebar-page-${page.key}-control`}
                />
              ))}
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      <Card data-testid="settings-search-history-card">
        <CardContent>
          <Stack spacing={3} data-testid="settings-search-history-section">
            <Typography variant="h6" component="h2" fontWeight={600} data-testid="settings-search-history-title">
              Search history
            </Typography>

            <Typography variant="body2" color="text.secondary" data-testid="settings-search-history-description">
              View and manage your search history. You can review past searches, execute them again, or delete them.
            </Typography>

            <Stack direction="row" justifyContent="flex-start">
              <Button
                variant="outlined"
                endIcon={<ArrowForwardIcon />}
                onClick={() => navigate('/settings/search-history')}
                data-testid="settings-search-history-link"
              >
                View search history
              </Button>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      <Card data-testid="settings-analytics-card">
        <CardContent>
          <Stack spacing={3} data-testid="settings-analytics-section">
            <Stack direction="row" spacing={1} alignItems="center">
              <BarChartIcon color="primary" />
              <Typography variant="h6" component="h2" fontWeight={600} data-testid="settings-analytics-title">
                Analytics
              </Typography>
            </Stack>

            <Typography variant="body2" color="text.secondary" data-testid="settings-analytics-description">
              View system analytics including route performance, generation metrics, and tag cardinality statistics. Monitor API endpoint performance, track generation success rates, and analyze content distribution across tags.
            </Typography>

            <Stack direction="row" justifyContent="flex-start">
              <Button
                variant="outlined"
                startIcon={<BarChartIcon />}
                endIcon={<ArrowForwardIcon />}
                onClick={() => navigate('/settings/analytics')}
                data-testid="settings-analytics-link"
              >
                View analytics
              </Button>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      <Card data-testid="settings-early-features-card">
        <CardContent>
          <Stack spacing={3} data-testid="settings-early-features-section">
            <Typography variant="h6" component="h2" fontWeight={600} data-testid="settings-early-features-title">
              Early development features
            </Typography>

            <Typography variant="body2" color="text.secondary" data-testid="settings-early-features-description">
              These features are very early in development and may be buggy.
            </Typography>

            <Stack spacing={1.5} data-testid="settings-early-features-list">
              <FormControlLabel
                control={
                  <Switch
                    checked={earlyFeatures.galleryVirtualScrolling}
                    onChange={() => toggleEarlyFeature('galleryVirtualScrolling')}
                    name="galleryVirtualScrolling"
                    inputProps={{ 'data-testid': 'settings-gallery-virtual-scrolling-switch' }}
                  />
                }
                label="Gallery page: Virtual scrolling"
                data-testid="settings-gallery-virtual-scrolling-control"
              />
            </Stack>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  )
}

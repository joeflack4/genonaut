import { useMemo } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  IconButton,
  Stack,
  Tooltip,
  Typography,
  Chip,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import ImageNotSupportedIcon from '@mui/icons-material/ImageNotSupported'
import { useGalleryItem } from '../../hooks'
import { getImageUrl, getImageUrlFromPath } from '../../utils/image-url'

interface LocationState {
  sourceType?: 'regular' | 'auto'
}

export function DashboardImageView() {
  const params = useParams<{ id: string }>()
  const navigate = useNavigate()
  const location = useLocation()

  const contentId = useMemo(() => {
    const parsed = Number(params.id)
    return Number.isFinite(parsed) ? parsed : undefined
  }, [params.id])

  const state = (location.state as LocationState | undefined) ?? {}

  const { data, isLoading, error } = useGalleryItem(contentId, {
    sourceType: state.sourceType,
  })

  const handleBack = () => {
    if (window.history.length > 1) {
      navigate(-1)
    } else {
      navigate('/dashboard')
    }
  }

  if (!contentId) {
    return (
      <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 2 }} data-testid="dashboard-detail-page">
        <Tooltip title="Back to dashboard">
          <IconButton onClick={handleBack} aria-label="Back" data-testid="dashboard-detail-back-button">
            <ArrowBackIcon />
          </IconButton>
        </Tooltip>
        <Alert severity="error" data-testid="dashboard-detail-error">
          Invalid content identifier. Return to the dashboard to continue browsing.
        </Alert>
      </Box>
    )
  }

  if (isLoading) {
    return (
      <Box
        sx={{ p: 3, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}
        data-testid="dashboard-detail-loading"
      >
        <CircularProgress />
        <Typography variant="body2" color="text.secondary">
          Loading item details…
        </Typography>
      </Box>
    )
  }

  if (error) {
    return (
      <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 2 }} data-testid="dashboard-detail-error-state">
        <Tooltip title="Back to dashboard">
          <IconButton onClick={handleBack} aria-label="Back" data-testid="dashboard-detail-back-button">
            <ArrowBackIcon />
          </IconButton>
        </Tooltip>
        <Alert severity="error" data-testid="dashboard-detail-error">
          Unable to load this dashboard item. It may have been removed or is temporarily unavailable.
        </Alert>
      </Box>
    )
  }

  if (!data) {
    return null
  }

  const imageSource = useMemo(() => {
    const altResPath = data.pathThumbsAltRes
      ? Object.values(data.pathThumbsAltRes).find((value) => Boolean(value)) ?? null
      : null

    const candidates = [altResPath, data.pathThumb, data.imageUrl, data.contentData].filter(
      (value): value is string => Boolean(value)
    )

    if (candidates.length === 0) {
      return null
    }

    for (const candidate of candidates) {
      const resolved = getImageUrlFromPath(candidate)
      if (resolved.startsWith('http://') || resolved.startsWith('https://')) {
        return resolved
      }
    }

    return getImageUrl(data.id)
  }, [data.contentData, data.id, data.imageUrl, data.pathThumb, data.pathThumbsAltRes])
  const createdAt = new Date(data.createdAt)
  const qualityLabel = data.qualityScore !== null && data.qualityScore !== undefined
    ? `${Math.round(data.qualityScore * 100)}%`
    : null

  return (
    <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 3 }} data-testid="dashboard-detail-page">
      <Stack direction="row" spacing={2} alignItems="center">
        <Tooltip title="Back to dashboard">
          <IconButton onClick={handleBack} aria-label="Back" data-testid="dashboard-detail-back-button">
            <ArrowBackIcon />
          </IconButton>
        </Tooltip>
        <Typography variant="h4" fontWeight={600} data-testid="dashboard-detail-title">
          {data.title}
        </Typography>
      </Stack>

      <Card data-testid="dashboard-detail-card">
        <Box
          sx={{
            position: 'relative',
            bgcolor: 'background.default',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: 320,
            borderBottom: (theme) => `1px solid ${theme.palette.divider}`,
          }}
          data-testid="dashboard-detail-media"
        >
          {imageSource ? (
            <Box
              component="img"
              src={imageSource}
              alt={data.title}
              sx={{
                maxWidth: '100%',
                maxHeight: 640,
                objectFit: 'contain',
              }}
              data-testid="dashboard-detail-image"
            />
          ) : (
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                py: 12,
                color: 'text.disabled',
              }}
              data-testid="dashboard-detail-placeholder"
            >
              <ImageNotSupportedIcon sx={{ fontSize: 80 }} />
              <Typography variant="body2" mt={2}>
                No image available
              </Typography>
            </Box>
          )}
        </Box>

        <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Stack direction="row" spacing={2} flexWrap="wrap" alignItems="center">
            <Typography variant="subtitle1" color="text.secondary" data-testid="dashboard-detail-created">
              Created {createdAt.toLocaleString()}
            </Typography>
            <Divider orientation="vertical" flexItem sx={{ display: { xs: 'none', sm: 'block' } }} />
            <Typography variant="subtitle1" color="text.secondary" data-testid="dashboard-detail-source">
              Source: {data.sourceType === 'auto' ? 'Auto-generated' : 'User-generated'}
            </Typography>
            {qualityLabel && (
              <Chip
                label={`Quality ${qualityLabel}`}
                color={data.qualityScore && data.qualityScore > 0.75 ? 'success' : 'default'}
                data-testid="dashboard-detail-quality"
              />
            )}
          </Stack>

          {data.description && (
            <Typography variant="body1" data-testid="dashboard-detail-description">
              {data.description}
            </Typography>
          )}

          <Divider />

          <Stack spacing={1} data-testid="dashboard-detail-metadata">
            <Typography variant="subtitle2" color="text.secondary">
              Creator ID
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace' }} data-testid="dashboard-detail-creator">
              {data.creatorId}
            </Typography>
          </Stack>

          {data.itemMetadata && data.itemMetadata['prompt'] && (
            <Stack spacing={1} data-testid="dashboard-detail-prompt">
              <Typography variant="subtitle2" color="text.secondary">
                Prompt
              </Typography>
              <Typography variant="body2">
                {String(data.itemMetadata['prompt'])}
              </Typography>
            </Stack>
          )}

          {data.tags.length > 0 && (
            <Stack spacing={1} data-testid="dashboard-detail-tags">
              <Typography variant="subtitle2" color="text.secondary">
                Tags
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {data.tags.map((tag) => (
                  <Chip key={tag} label={tag} size="small" />
                ))}
              </Stack>
            </Stack>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}

export default DashboardImageView

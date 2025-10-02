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
  Typography,
  Chip,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import ImageNotSupportedIcon from '@mui/icons-material/ImageNotSupported'
import { useGalleryItem } from '../../hooks'

interface LocationState {
  sourceType?: 'regular' | 'auto'
}

export function GalleryImageView() {
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
      navigate('/gallery')
    }
  }

  if (!contentId) {
    return (
      <Box
        sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 2 }}
        data-testid="gallery-detail-page"
      >
        <IconButton onClick={handleBack} aria-label="Back" data-testid="gallery-detail-back-button">
          <ArrowBackIcon />
        </IconButton>
        <Alert severity="error" data-testid="gallery-detail-error">
          Invalid gallery item identifier. Please return to the gallery and try again.
        </Alert>
      </Box>
    )
  }

  if (isLoading) {
    return (
      <Box
        sx={{ p: 3, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}
        data-testid="gallery-detail-loading"
      >
        <CircularProgress />
        <Typography variant="body2" color="text.secondary">
          Loading image details…
        </Typography>
      </Box>
    )
  }

  if (error) {
    return (
      <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 2 }} data-testid="gallery-detail-error-state">
        <IconButton onClick={handleBack} aria-label="Back" data-testid="gallery-detail-back-button">
          <ArrowBackIcon />
        </IconButton>
        <Alert severity="error" data-testid="gallery-detail-error">
          Unable to load this gallery item. It may have been removed or is currently unavailable.
        </Alert>
      </Box>
    )
  }

  if (!data) {
    return null
  }

  const imageSource = data.pathThumb || data.contentData || data.imageUrl || null
  const createdAt = new Date(data.createdAt)
  const qualityLabel = data.qualityScore !== null && data.qualityScore !== undefined
    ? `${Math.round(data.qualityScore * 100)}%`
    : null

  return (
    <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 3 }} data-testid="gallery-detail-page">
      <Stack direction="row" spacing={2} alignItems="center">
        <IconButton onClick={handleBack} aria-label="Back" data-testid="gallery-detail-back-button">
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4" fontWeight={600} data-testid="gallery-detail-title">
          {data.title}
        </Typography>
      </Stack>

      <Card data-testid="gallery-detail-card">
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
          data-testid="gallery-detail-media"
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
              data-testid="gallery-detail-image"
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
              data-testid="gallery-detail-placeholder"
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
            <Typography variant="subtitle1" color="text.secondary" data-testid="gallery-detail-created">
              Created {createdAt.toLocaleString()}
            </Typography>
            <Divider orientation="vertical" flexItem sx={{ display: { xs: 'none', sm: 'block' } }} />
            <Typography variant="subtitle1" color="text.secondary" data-testid="gallery-detail-source">
              Source: {data.sourceType === 'auto' ? 'Auto-generated' : 'User-generated'}
            </Typography>
            {qualityLabel && (
              <Chip
                label={`Quality ${qualityLabel}`}
                color={data.qualityScore && data.qualityScore > 0.75 ? 'success' : 'default'}
                data-testid="gallery-detail-quality"
              />
            )}
          </Stack>

          {data.description && (
            <Typography variant="body1" data-testid="gallery-detail-description">
              {data.description}
            </Typography>
          )}

          <Divider />

          <Stack spacing={1} data-testid="gallery-detail-metadata">
            <Typography variant="subtitle2" color="text.secondary">
              Creator ID
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace' }} data-testid="gallery-detail-creator">
              {data.creatorId}
            </Typography>
          </Stack>

          {data.itemMetadata && data.itemMetadata['prompt'] && (
            <Stack spacing={1} data-testid="gallery-detail-prompt">
              <Typography variant="subtitle2" color="text.secondary">
                Prompt
              </Typography>
              <Typography variant="body2">
                {String(data.itemMetadata['prompt'])}
              </Typography>
            </Stack>
          )}

          {data.tags.length > 0 && (
            <Stack spacing={1} data-testid="gallery-detail-tags">
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

export default GalleryImageView

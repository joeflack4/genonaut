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
import { resolveImageSourceCandidates } from '../../utils/image-url'

type MetadataRecord = Record<string, unknown>

function getMetadataString(metadata: MetadataRecord | null | undefined, ...keys: string[]): string | null {
  if (!metadata) {
    return null
  }

  for (const key of keys) {
    const value = metadata[key]
    if (typeof value === 'string') {
      const trimmed = value.trim()
      if (trimmed.length > 0) {
        return trimmed
      }
    }
  }

  return null
}

function getMetadataTags(metadata: MetadataRecord | null | undefined): string[] {
  if (!metadata) {
    return []
  }

  const value = metadata['tags']

  if (Array.isArray(value)) {
    return value
      .filter((tag): tag is string => typeof tag === 'string' && tag.trim().length > 0)
  }

  if (typeof value === 'string') {
    const trimmed = value.trim()
    return trimmed.length > 0 ? [trimmed] : []
  }

  return []
}

interface ViewLocationState {
  from?: 'dashboard' | 'gallery' | 'generation' | 'notifications'
  sourceType?: 'regular' | 'auto'
  fallbackPath?: string
}

const DEFAULT_FALLBACK_PATH = '/dashboard'

export function ImageViewPage() {
  const params = useParams<{ id: string }>()
  const navigate = useNavigate()
  const location = useLocation()

  const contentId = useMemo(() => {
    const parsed = Number(params.id)
    return Number.isFinite(parsed) ? parsed : undefined
  }, [params.id])

  const state = (location.state as ViewLocationState | undefined) ?? {}

  const fallbackPath = state.fallbackPath
    ?? (state.from === 'gallery'
      ? '/gallery'
      : state.from === 'generation'
        ? '/generate'
        : DEFAULT_FALLBACK_PATH)

  const { data, isLoading, error } = useGalleryItem(contentId, {
    sourceType: state.sourceType,
  })

  const imageSource = useMemo(() => {
    if (!data) {
      return null
    }

    const altResPath = data.pathThumbsAltRes
      ? Object.values(data.pathThumbsAltRes).find((value) => Boolean(value)) ?? null
      : null

    return resolveImageSourceCandidates(
      data.id,
      altResPath,
      data.pathThumb,
      data.imageUrl,
      data.contentData
    )
  }, [data])

  const handleBack = () => {
    if (window.history.length > 1) {
      navigate(-1)
    } else {
      navigate(fallbackPath)
    }
  }

  if (!contentId) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }} data-testid="image-view-page">
        <Tooltip title="Back">
          <IconButton onClick={handleBack} aria-label="Back" data-testid="image-view-back-button">
            <ArrowBackIcon />
          </IconButton>
        </Tooltip>
        <Alert severity="error" data-testid="image-view-error">
          Invalid content identifier. Return to the list to continue browsing.
        </Alert>
      </Box>
    )
  }

  if (isLoading) {
    return (
      <Box
        sx={{ p: 3, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}
        data-testid="image-view-loading"
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
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }} data-testid="image-view-error-state">
        <Tooltip title="Back">
          <IconButton onClick={handleBack} aria-label="Back" data-testid="image-view-back-button">
            <ArrowBackIcon />
          </IconButton>
        </Tooltip>
        <Alert severity="error" data-testid="image-view-error">
          Unable to load this item. It may have been removed or is temporarily unavailable.
        </Alert>
      </Box>
    )
  }

  if (!data) {
    return null
  }

  const metadata = data.itemMetadata && typeof data.itemMetadata === 'object' ? (data.itemMetadata as MetadataRecord) : null
  const metadataTags = getMetadataTags(metadata)
  const displayTags = data.tags.length > 0 ? data.tags : metadataTags
  const displayPrompt = getMetadataString(metadata, 'prompt', 'raw_prompt') ?? (data.prompt ?? null)
  const displayTitle = getMetadataString(metadata, 'title', 'display_title', 'name') ?? data.title ?? `Content #${data.id}`
  const truncatedTitle = displayTitle.length > 70 ? `${displayTitle.slice(0, 70)}...` : displayTitle
  const creatorDisplayName = data.creatorUsername ?? data.creatorId

  const createdAt = new Date(data.createdAt)
  const qualityLabel = data.qualityScore !== null && data.qualityScore !== undefined
    ? `${Math.round(data.qualityScore * 100)}%`
    : null
  const ratingLabel = qualityLabel ? `Rating ${qualityLabel}` : 'Rating N/A'
  const sourceLabel = data.sourceType === 'auto' ? 'Auto-generated' : 'User-generated'
  const createdAtLabel = createdAt.toLocaleString()

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }} data-testid="image-view-page">
      <Card data-testid="image-view-card">
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
          data-testid="image-view-media"
        >
          <Tooltip title="Back">
            <IconButton
              onClick={handleBack}
              aria-label="Back"
              data-testid="image-view-back-button"
              sx={{
                position: 'absolute',
                top: 16,
                left: 16,
                bgcolor: 'rgba(0, 0, 0, 0.4)',
                color: 'common.white',
                '&:hover': {
                  bgcolor: 'rgba(0, 0, 0, 0.7)',
                },
              }}
            >
              <ArrowBackIcon />
            </IconButton>
          </Tooltip>
          {imageSource ? (
            <Box
              component="img"
              src={imageSource}
              alt={displayTitle}
              sx={{
                maxWidth: '100%',
                maxHeight: 640,
                objectFit: 'contain',
              }}
              data-testid="image-view-image"
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
              data-testid="image-view-placeholder"
            >
              <ImageNotSupportedIcon sx={{ fontSize: 80 }} />
              <Typography variant="body2" mt={2}>
                No image available
              </Typography>
            </Box>
          )}
        </Box>

        <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Typography
            variant="h5"
            fontWeight={600}
            data-testid="image-view-title"
            title={displayTitle}
          >
            {truncatedTitle}
          </Typography>

          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing={1.5}
            alignItems={{ xs: 'flex-start', sm: 'center' }}
            flexWrap="wrap"
            data-testid="image-view-meta-row"
          >
            <Chip
              label={ratingLabel}
              color={qualityLabel && data.qualityScore && data.qualityScore > 0.75 ? 'success' : 'default'}
              data-testid="image-view-quality"
            />
            <Typography variant="body2" color="text.secondary" data-testid="image-view-creator">
              By: {creatorDisplayName}
            </Typography>
            <Typography variant="body2" color="text.secondary" data-testid="image-view-created">
              Created: {createdAtLabel}
            </Typography>
            <Typography variant="body2" color="text.secondary" data-testid="image-view-source">
              {sourceLabel}
            </Typography>
          </Stack>

          {data.description && (
            <Typography variant="body1" data-testid="image-view-description">
              {data.description}
            </Typography>
          )}

          <Divider />

          <Stack spacing={1} data-testid="image-view-tags">
            <Typography variant="subtitle2" color="text.secondary">
              Tags
            </Typography>
            {displayTags.length > 0 ? (
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {displayTags.map((tag) => (
                  <Chip key={tag} label={tag} size="small" />
                ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No tags
              </Typography>
            )}
          </Stack>

          <Divider />

          <Stack spacing={1} data-testid="image-view-prompt">
            <Typography variant="subtitle2" color="text.secondary">
              Prompt
            </Typography>
            <Typography variant="body2">
              {displayPrompt ?? 'No prompt available'}
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  )
}

export default ImageViewPage

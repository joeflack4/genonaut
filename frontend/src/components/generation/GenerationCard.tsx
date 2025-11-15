import { useState, useMemo } from 'react'
import {
  Card,
  CardContent,
  Typography,
  Chip,
  Box,
  IconButton,
  Tooltip,
  Button,
  Stack,
} from '@mui/material'
import {
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Image as ImageIcon,
} from '@mui/icons-material'
import type { GenerationJobResponse } from '../../services/generation-job-service'
import type { ThumbnailResolution, Bookmark } from '../../types/domain'
import { resolveImageSourceCandidates } from '../../utils/image-url'
import { BookmarkButton } from '../bookmarks'

interface GenerationCardProps {
  generation: GenerationJobResponse
  resolution: ThumbnailResolution
  onClick?: () => void
  onDelete: () => void
  showBookmarkButton?: boolean
  userId?: string
  /**
   * Optional pre-fetched bookmark status from batch query
   * If provided, will be passed to BookmarkButton to avoid individual API calls
   */
  bookmarkStatus?: {
    isBookmarked: boolean
    bookmark: Bookmark | undefined
  }
}

const STATUS_COLORS = {
  pending: 'default' as const,
  running: 'primary' as const,
  processing: 'primary' as const,
  completed: 'success' as const,
  failed: 'error' as const,
  cancelled: 'secondary' as const,
}

export function GenerationCard({
  generation,
  resolution,
  onClick,
  onDelete,
  showBookmarkButton = false,
  userId,
  bookmarkStatus
}: GenerationCardProps) {
  const statusColor = STATUS_COLORS[generation.status as keyof typeof STATUS_COLORS] || 'default'
  // Use content_id to construct image URL, fallback to output_paths for backward compatibility
  const hasImages = (generation.content_id !== null && generation.content_id !== undefined) || (generation.output_paths && generation.output_paths.length > 0)

  const thumbnailPath = useMemo(() => {
    return resolveImageSourceCandidates(
      generation.content_id,
      generation.thumbnail_paths?.[0],
      generation.output_paths?.[0]
    )
  }, [generation.content_id, generation.thumbnail_paths, generation.output_paths])

  const [imageError, setImageError] = useState(false)
  const [imageReloadCount, setImageReloadCount] = useState(0)

  const aspectRatioPercentage = useMemo(() => (resolution.height / resolution.width) * 100, [resolution.height, resolution.width])
  const isSmallestResolution = resolution.id === '152x232'

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  const handleDownload = async () => {
    if (!generation.content_id) {
      console.warn('No content_id available for download')
      return
    }

    try {
      const imageUrl = resolveImageSourceCandidates(
        generation.content_id,
        generation.thumbnail_paths?.[0],
        generation.output_paths?.[0]
      )

      if (!imageUrl) {
        console.warn('Could not resolve image URL for download')
        return
      }

      // Fetch the image
      const response = await fetch(imageUrl)
      const blob = await response.blob()

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${generation.prompt.substring(0, 50).replace(/[^a-z0-9]/gi, '_')}_${generation.id}.png`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download image:', error)
    }
  }

  return (
    <Card
      data-testid="generation-card"
      sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      {/* Image or Placeholder */}
      <Box
        onClick={onClick}
        sx={{
          position: 'relative',
          paddingTop: `${aspectRatioPercentage}%`,
          bgcolor: 'background.default',
          cursor: onClick ? 'pointer' : 'default',
          '&:hover': onClick ? {
            opacity: 0.95,
          } : undefined,
        }}
      >
        {thumbnailPath && !imageError ? (
          <Box
            component="img"
            key={imageReloadCount}
            src={thumbnailPath}
            alt={`Generated image: ${truncateText(generation.prompt, 50)}`}
            onError={() => setImageError(true)}
            onLoad={() => setImageError(false)}
            sx={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
              objectFit: 'contain',
              bgcolor: 'background.paper',
            }}
            data-testid="generation-card-image"
          />
        ) : (
          <Box
            sx={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: 'background.paper',
              color: 'text.disabled',
              flexDirection: 'column',
              gap: 1,
            }}
          >
            <ImageIcon sx={{ fontSize: 48 }} data-testid="image-placeholder" />
            {imageError && (
              <Stack spacing={1} alignItems="center">
                <Typography variant="caption" color="error" data-testid="image-error">
                  We couldn't load this preview.
                </Typography>
                <Button
                  size="small"
                  variant="outlined"
                  data-testid="retry-image-button"
                  onClick={() => {
                    setImageError(false)
                    setImageReloadCount(count => count + 1)
                  }}
                >
                  Retry Image
                </Button>
              </Stack>
            )}
          </Box>
        )}

        {/* Status Chip */}
        <Chip
          label={generation.status}
          color={statusColor}
          size="small"
          sx={{
            position: 'absolute',
            top: 8,
            left: 8,
            textTransform: 'capitalize',
          }}
        />
      </Box>

      {/* Content */}
      <CardContent sx={{ flexGrow: 1, p: 0, pt: '5px' }}>
        {/* Date/dimensions row with action buttons */}
        <Box sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 1
        }}>
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
            {new Date(generation.created_at).toLocaleDateString()} •{' '}
            {generation.width} × {generation.height}
          </Typography>

          {!isSmallestResolution && (
            <Box sx={{ display: 'flex', gap: 0.5, ml: 1 }}>
              {showBookmarkButton && userId && generation.content_id && (
                <BookmarkButton
                  contentId={generation.content_id}
                  contentSourceType="items"
                  userId={userId}
                  size="small"
                  bookmarkStatus={bookmarkStatus}
                />
              )}
              {hasImages && (
                <Tooltip title="Download Images">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDownload()
                    }}
                    data-testid="download-images"
                  >
                    <DownloadIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
              <Tooltip title="Delete Generation">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete()
                  }}
                  sx={{ opacity: 0.7, '&:hover': { opacity: 1 } }}
                  data-testid="delete-generation"
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          )}
        </Box>

        <Typography variant="body2" sx={{ mb: 1, minHeight: '2.5em', lineHeight: 1.2 }}>
          {truncateText(generation.prompt, 80)}
        </Typography>

        {generation.checkpoint_model && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
            Model: {truncateText(generation.checkpoint_model, 25)}
          </Typography>
        )}

        {generation.lora_models && generation.lora_models.length > 0 && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: isSmallestResolution ? 0.5 : 0 }}>
            LoRA: {generation.lora_models.map(l => l.name).join(', ').substring(0, 30)}
            {generation.lora_models.map(l => l.name).join(', ').length > 30 ? '...' : ''}
          </Typography>
        )}

        {/* Action buttons for smallest resolution - bottom left */}
        {isSmallestResolution && (
          <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
            {showBookmarkButton && userId && generation.content_id && (
              <BookmarkButton
                contentId={generation.content_id}
                contentSourceType="items"
                userId={userId}
                size="small"
                bookmarkStatus={bookmarkStatus}
              />
            )}
            {hasImages && (
              <Tooltip title="Download Images">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDownload()
                  }}
                  data-testid="download-images"
                >
                  <DownloadIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            <Tooltip title="Delete Generation">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation()
                  onDelete()
                }}
                sx={{ opacity: 0.7, '&:hover': { opacity: 1 } }}
                data-testid="delete-generation"
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        )}
      </CardContent>
    </Card>
  )
}

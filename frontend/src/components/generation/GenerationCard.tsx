import { useState } from 'react'
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Chip,
  Box,
  IconButton,
  Tooltip,
  Button,
  Stack,
} from '@mui/material'
import {
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Image as ImageIcon,
} from '@mui/icons-material'
import { LazyImage } from '../common/LazyImage'
import type { ComfyUIGenerationResponse } from '../../services/comfyui-service'

interface GenerationCardProps {
  generation: ComfyUIGenerationResponse
  onView: () => void
  onDelete: () => void
}

const STATUS_COLORS = {
  pending: 'default' as const,
  processing: 'primary' as const,
  completed: 'success' as const,
  failed: 'error' as const,
  cancelled: 'secondary' as const,
}

export function GenerationCard({ generation, onView, onDelete }: GenerationCardProps) {
  const statusColor = STATUS_COLORS[generation.status as keyof typeof STATUS_COLORS] || 'default'
  const hasImages = generation.output_paths && generation.output_paths.length > 0
  const thumbnailPath = generation.thumbnail_paths?.[0]
  const [imageError, setImageError] = useState(false)
  const [imageReloadCount, setImageReloadCount] = useState(0)

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  return (
    <Card
      data-testid="generation-card"
      sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      {/* Image or Placeholder */}
      <Box sx={{ position: 'relative', paddingTop: '56.25%' }}> {/* 16:9 aspect ratio */}
        {thumbnailPath && !imageError ? (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
            }}
          >
            <LazyImage
              key={imageReloadCount}
              src={thumbnailPath}
              alt={`Generated image: ${truncateText(generation.prompt, 50)}`}
              objectFit="cover"
              onError={() => setImageError(true)}
              onLoad={() => setImageError(false)}
              placeholder={
                <Box
                  sx={{
                    width: '100%',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    bgcolor: 'grey.100',
                    color: 'grey.400',
                  }}
                  data-testid="image-placeholder"
                >
                  <ImageIcon sx={{ fontSize: 48 }} />
                </Box>
              }
            />
          </Box>
        ) : (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: 'grey.100',
              color: 'grey.400',
              flexDirection: 'column',
              gap: 1,
            }}
          >
            <ImageIcon sx={{ fontSize: 48 }} data-testid="image-placeholder" />
            {imageError && (
              <Stack spacing={1} alignItems="center">
                <Typography variant="caption" color="error" data-testid="image-error">
                  We couldn’t load this preview.
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
      <CardContent sx={{ flexGrow: 1, pb: 1 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontSize: '0.75rem' }}>
          {new Date(generation.created_at).toLocaleDateString()} •{' '}
          {generation.width} × {generation.height}
        </Typography>

        <Typography variant="body2" sx={{ mb: 1, minHeight: '2.5em', lineHeight: 1.2 }}>
          {truncateText(generation.prompt, 80)}
        </Typography>

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
          Model: {truncateText(generation.checkpoint_model, 25)}
        </Typography>

        {generation.lora_models.length > 0 && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
            LoRA: {generation.lora_models.map(l => l.name).join(', ').substring(0, 30)}
            {generation.lora_models.map(l => l.name).join(', ').length > 30 ? '...' : ''}
          </Typography>
        )}
      </CardContent>

      {/* Actions */}
      <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
        <Box>
          <Tooltip title="View Details">
            <IconButton size="small" onClick={onView} data-testid="view-details">
              <VisibilityIcon fontSize="small" />
            </IconButton>
          </Tooltip>

          {hasImages && (
            <Tooltip title="Download Images">
              <IconButton
                size="small"
                onClick={() => {
                  // TODO: Implement download functionality
                  console.log('Download:', generation.output_paths)
                }}
                data-testid="download-images"
              >
                <DownloadIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>

        <Box>
          {generation.batch_size > 1 && (
            <Chip
              label={`${generation.output_paths.length}/${generation.batch_size}`}
              size="small"
              variant="outlined"
              sx={{ mr: 1 }}
            />
          )}

          <Tooltip title="Delete Generation">
            <IconButton
              size="small"
              color="error"
              onClick={onDelete}
              sx={{ opacity: 0.7, '&:hover': { opacity: 1 } }}
              data-testid="delete-generation"
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </CardActions>
    </Card>
  )
}

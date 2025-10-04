import { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  IconButton,
  Chip,
  Stack,
  Divider,
  Grid,
  ImageList,
  ImageListItem,
} from '@mui/material'
import {
  Close as CloseIcon,
  Download as DownloadIcon,
  NavigateBefore as NavigateBeforeIcon,
  NavigateNext as NavigateNextIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import type { GenerationJobResponse } from '../../services/generation-job-service'

interface ImageViewerProps {
  generation: GenerationJobResponse
  open: boolean
  onClose: () => void
}

const STATUS_COLORS = {
  pending: 'default' as const,
  running: 'primary' as const,
  processing: 'primary' as const,
  completed: 'success' as const,
  failed: 'error' as const,
  cancelled: 'secondary' as const,
}

export function ImageViewer({ generation, open, onClose }: ImageViewerProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const [zoomLevel, setZoomLevel] = useState(1)

  // Use content_id to construct image URL, fallback to output_paths for backward compatibility
  const imageUrl = generation.content_id ? `/api/v1/images/${generation.content_id}` : generation.output_paths?.[0]
  const hasImages = imageUrl !== undefined || (generation.output_paths && generation.output_paths.length > 0)
  const statusColor = STATUS_COLORS[generation.status as keyof typeof STATUS_COLORS] || 'default'

  const handlePreviousImage = () => {
    if (!generation.output_paths) return
    setCurrentImageIndex((prev) =>
      prev > 0 ? prev - 1 : generation.output_paths.length - 1
    )
    setZoomLevel(1)
  }

  const handleNextImage = () => {
    if (!generation.output_paths) return
    setCurrentImageIndex((prev) =>
      prev < generation.output_paths.length - 1 ? prev + 1 : 0
    )
    setZoomLevel(1)
  }

  const handleZoomIn = () => {
    setZoomLevel((prev) => Math.min(prev * 1.2, 3))
  }

  const handleZoomOut = () => {
    setZoomLevel((prev) => Math.max(prev / 1.2, 0.5))
  }

  const handleDownload = (imageUrl: string, index: number) => {
    const link = document.createElement('a')
    link.href = imageUrl
    link.download = `generation-${generation.id}-${index + 1}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleDownloadAll = () => {
    if (!generation.output_paths) return
    generation.output_paths.forEach((path, index) => {
      handleDownload(path, index)
    })
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { height: '90vh', maxHeight: '90vh' },
      }}
      data-testid="generation-modal"
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box display="flex" alignItems="center" justifyContent="between">
          <Box display="flex" alignItems="center" gap={1} sx={{ flex: 1 }}>
            <Typography variant="h6">Generation #{generation.id}</Typography>
            <Chip
              label={generation.status}
              color={statusColor}
              size="small"
              sx={{ textTransform: 'capitalize' }}
            />
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 0, overflow: 'hidden' }}>
        <Grid container sx={{ height: '100%' }}>
          {/* Image Display */}
          {/* @ts-ignore */}
          <Grid item xs={12} md={8} sx={{ position: 'relative', height: '100%' }}>
            {hasImages ? (
              <Box
                sx={{
                  width: '100%',
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  bgcolor: 'grey.100',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                <Box
                  component="img"
                  src={imageUrl || generation.output_paths?.[currentImageIndex]}
                  alt={`Generated image ${currentImageIndex + 1}`}
                  sx={{
                    maxWidth: '100%',
                    maxHeight: '100%',
                    objectFit: 'contain',
                    transform: `scale(${zoomLevel})`,
                    transition: 'transform 0.2s ease',
                    cursor: zoomLevel > 1 ? 'grab' : 'default',
                  }}
                />

                {/* Image Navigation */}
                {generation.output_paths && generation.output_paths.length > 1 && (
                  <>
                    <IconButton
                      onClick={handlePreviousImage}
                      sx={{
                        position: 'absolute',
                        left: 16,
                        top: '50%',
                        transform: 'translateY(-50%)',
                        bgcolor: 'rgba(0, 0, 0, 0.5)',
                        color: 'white',
                        '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.7)' },
                      }}
                    >
                      <NavigateBeforeIcon />
                    </IconButton>
                    <IconButton
                      onClick={handleNextImage}
                      sx={{
                        position: 'absolute',
                        right: 16,
                        top: '50%',
                        transform: 'translateY(-50%)',
                        bgcolor: 'rgba(0, 0, 0, 0.5)',
                        color: 'white',
                        '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.7)' },
                      }}
                    >
                      <NavigateNextIcon />
                    </IconButton>

                    <Box
                      sx={{
                        position: 'absolute',
                        bottom: 16,
                        left: '50%',
                        transform: 'translateX(-50%)',
                        bgcolor: 'rgba(0, 0, 0, 0.5)',
                        color: 'white',
                        px: 2,
                        py: 1,
                        borderRadius: 1,
                      }}
                    >
                      <Typography variant="body2">
                        {currentImageIndex + 1} / {generation.output_paths?.length || 1}
                      </Typography>
                    </Box>
                  </>
                )}

                {/* Zoom Controls */}
                <Box
                  sx={{
                    position: 'absolute',
                    top: 16,
                    right: 16,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 1,
                  }}
                >
                  <IconButton
                    onClick={handleZoomIn}
                    size="small"
                    sx={{
                      bgcolor: 'rgba(0, 0, 0, 0.5)',
                      color: 'white',
                      '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.7)' },
                    }}
                  >
                    <ZoomInIcon />
                  </IconButton>
                  <IconButton
                    onClick={handleZoomOut}
                    size="small"
                    sx={{
                      bgcolor: 'rgba(0, 0, 0, 0.5)',
                      color: 'white',
                      '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.7)' },
                    }}
                  >
                    <ZoomOutIcon />
                  </IconButton>
                  <IconButton
                    onClick={() => setZoomLevel(1)}
                    size="small"
                    sx={{
                      bgcolor: 'rgba(0, 0, 0, 0.5)',
                      color: 'white',
                      '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.7)' },
                    }}
                  >
                    <RefreshIcon />
                  </IconButton>
                </Box>
              </Box>
            ) : (
              <Box
                display="flex"
                alignItems="center"
                justifyContent="center"
                flexDirection="column"
                sx={{ height: '100%', color: 'text.secondary' }}
              >
                <Typography variant="h6" gutterBottom>
                  No images available
                </Typography>
                <Typography variant="body2">
                  {generation.status === 'completed'
                    ? 'Images may not have been generated successfully'
                    : `Generation is ${generation.status}`}
                </Typography>
              </Box>
            )}
          </Grid>

          {/* Details Panel */}
          {/* @ts-ignore */}
          <Grid item xs={12} md={4} sx={{ borderLeft: 1, borderColor: 'divider' }}>
            <Box sx={{ p: 2, height: '100%', overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom>
                Generation Details
              </Typography>

              <Stack spacing={2}>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Prompt
                  </Typography>
                  <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
                    {generation.prompt}
                  </Typography>
                </Box>

                {generation.negative_prompt && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Negative Prompt
                    </Typography>
                    <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
                      {generation.negative_prompt}
                    </Typography>
                  </Box>
                )}

                <Divider />

                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Model Settings
                  </Typography>
                  <Typography variant="body2">
                    <strong>Checkpoint:</strong> {generation.checkpoint_model}
                  </Typography>
                  {generation.lora_models.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2" gutterBottom>
                        <strong>LoRA Models:</strong>
                      </Typography>
                      {generation.lora_models.map((lora, index) => (
                        <Typography key={index} variant="caption" display="block" sx={{ ml: 1 }}>
                          • {lora.name} (Model: {lora.strength_model}, CLIP: {lora.strength_clip})
                        </Typography>
                      ))}
                    </Box>
                  )}
                </Box>

                <Divider />

                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Generation Settings
                  </Typography>
                  {generation.width && generation.height && (
                    <Typography variant="body2">
                      <strong>Dimensions:</strong> {generation.width} × {generation.height}
                    </Typography>
                  )}
                  {generation.batch_size && (
                    <Typography variant="body2">
                      <strong>Batch Size:</strong> {generation.batch_size}
                    </Typography>
                  )}
                  {generation.params?.sampler_params && (
                    <>
                      {generation.params.sampler_params.steps && (
                        <Typography variant="body2">
                          <strong>Steps:</strong> {generation.params.sampler_params.steps}
                        </Typography>
                      )}
                      {generation.params.sampler_params.cfg && (
                        <Typography variant="body2">
                          <strong>CFG Scale:</strong> {generation.params.sampler_params.cfg}
                        </Typography>
                      )}
                      {generation.params.sampler_params.sampler_name && (
                        <Typography variant="body2">
                          <strong>Sampler:</strong> {generation.params.sampler_params.sampler_name}
                        </Typography>
                      )}
                      {generation.params.sampler_params.scheduler && (
                        <Typography variant="body2">
                          <strong>Scheduler:</strong> {generation.params.sampler_params.scheduler}
                        </Typography>
                      )}
                      {generation.params.sampler_params.seed !== undefined && generation.params.sampler_params.seed !== -1 && (
                        <Typography variant="body2">
                          <strong>Seed:</strong> {generation.params.sampler_params.seed}
                        </Typography>
                      )}
                    </>
                  )}
                </Box>

                <Divider />

                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Timestamps
                  </Typography>
                  <Typography variant="body2">
                    <strong>Created:</strong> {new Date(generation.created_at).toLocaleString()}
                  </Typography>
                  {generation.started_at && (
                    <Typography variant="body2">
                      <strong>Started:</strong> {new Date(generation.started_at).toLocaleString()}
                    </Typography>
                  )}
                  {generation.completed_at && (
                    <Typography variant="body2">
                      <strong>Completed:</strong> {new Date(generation.completed_at).toLocaleString()}
                    </Typography>
                  )}
                </Box>

                {generation.error_message && (
                  <>
                    <Divider />
                    <Box>
                      <Typography variant="subtitle2" gutterBottom color="error">
                        Error Message
                      </Typography>
                      <Typography variant="body2" color="error">
                        {generation.error_message}
                      </Typography>
                    </Box>
                  </>
                )}
              </Stack>
            </Box>
          </Grid>
        </Grid>

        {/* Thumbnail Strip */}
        {hasImages && generation.output_paths && generation.output_paths.length > 1 && (
          <Box
            sx={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              bgcolor: 'background.paper',
              borderTop: 1,
              borderColor: 'divider',
              p: 1,
            }}
          >
            <ImageList
              sx={{
                gridAutoFlow: 'column',
                gridTemplateColumns: 'repeat(auto-fill, minmax(60px, 1fr)) !important',
                gridAutoColumns: 'minmax(60px, 1fr)',
              }}
              cols={generation.output_paths.length}
              rowHeight={60}
            >
              {generation.output_paths.map((path, index) => (
                <ImageListItem
                  key={index}
                  sx={{
                    cursor: 'pointer',
                    border: currentImageIndex === index ? 2 : 1,
                    borderColor: currentImageIndex === index ? 'primary.main' : 'divider',
                  }}
                  onClick={() => {
                    setCurrentImageIndex(index)
                    setZoomLevel(1)
                  }}
                >
                  <img
                    src={path}
                    alt={`Thumbnail ${index + 1}`}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                    }}
                  />
                </ImageListItem>
              ))}
            </ImageList>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        {hasImages && generation.output_paths && generation.output_paths.length > 0 && (
          <>
            <Button
              startIcon={<DownloadIcon />}
              onClick={() => handleDownload(generation.output_paths![currentImageIndex], currentImageIndex)}
            >
              Download Current
            </Button>
            {generation.output_paths.length > 1 && (
              <Button
                startIcon={<DownloadIcon />}
                onClick={handleDownloadAll}
              >
                Download All
              </Button>
            )}
          </>
        )}
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  )
}

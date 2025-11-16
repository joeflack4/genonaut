import { useMemo, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import type { SelectChangeEvent } from '@mui/material/Select'
import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Snackbar,
  Stack,
  Tooltip,
  Typography,
  Chip,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import ImageNotSupportedIcon from '@mui/icons-material/ImageNotSupported'
import DeleteIcon from '@mui/icons-material/Delete'
import { useGalleryItem, useTags, useCurrentUser, useDeleteContent } from '../../hooks'
import { BookmarkButton } from '../../components/bookmarks'
import { DeleteContentDialog } from '../../components/dialogs'
import { resolveImageSourceCandidates } from '../../utils/image-url'

type MetadataRecord = Record<string, unknown>

type TagSortOption = 'name-asc' | 'name-desc' | 'rating-asc' | 'rating-desc'

const tagSortOptions: Array<{ value: TagSortOption; label: string }> = [
  { value: 'name-asc', label: 'Name (A-Z)' },
  { value: 'name-desc', label: 'Name (Z-A)' },
  { value: 'rating-asc', label: 'Rating (Low to High)' },
  { value: 'rating-desc', label: 'Rating (High to Low)' },
]

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
    const filtered = value
      .filter((tag): tag is string => typeof tag === 'string' && tag.trim().length > 0)
    // Deduplicate tags as defensive safeguard
    return Array.from(new Set(filtered))
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
  const { data: currentUser } = useCurrentUser()

  // Delete functionality state
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showSuccessSnackbar, setShowSuccessSnackbar] = useState(false)
  const [showErrorSnackbar, setShowErrorSnackbar] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string>('')

  // Delete mutation hook
  const { mutate: deleteContent, isPending: isDeleting } = useDeleteContent()

  // Tag sorting state - persisted to localStorage (separate from gallery page)
  const [tagSortOption, setTagSortOption] = useState<TagSortOption>(() => {
    const saved = localStorage.getItem('viewPageTagSortPreference')
    return (saved as TagSortOption) || 'name-asc'
  })

  // Persist sort preference to localStorage
  const handleSortChange = (e: SelectChangeEvent<TagSortOption>) => {
    const newValue = e.target.value as TagSortOption
    setTagSortOption(newValue)
    localStorage.setItem('viewPageTagSortPreference', newValue)
  }

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

  // Fetch all tags for enrichment (with ratings) - React Query caches this
  const { data: allTagsData } = useTags({ page: 1, page_size: 100 })

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

  // Enrich tags with rating data and sort - MUST be before early returns to satisfy Rules of Hooks
  const sortedTags = useMemo(() => {
    if (!data) {
      return []
    }

    const metadata = data.itemMetadata && typeof data.itemMetadata === 'object' ? (data.itemMetadata as MetadataRecord) : null
    const metadataTags = getMetadataTags(metadata)
    const displayTags = data.tags.length > 0 ? data.tags : metadataTags

    if (!displayTags || displayTags.length === 0) {
      return []
    }

    // Create map of tag names to tag objects
    const tagMap = new Map(
      (allTagsData?.items || []).map(tag => [tag.name, tag])
    )

    // Enrich display tags with full tag objects
    const enrichedTags = displayTags
      .map(tagName => ({
        name: tagName,
        averageRating: tagMap.get(tagName)?.average_rating ?? null,
      }))

    // Sort based on selected option
    const sorted = [...enrichedTags]
    switch (tagSortOption) {
      case 'name-asc':
        sorted.sort((a, b) => a.name.localeCompare(b.name))
        break
      case 'name-desc':
        sorted.sort((a, b) => b.name.localeCompare(a.name))
        break
      case 'rating-asc':
        sorted.sort((a, b) => {
          const ratingA = a.averageRating ?? -Infinity
          const ratingB = b.averageRating ?? -Infinity
          return ratingA - ratingB
        })
        break
      case 'rating-desc':
        sorted.sort((a, b) => {
          const ratingA = a.averageRating ?? -Infinity
          const ratingB = b.averageRating ?? -Infinity
          return ratingB - ratingA
        })
        break
    }

    return sorted.map(t => t.name)
  }, [data, allTagsData, tagSortOption])

  const handleBack = () => {
    if (window.history.length > 1) {
      navigate(-1)
    } else {
      navigate(fallbackPath)
    }
  }

  /**
   * Opens the delete confirmation dialog
   */
  const handleDelete = () => {
    setShowDeleteDialog(true)
  }

  /**
   * Handles the actual content deletion after confirmation
   * Navigates to gallery on success, shows error on failure
   */
  const handleConfirmDelete = () => {
    if (!contentId) {
      return
    }

    deleteContent(
      {
        contentId,
        sourceType: data?.sourceType,
      },
      {
        onSuccess: () => {
          setShowSuccessSnackbar(true)
          // Navigate to gallery after a short delay to show the success message
          setTimeout(() => {
            navigate('/gallery')
          }, 1000)
        },
        onError: (error) => {
          setErrorMessage(error.message || 'Failed to delete content. Please try again.')
          setShowErrorSnackbar(true)
        },
      }
    )
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
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
            <Typography
              variant="h5"
              fontWeight={600}
              data-testid="image-view-title"
              title={displayTitle}
              sx={{ flexGrow: 1 }}
            >
              {truncatedTitle}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {currentUser && contentId !== undefined && (
                <BookmarkButton
                  contentId={contentId}
                  contentSourceType={data.sourceType === 'auto' ? 'auto' : 'items'}
                  userId={currentUser.id}
                  size="medium"
                />
              )}
              <Tooltip title={isDeleting ? "Deleting..." : "Delete Content"}>
                <span>
                  <IconButton
                    onClick={handleDelete}
                    disabled={isDeleting}
                    aria-label="Delete content"
                    data-testid="delete-content-button"
                    sx={{
                      color: 'text.secondary',
                      '&:hover': {
                        color: 'error.main',
                      },
                      '&.Mui-disabled': {
                        color: 'text.disabled',
                      },
                    }}
                  >
                    <DeleteIcon />
                  </IconButton>
                </span>
              </Tooltip>
            </Box>
          </Box>

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
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Tags
              </Typography>
              {displayTags.length > 0 && (
                <FormControl size="small" sx={{ minWidth: 140 }}>
                  <InputLabel id="image-view-tag-sort-label" sx={{ fontSize: '0.875rem' }}>Sort</InputLabel>
                  <Select
                    labelId="image-view-tag-sort-label"
                    value={tagSortOption}
                    label="Sort"
                    onChange={handleSortChange}
                    data-testid="image-view-tag-sort-select"
                    sx={{ fontSize: '0.875rem' }}
                  >
                    {tagSortOptions.map((option) => (
                      <MenuItem
                        key={option.value}
                        value={option.value}
                        data-testid={`image-view-tag-sort-option-${option.value}`}
                        sx={{ fontSize: '0.875rem' }}
                      >
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            </Box>
            {sortedTags.length > 0 ? (
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {sortedTags.map((tag) => (
                  <Chip
                    key={tag}
                    label={tag}
                    size="small"
                    clickable
                    onClick={() => navigate(`/tags/${tag}`)}
                    data-testid={`image-view-tag-${tag}`}
                  />
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

      {/* Delete Confirmation Dialog */}
      {contentId !== undefined && (
        <DeleteContentDialog
          open={showDeleteDialog}
          onClose={() => setShowDeleteDialog(false)}
          onConfirm={handleConfirmDelete}
          contentId={contentId}
        />
      )}

      {/* Success Snackbar */}
      <Snackbar
        open={showSuccessSnackbar}
        autoHideDuration={4000}
        onClose={() => setShowSuccessSnackbar(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setShowSuccessSnackbar(false)}
          severity="success"
          variant="filled"
          sx={{ width: '100%' }}
        >
          Content deleted successfully
        </Alert>
      </Snackbar>

      {/* Error Snackbar */}
      <Snackbar
        open={showErrorSnackbar}
        autoHideDuration={6000}
        onClose={() => setShowErrorSnackbar(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setShowErrorSnackbar(false)}
          severity="error"
          variant="filled"
          sx={{ width: '100%' }}
        >
          {errorMessage}
        </Alert>
      </Snackbar>
    </Box>
  )
}

export default ImageViewPage

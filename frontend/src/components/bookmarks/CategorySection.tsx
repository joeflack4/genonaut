import { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  IconButton,
  Tooltip,
  Paper,
} from '@mui/material'
import PublicIcon from '@mui/icons-material/Public'
import PublicOffIcon from '@mui/icons-material/PublicOff'
import EditIcon from '@mui/icons-material/Edit'
import { GridView } from '../gallery/GridView'
import { ImageGridCell } from '../gallery/ImageGridCell'
import { MoreGridCell } from './MoreGridCell'
import type { BookmarkCategory, BookmarkWithContent, GalleryItem, ThumbnailResolution } from '../../types/domain'
import { useDebounce } from '../../hooks/useDebounce'

export interface CategorySectionProps {
  category: BookmarkCategory
  bookmarks: BookmarkWithContent[]
  resolution: ThumbnailResolution
  isLoading?: boolean
  itemsPerPage?: number
  onPublicToggle?: (categoryId: string, isPublic: boolean) => void
  onEditCategory?: (category: BookmarkCategory) => void
  onItemClick?: (item: GalleryItem) => void
  dataTestId?: string
}

/**
 * CategorySection - Displays a category header with toolbar and grid of bookmarks
 *
 * Features:
 * - Category name and description
 * - Public/private toggle with debounce
 * - Edit button
 * - Grid of bookmarks
 * - "More..." cell to navigate to full category view
 */
export function CategorySection({
  category,
  bookmarks,
  resolution,
  isLoading = false,
  itemsPerPage = 15,
  onPublicToggle,
  onEditCategory,
  onItemClick,
  dataTestId = `category-section-${category.id}`,
}: CategorySectionProps) {
  const navigate = useNavigate()
  const [isPublicState, setIsPublicState] = useState(category.isPublic)

  // Sync local state when category prop changes (from refetch)
  useEffect(() => {
    setIsPublicState(category.isPublic)
  }, [category.isPublic])

  // Debounced public toggle (500ms)
  const debouncedPublicToggle = useDebounce((newValue: boolean) => {
    if (onPublicToggle) {
      onPublicToggle(category.id, newValue)
    }
  }, 500)

  const handlePublicToggle = useCallback(() => {
    const newValue = !isPublicState
    setIsPublicState(newValue)
    debouncedPublicToggle(newValue)
  }, [isPublicState, debouncedPublicToggle])

  const handleEdit = useCallback(() => {
    if (onEditCategory) {
      onEditCategory(category)
    }
  }, [category, onEditCategory])

  const handleMoreClick = useCallback(() => {
    navigate(`/bookmarks/${category.id}`)
  }, [category.id, navigate])

  // Transform bookmarks to GalleryItems for GridView
  const galleryItems: GalleryItem[] = bookmarks.map((bm) => bm.content!).filter(Boolean)

  // Determine if we need to show "More..." cell
  const hasMore = bookmarks.length >= itemsPerPage
  const displayItems = hasMore ? galleryItems.slice(0, itemsPerPage) : galleryItems

  return (
    <Paper
      elevation={1}
      sx={{ p: 3, mb: 3 }}
      data-testid={dataTestId}
    >
      {/* Header with title and toolbar */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          mb: 2,
        }}
        data-testid={`${dataTestId}-header`}
      >
        <Box
          component="button"
          sx={{
            flex: 1,
            cursor: 'pointer',
            textAlign: 'left',
            border: 'none',
            background: 'transparent',
            padding: 0,
            color: 'text.primary',
            '&:hover': {
              opacity: 0.7,
            },
            '&:focus-visible': {
              outline: '2px solid',
              outlineColor: 'primary.main',
              outlineOffset: '2px',
              borderRadius: 1,
            },
          }}
          onClick={handleMoreClick}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              handleMoreClick()
            }
          }}
          tabIndex={0}
          aria-label={`View all bookmarks in ${category.name} category`}
          data-testid={`${dataTestId}-title-section`}
        >
          <Typography
            variant="h5"
            component="h2"
            gutterBottom
            color="inherit"
            data-testid={`${dataTestId}-name`}
          >
            {category.name}
          </Typography>
          {category.description && (
            <Typography
              variant="body2"
              color="text.secondary"
              data-testid={`${dataTestId}-description`}
            >
              {category.description}
            </Typography>
          )}
        </Box>

        {/* Toolbar */}
        <Box
          sx={{ display: 'flex', gap: 0.5, ml: 2 }}
          data-testid={`${dataTestId}-toolbar`}
        >
          {/* Public/Private Toggle */}
          <Tooltip
            title={isPublicState ? 'Currently: Public - Click to make private' : 'Currently: Private - Click to make public'}
            arrow
            data-testid={`${dataTestId}-public-tooltip`}
          >
            <IconButton
              onClick={handlePublicToggle}
              size="small"
              color={isPublicState ? 'primary' : 'default'}
              data-testid={`${dataTestId}-public-toggle`}
              aria-label={isPublicState ? 'Make category private' : 'Make category public'}
            >
              {isPublicState ? <PublicIcon /> : <PublicOffIcon />}
            </IconButton>
          </Tooltip>

          {/* Edit Button - Hidden for Uncategorized */}
          {category.name !== 'Uncategorized' && (
            <Tooltip
              title="Edit category"
              arrow
              data-testid={`${dataTestId}-edit-tooltip`}
            >
              <IconButton
                onClick={handleEdit}
                size="small"
                data-testid={`${dataTestId}-edit-button`}
                aria-label="Edit category"
              >
                <EditIcon />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>

      {/* Grid of bookmarks */}
      <Box data-testid={`${dataTestId}-grid-container`}>
        {isLoading ? (
          <GridView
            items={[]}
            resolution={resolution}
            isLoading={true}
            loadingPlaceholderCount={itemsPerPage}
            dataTestId={`${dataTestId}-grid`}
          />
        ) : bookmarks.length === 0 ? (
          <Typography
            variant="body2"
            color="text.secondary"
            data-testid={`${dataTestId}-empty`}
          >
            0 bookmarks in category.
          </Typography>
        ) : (
          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: `repeat(auto-fill, minmax(${resolution.width}px, 1fr))`,
              alignItems: 'flex-start',
            }}
            data-testid={`${dataTestId}-grid`}
          >
            {displayItems.map((item) => (
              <ImageGridCell
                key={item.id}
                item={item}
                resolution={resolution}
                onClick={onItemClick}
                dataTestId={`${dataTestId}-item-${item.id}`}
              />
            ))}
            {hasMore && (
              <MoreGridCell
                resolution={resolution}
                onClick={handleMoreClick}
                dataTestId={`${dataTestId}-more-cell`}
              />
            )}
          </Box>
        )}
      </Box>
    </Paper>
  )
}

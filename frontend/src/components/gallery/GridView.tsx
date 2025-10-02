import { useMemo } from 'react'
import { Box, Skeleton, Typography } from '@mui/material'
import type { GalleryItem, ThumbnailResolution } from '../../types/domain'
import { GRID_COLUMN_BREAKPOINTS } from '../../constants/gallery'
import { ImageGridCell } from './ImageGridCell'

export interface GridViewProps {
  items: GalleryItem[]
  resolution: ThumbnailResolution
  isLoading?: boolean
  onItemClick?: (item: GalleryItem) => void
  emptyMessage?: string
  loadingPlaceholderCount?: number
  dataTestId?: string
}

const DEFAULT_LOADING_PLACEHOLDERS = 6

export function GridView({
  items,
  resolution,
  isLoading = false,
  onItemClick,
  emptyMessage = 'No gallery items found. Try adjusting your filters.',
  loadingPlaceholderCount = DEFAULT_LOADING_PLACEHOLDERS,
  dataTestId = 'gallery-grid-view',
}: GridViewProps) {
  const aspectRatioPercentage = useMemo(
    () => (resolution.height / resolution.width) * 100,
    [resolution.height, resolution.width]
  )

  const gridTemplateColumns = useMemo(
    () => ({
      xs: `repeat(${GRID_COLUMN_BREAKPOINTS.xs}, minmax(0, 1fr))`,
      sm: `repeat(${GRID_COLUMN_BREAKPOINTS.sm}, minmax(0, 1fr))`,
      md: `repeat(${GRID_COLUMN_BREAKPOINTS.md}, minmax(0, 1fr))`,
      lg: `repeat(${GRID_COLUMN_BREAKPOINTS.lg}, minmax(0, 1fr))`,
      xl: `repeat(${GRID_COLUMN_BREAKPOINTS.xl}, minmax(0, 1fr))`,
    }),
    []
  )

  return (
    <Box
      sx={{
        display: 'grid',
        gap: 2,
        gridTemplateColumns,
        alignItems: 'flex-start',
      }}
      data-testid={dataTestId}
    >
      {isLoading
        ? Array.from({ length: loadingPlaceholderCount }).map((_, index) => (
            <Box key={`gallery-grid-skeleton-${index}`} data-testid={`gallery-grid-skeleton-${index}`}>
              <Box
                sx={{
                  position: 'relative',
                  width: '100%',
                  pt: `${aspectRatioPercentage}%`,
                  borderRadius: 2,
                  overflow: 'hidden',
                }}
              >
                <Skeleton
                  variant="rectangular"
                  animation="wave"
                  sx={{
                    position: 'absolute',
                    inset: 0,
                    width: '100%',
                    height: '100%',
                  }}
                />
              </Box>
              <Skeleton variant="text" width="80%" sx={{ mt: 1 }} />
              <Skeleton variant="text" width="40%" />
            </Box>
          ))
        : items.map((item) => (
            <ImageGridCell
              key={item.id}
              item={item}
              resolution={resolution}
              onClick={onItemClick}
              dataTestId={`gallery-grid-item-${item.id}`}
            />
          ))}

      {!isLoading && items.length === 0 && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ gridColumn: '1 / -1' }}
          data-testid="gallery-grid-empty"
        >
          {emptyMessage}
        </Typography>
      )}
    </Box>
  )
}

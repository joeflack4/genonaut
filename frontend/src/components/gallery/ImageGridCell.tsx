import { useMemo, useState } from 'react'
import { Box, ButtonBase, Typography } from '@mui/material'
import ImageNotSupportedIcon from '@mui/icons-material/ImageNotSupported'
import InsertPhotoIcon from '@mui/icons-material/InsertPhoto'
import type { GalleryItem, ThumbnailResolution } from '../../types/domain'

export interface ImageGridCellProps {
  item: GalleryItem
  resolution: ThumbnailResolution
  onClick?: (item: GalleryItem) => void
  dataTestId?: string
}

export function ImageGridCell({ item, resolution, onClick, dataTestId = `gallery-grid-item-${item.id}` }: ImageGridCellProps) {
  const [imageError, setImageError] = useState(false)

  // Priority: resolution-specific thumbnail > default thumbnail > full image > imageUrl fallback
  const mediaSource = useMemo(() => {
    // Try to find resolution-specific thumbnail
    if (item.pathThumbsAltRes && item.pathThumbsAltRes[resolution.id]) {
      return item.pathThumbsAltRes[resolution.id]
    }
    // Fall back to default thumbnail, then full image, then imageUrl
    return item.pathThumb || item.contentData || item.imageUrl || null
  }, [item.pathThumbsAltRes, item.pathThumb, item.contentData, item.imageUrl, resolution.id])

  const aspectRatioPercentage = useMemo(() => (resolution.height / resolution.width) * 100, [resolution.height, resolution.width])

  const handleClick = () => {
    if (onClick) {
      onClick(item)
    }
  }

  const handleImageError = () => {
    setImageError(true)
  }

  return (
    <ButtonBase
      focusRipple={Boolean(onClick)}
      onClick={onClick ? handleClick : undefined}
      component="div"
      sx={{
        display: 'block',
        width: '100%',
        textAlign: 'left',
        borderRadius: 2,
        overflow: 'hidden',
        position: 'relative',
        boxShadow: 1,
        bgcolor: 'background.paper',
        transition: (theme) => theme.transitions.create(['transform', 'box-shadow'], {
          duration: theme.transitions.duration.short,
        }),
        '&:hover': onClick
          ? {
              transform: 'translateY(-2px)',
              boxShadow: 3,
            }
          : undefined,
        '&.Mui-disabled': {
          opacity: 1,
          boxShadow: 1,
        },
      }}
      data-testid={dataTestId}
      aria-label={item.title}
    >
      <Box
        sx={{
          position: 'relative',
          width: '100%',
          pt: `${aspectRatioPercentage}%`,
          bgcolor: 'background.default',
        }}
        data-testid={`${dataTestId}-media`}
      >
        {mediaSource && !imageError ? (
          <Box
            component="img"
            src={mediaSource}
            alt={item.title}
            onError={handleImageError}
            sx={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
              objectFit: 'contain',
              bgcolor: 'background.paper',
            }}
            data-testid={`${dataTestId}-image`}
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
            }}
            data-testid={`${dataTestId}-placeholder`}
          >
            <InsertPhotoIcon fontSize="large" />
          </Box>
        )}
      </Box>
      <Box sx={{ px: 2, py: 1.5 }} data-testid={`${dataTestId}-meta`}>
        <Typography
          variant="caption"
          display="block"
          noWrap
          title={item.title}
          data-testid={`${dataTestId}-title`}
        >
          {item.title}
        </Typography>
        {item.createdAt && (
          <Typography
            variant="caption"
            color="text.secondary"
            display="block"
            data-testid={`${dataTestId}-createdAt`}
          >
            {new Date(item.createdAt).toLocaleDateString()}
          </Typography>
        )}
      </Box>
    </ButtonBase>
  )
}

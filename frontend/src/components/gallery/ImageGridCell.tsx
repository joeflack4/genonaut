import { useMemo, useState } from 'react'
import { Box, ButtonBase, Typography } from '@mui/material'
import InsertPhotoIcon from '@mui/icons-material/InsertPhoto'
import type { GalleryItem, ThumbnailResolution } from '../../types/domain'
import { resolveImageSourceCandidates } from '../../utils/image-url'
import { BookmarkButton } from '../bookmarks'

export interface ImageGridCellProps {
  item: GalleryItem
  resolution: ThumbnailResolution
  onClick?: (item: GalleryItem) => void
  dataTestId?: string
  showBookmarkButton?: boolean
  userId?: string
}

export function ImageGridCell({
  item,
  resolution,
  onClick,
  dataTestId = `gallery-grid-item-${item.id}`,
  showBookmarkButton = false,
  userId
}: ImageGridCellProps) {
  const [imageError, setImageError] = useState(false)

  const mediaSource = useMemo(() => {
    const altResPath = item.pathThumbsAltRes ? item.pathThumbsAltRes[resolution.id] ?? null : null

    return resolveImageSourceCandidates(
      item.id,
      altResPath,
      item.pathThumb,
      item.imageUrl,
      item.contentData
    )
  }, [item.contentData, item.id, item.imageUrl, item.pathThumb, item.pathThumbsAltRes, resolution.id])

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
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 0.5, mb: 0.5 }}>
          <Typography
            variant="caption"
            display="block"
            noWrap
            title={item.title}
            data-testid={`${dataTestId}-title`}
            sx={{ flexGrow: 1, minWidth: 0 }}
          >
            {item.title}
          </Typography>
          {showBookmarkButton && userId && (
            <BookmarkButton
              contentId={item.id}
              contentSourceType={item.sourceType === 'auto' ? 'auto' : 'items'}
              userId={userId}
              size="small"
            />
          )}
        </Box>
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

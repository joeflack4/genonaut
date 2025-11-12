import { useMemo } from 'react'
import { Box, ButtonBase, Typography } from '@mui/material'
import MoreHorizIcon from '@mui/icons-material/MoreHoriz'
import type { ThumbnailResolution } from '../../types/domain'

export interface MoreGridCellProps {
  resolution: ThumbnailResolution
  onClick: () => void
  dataTestId?: string
}

/**
 * MoreGridCell - Grid cell that displays "More..." and navigates to full category view
 *
 * Used at the end of category grids to indicate there are more items to view
 */
export function MoreGridCell({
  resolution,
  onClick,
  dataTestId = 'bookmark-more-cell'
}: MoreGridCellProps) {
  const aspectRatioPercentage = useMemo(
    () => (resolution.height / resolution.width) * 100,
    [resolution.height, resolution.width]
  )

  return (
    <ButtonBase
      onClick={onClick}
      component="div"
      sx={{
        display: 'block',
        width: '100%',
        textAlign: 'center',
        borderRadius: 2,
        overflow: 'hidden',
        position: 'relative',
        boxShadow: 1,
        bgcolor: 'background.paper',
        border: 2,
        borderColor: 'divider',
        borderStyle: 'dashed',
        transition: (theme) => theme.transitions.create(['transform', 'box-shadow', 'border-color'], {
          duration: theme.transitions.duration.short,
        }),
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: 3,
          borderColor: 'primary.main',
        },
      }}
      data-testid={dataTestId}
      aria-label="View more bookmarks in this category"
    >
      <Box
        sx={{
          position: 'relative',
          width: '100%',
          pt: `${aspectRatioPercentage}%`,
          bgcolor: 'background.default',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
        data-testid={`${dataTestId}-container`}
      >
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 1,
          }}
          data-testid={`${dataTestId}-content`}
        >
          <MoreHorizIcon
            fontSize="large"
            color="primary"
            data-testid={`${dataTestId}-icon`}
          />
          <Typography
            variant="body1"
            color="primary"
            fontWeight="medium"
            data-testid={`${dataTestId}-text`}
          >
            More...
          </Typography>
        </Box>
      </Box>
    </ButtonBase>
  )
}

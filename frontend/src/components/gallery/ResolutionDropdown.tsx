import { useState, MouseEvent } from 'react'
import { IconButton, Menu, MenuItem, ListItemText, Tooltip } from '@mui/material'
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown'
import type { ThumbnailResolution, ThumbnailResolutionId } from '../../types/domain'
import { THUMBNAIL_RESOLUTION_OPTIONS } from '../../constants/gallery'

export interface ResolutionDropdownProps {
  currentResolution: ThumbnailResolutionId
  onResolutionChange: (resolution: ThumbnailResolutionId) => void
  dataTestId?: string
  disabled?: boolean
}

export function ResolutionDropdown({
  currentResolution,
  onResolutionChange,
  dataTestId = 'resolution-dropdown',
  disabled = false,
}: ResolutionDropdownProps) {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const open = Boolean(anchorEl)

  const handleClick = (event: MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleResolutionSelect = (resolutionId: ThumbnailResolutionId) => {
    onResolutionChange(resolutionId)
    handleClose()
  }

  const getCurrentResolutionLabel = () => {
    const resolution = THUMBNAIL_RESOLUTION_OPTIONS.find(r => r.id === currentResolution)
    return resolution?.label || currentResolution
  }

  return (
    <>
      <Tooltip title={`Grid resolution: ${getCurrentResolutionLabel()}`}>
        <IconButton
          onClick={handleClick}
          disabled={disabled}
          size="small"
          data-testid={dataTestId}
          aria-label="Select grid resolution"
          aria-controls={open ? 'resolution-menu' : undefined}
          aria-haspopup="true"
          aria-expanded={open ? 'true' : undefined}
        >
          <ArrowDropDownIcon />
        </IconButton>
      </Tooltip>
      <Menu
        id="resolution-menu"
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        MenuListProps={{
          'aria-labelledby': 'resolution-button',
        }}
        data-testid={`${dataTestId}-menu`}
      >
        {THUMBNAIL_RESOLUTION_OPTIONS.map((resolution: ThumbnailResolution) => (
          <MenuItem
            key={resolution.id}
            selected={resolution.id === currentResolution}
            onClick={() => handleResolutionSelect(resolution.id)}
            data-testid={`${dataTestId}-option-${resolution.id}`}
          >
            <ListItemText primary={resolution.label} />
          </MenuItem>
        ))}
      </Menu>
    </>
  )
}

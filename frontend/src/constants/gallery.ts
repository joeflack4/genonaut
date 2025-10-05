import type { ThumbnailResolution, ThumbnailResolutionId, ViewMode } from '../types/domain'

export const GALLERY_VIEW_MODE_STORAGE_KEY = 'gallery-view-mode'
export const DASHBOARD_VIEW_MODE_STORAGE_KEY = 'dashboard-view-mode'

export const DEFAULT_VIEW_MODE: ViewMode = 'list'

export const DEFAULT_THUMBNAIL_RESOLUTION_ID: ThumbnailResolutionId = '480x644'

export const GRID_COLUMN_BREAKPOINTS = {
  xs: 1,
  sm: 2,
  md: 3,
  lg: 4,
  xl: 5,
} as const

export const THUMBNAIL_RESOLUTION_OPTIONS: ThumbnailResolution[] = [
  { id: '576x768', width: 576, height: 768, label: '576x768', scale: 1 },
  { id: '520x698', width: 520, height: 698, label: '520x698', scale: 0.91 },
  { id: '480x644', width: 480, height: 644, label: '480x644', scale: 0.84 },
  { id: '440x590', width: 440, height: 590, label: '440x590', scale: 0.77 },
  { id: '400x537', width: 400, height: 537, label: '400x537', scale: 0.7 },
  { id: '360x484', width: 360, height: 484, label: '360x484', scale: 0.63 },
  { id: '320x430', width: 320, height: 430, label: '320x430', scale: 0.56 },
  { id: '300x403', width: 300, height: 403, label: '300x403', scale: 0.53 },
]

export const DEFAULT_THUMBNAIL_RESOLUTION: ThumbnailResolution =
  THUMBNAIL_RESOLUTION_OPTIONS.find((option) => option.id === DEFAULT_THUMBNAIL_RESOLUTION_ID)
  ?? THUMBNAIL_RESOLUTION_OPTIONS[0]

export const DEFAULT_GRID_VIEW_MODE: ViewMode = `grid-${DEFAULT_THUMBNAIL_RESOLUTION_ID}`

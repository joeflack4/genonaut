import type { ThumbnailResolution, ThumbnailResolutionId, ViewMode } from '../types/domain'

export const GALLERY_VIEW_MODE_STORAGE_KEY = 'gallery-view-mode'
export const DASHBOARD_VIEW_MODE_STORAGE_KEY = 'dashboard-view-mode'

export const DEFAULT_VIEW_MODE: ViewMode = 'list'

export const DEFAULT_THUMBNAIL_RESOLUTION_ID: ThumbnailResolutionId = '256x384'

export const GRID_COLUMN_BREAKPOINTS = {
  xs: 1,
  sm: 2,
  md: 3,
  lg: 4,
  xl: 5,
} as const

export const THUMBNAIL_RESOLUTION_OPTIONS: ThumbnailResolution[] = [
  { id: '512x768', width: 512, height: 768, label: '512x768', scale: 1 },
  { id: '460x691', width: 460, height: 691, label: '460x691', scale: 0.9 },
  { id: '410x614', width: 410, height: 614, label: '410x614', scale: 0.8 },
  { id: '358x538', width: 358, height: 538, label: '358x538', scale: 0.7 },
  { id: '307x461', width: 307, height: 461, label: '307x461', scale: 0.6 },
  { id: '256x384', width: 256, height: 384, label: '256x384', scale: 0.5 },
  { id: '232x344', width: 232, height: 344, label: '232x344', scale: 0.45 },
  { id: '200x304', width: 200, height: 304, label: '200x304', scale: 0.39 },
  { id: '184x272', width: 184, height: 272, label: '184x272', scale: 0.36 },
  { id: '152x232', width: 152, height: 232, label: '152x232', scale: 0.3 },
]

export const DEFAULT_THUMBNAIL_RESOLUTION: ThumbnailResolution =
  THUMBNAIL_RESOLUTION_OPTIONS.find((option) => option.id === DEFAULT_THUMBNAIL_RESOLUTION_ID)
  ?? THUMBNAIL_RESOLUTION_OPTIONS[0]

export const DEFAULT_GRID_VIEW_MODE: ViewMode = `grid-${DEFAULT_THUMBNAIL_RESOLUTION_ID}`

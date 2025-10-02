import type { ThumbnailResolutionId, ViewMode } from '../types/domain'
import { THUMBNAIL_RESOLUTION_OPTIONS } from '../constants/gallery'

const isBrowser = () => typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'

const VALID_RESOLUTION_IDS = new Set<ThumbnailResolutionId>(
  THUMBNAIL_RESOLUTION_OPTIONS.map((option) => option.id)
)

const parseViewMode = (value: unknown, fallback: ViewMode): ViewMode => {
  if (typeof value !== 'string') {
    return fallback
  }

  if (value === 'list') {
    return 'list'
  }

  if (value.startsWith('grid-')) {
    const resolutionId = value.slice(5) as ThumbnailResolutionId
    if (VALID_RESOLUTION_IDS.has(resolutionId)) {
      return value as ViewMode
    }
  }

  return fallback
}

export function loadViewMode(key: string, fallback: ViewMode): ViewMode {
  if (!isBrowser()) {
    return fallback
  }

  try {
    const stored = window.localStorage.getItem(key)
    return parseViewMode(stored, fallback)
  } catch (error) {
    console.warn(`Unable to read view mode from localStorage key "${key}"`, error)
    return fallback
  }
}

export function persistViewMode(key: string, mode: ViewMode): void {
  if (!isBrowser()) {
    return
  }

  try {
    window.localStorage.setItem(key, mode)
  } catch (error) {
    console.warn(`Unable to persist view mode to localStorage key "${key}"`, error)
  }
}

export function clearStoredViewMode(key: string): void {
  if (!isBrowser()) {
    return
  }

  try {
    window.localStorage.removeItem(key)
  } catch (error) {
    console.warn(`Unable to clear view mode in localStorage key "${key}"`, error)
  }
}

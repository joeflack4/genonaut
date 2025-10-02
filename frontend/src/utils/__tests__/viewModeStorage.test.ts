import { describe, it, expect, beforeEach, vi } from 'vitest'
import { loadViewMode, persistViewMode, clearStoredViewMode } from '../viewModeStorage'
import { DEFAULT_VIEW_MODE, DEFAULT_GRID_VIEW_MODE } from '../../constants/gallery'

const STORAGE_KEY = 'test-view-mode'

describe('viewModeStorage', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('returns fallback view mode when storage is empty', () => {
    const mode = loadViewMode(STORAGE_KEY, DEFAULT_VIEW_MODE)
    expect(mode).toBe(DEFAULT_VIEW_MODE)
  })

  it('persists and loads list view mode', () => {
    persistViewMode(STORAGE_KEY, 'list')
    expect(localStorage.getItem(STORAGE_KEY)).toBe('list')
    expect(loadViewMode(STORAGE_KEY, DEFAULT_VIEW_MODE)).toBe('list')
  })

  it('persists and loads grid view mode with valid resolution', () => {
    persistViewMode(STORAGE_KEY, DEFAULT_GRID_VIEW_MODE)
    expect(loadViewMode(STORAGE_KEY, DEFAULT_VIEW_MODE)).toBe(DEFAULT_GRID_VIEW_MODE)
  })

  it('returns fallback when stored value is invalid', () => {
    localStorage.setItem(STORAGE_KEY, 'grid-unknown')
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const mode = loadViewMode(STORAGE_KEY, DEFAULT_GRID_VIEW_MODE)

    expect(mode).toBe(DEFAULT_GRID_VIEW_MODE)
    expect(warnSpy).not.toHaveBeenCalled()
  })

  it('clears stored view mode', () => {
    persistViewMode(STORAGE_KEY, 'list')
    clearStoredViewMode(STORAGE_KEY)
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull()
  })
})

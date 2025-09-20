import type { ReactNode } from 'react'
import { renderHook, act } from '@testing-library/react'
import { vi } from 'vitest'
import { ThemeModeProvider, useThemeMode } from '../providers/theme'

describe('ThemeModeProvider', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('defaults to dark mode', () => {
    const { result } = renderHook(() => useThemeMode(), {
      wrapper: ({ children }: { children: ReactNode }) => (
        <ThemeModeProvider>{children}</ThemeModeProvider>
      ),
    })

    expect(result.current.mode).toBe('dark')
  })

  it('toggles theme mode and persists to localStorage', () => {
    const setItemSpy = vi.spyOn(Storage.prototype, 'setItem')

    const { result } = renderHook(() => useThemeMode(), {
      wrapper: ({ children }: { children: ReactNode }) => (
        <ThemeModeProvider>{children}</ThemeModeProvider>
      ),
    })

    act(() => {
      result.current.toggleMode()
    })

    expect(result.current.mode).toBe('light')
    expect(setItemSpy).toHaveBeenCalledWith('theme-mode', 'light')

    setItemSpy.mockRestore()
  })
})

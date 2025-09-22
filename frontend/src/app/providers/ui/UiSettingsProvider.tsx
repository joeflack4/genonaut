import type { PropsWithChildren } from 'react'
import { createContext, useContext, useEffect, useMemo, useState } from 'react'

interface UiSettings {
  showButtonLabels: boolean
}

interface UiSettingsContextValue extends UiSettings {
  toggleButtonLabels: () => void
  setShowButtonLabels: (show: boolean) => void
}

const UiSettingsContext = createContext<UiSettingsContextValue | undefined>(undefined)

const STORAGE_KEY = 'ui-settings'

const getStoredSettings = (): Partial<UiSettings> => {
  if (typeof window === 'undefined') {
    return {}
  }

  try {
    const stored = window.localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : {}
  } catch (error) {
    console.warn('Unable to access UI settings in localStorage', error)
    return {}
  }
}

const getInitialSettings = (): UiSettings => {
  const storedSettings = getStoredSettings()

  return {
    showButtonLabels: storedSettings.showButtonLabels ?? false, // Default is off
  }
}

const persistSettings = (settings: UiSettings) => {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch (error) {
    console.warn('Unable to persist UI settings to localStorage', error)
  }
}

export function UiSettingsProvider({ children }: PropsWithChildren) {
  const [settings, setSettings] = useState<UiSettings>(() => getInitialSettings())

  useEffect(() => {
    persistSettings(settings)
  }, [settings])

  const toggleButtonLabels = () => {
    setSettings((current) => ({
      ...current,
      showButtonLabels: !current.showButtonLabels,
    }))
  }

  const setShowButtonLabels = (show: boolean) => {
    setSettings((current) => ({
      ...current,
      showButtonLabels: show,
    }))
  }

  const contextValue = useMemo<UiSettingsContextValue>(
    () => ({
      ...settings,
      toggleButtonLabels,
      setShowButtonLabels,
    }),
    [settings]
  )

  return (
    <UiSettingsContext.Provider value={contextValue}>
      {children}
    </UiSettingsContext.Provider>
  )
}

export function useUiSettings() {
  const context = useContext(UiSettingsContext)

  if (!context) {
    throw new Error('useUiSettings must be used within a UiSettingsProvider')
  }

  return context
}
import type { PropsWithChildren } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeModeProvider } from './theme'
import { UiSettingsProvider } from './ui'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <QueryClientProvider client={queryClient}>
      <UiSettingsProvider>
        <ThemeModeProvider>{children}</ThemeModeProvider>
      </UiSettingsProvider>
    </QueryClientProvider>
  )
}

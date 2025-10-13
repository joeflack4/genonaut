import type { PropsWithChildren } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeModeProvider } from './theme'
import { TimeoutNotificationProvider } from './timeout'
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
        <ThemeModeProvider>
          <TimeoutNotificationProvider>{children}</TimeoutNotificationProvider>
        </ThemeModeProvider>
      </UiSettingsProvider>
    </QueryClientProvider>
  )
}

import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi } from 'vitest'
import { ThemeModeProvider } from '../../../app/providers/theme'
import { TimeoutNotificationProvider } from '../../../app/providers/timeout/TimeoutNotificationProvider'
import { UiSettingsProvider } from '../../../app/providers/ui'
import { AppLayout } from '../AppLayout'

vi.mock('../../../hooks', () => {
  const useCurrentUser = vi.fn()

  return {
    useCurrentUser,
  }
})

const { useCurrentUser } = await import('../../../hooks')
type UseCurrentUserResult = ReturnType<typeof useCurrentUser>
const mockedUseCurrentUser = vi.mocked(useCurrentUser)

const renderWithProviders = (ui: ReactNode, initialEntry: string = '/dashboard') => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <UiSettingsProvider>
        <ThemeModeProvider>
          <TimeoutNotificationProvider>
            <MemoryRouter initialEntries={[initialEntry]}>
              {ui}
            </MemoryRouter>
          </TimeoutNotificationProvider>
        </ThemeModeProvider>
      </UiSettingsProvider>
    </QueryClientProvider>
  )
}

describe('AppLayout', () => {
  beforeEach(() => {
    mockedUseCurrentUser.mockReset()
  })

  it.skip('renders navigation and user icon when data is available', () => {
    mockedUseCurrentUser.mockReturnValue({
      data: { id: 1, name: 'Admin User' },
      isLoading: false,
    } as UseCurrentUserResult)

    renderWithProviders(
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<div>Dashboard Content</div>} />
        </Route>
      </Routes>
    )

    // Username text is hidden by default (showButtonLabels defaults to false)
    expect(screen.queryByText(/Admin User/)).not.toBeInTheDocument()
    // But the person icon should be visible
    expect(screen.getByTestId('PersonIcon')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /dashboard/i })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('navigation')).toBeInTheDocument()
  })

  it('renders hamburger menu button', () => {
    mockedUseCurrentUser.mockReturnValue({
      data: { id: 1, name: 'Admin User' },
      isLoading: false,
    } as UseCurrentUserResult)

    renderWithProviders(
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<div>Dashboard Content</div>} />
        </Route>
      </Routes>
    )

    expect(screen.getByLabelText(/toggle sidebar/i)).toBeInTheDocument()
  })

  it('renders icons in navigation items', () => {
    mockedUseCurrentUser.mockReturnValue({
      data: { id: 1, name: 'Admin User' },
      isLoading: false,
    } as UseCurrentUserResult)

    renderWithProviders(
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<div>Dashboard Content</div>} />
        </Route>
      </Routes>
    )

    // Check that navigation items have icons
    expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /gallery/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /recommendations/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /settings/i })).toBeInTheDocument()
  })

  it('navigates to settings when user icon is clicked', async () => {
    const user = userEvent.setup()
    mockedUseCurrentUser.mockReturnValue({
      data: { id: 1, name: 'Admin User' },
      isLoading: false,
    } as UseCurrentUserResult)

    renderWithProviders(
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<div>Dashboard Content</div>} />
          <Route path="/settings" element={<div>Settings Content</div>} />
        </Route>
      </Routes>
    )

    // Click on the user icon (since text is hidden by default)
    await user.click(screen.getByTestId('PersonIcon'))

    // Should navigate to settings page
    expect(screen.getByText('Settings Content')).toBeInTheDocument()
  })
})

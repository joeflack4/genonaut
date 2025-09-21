import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi } from 'vitest'
import { ThemeModeProvider } from '../../../app/providers/theme'
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
      <ThemeModeProvider>
        <MemoryRouter initialEntries={[initialEntry]}>
          {ui}
        </MemoryRouter>
      </ThemeModeProvider>
    </QueryClientProvider>
  )
}

describe('AppLayout', () => {
  beforeEach(() => {
    mockedUseCurrentUser.mockReset()
  })

  it('renders navigation and user name when data is available', () => {
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

    expect(screen.getByText(/Admin User/)).toBeInTheDocument()
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
})

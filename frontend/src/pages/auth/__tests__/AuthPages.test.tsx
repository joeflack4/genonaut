import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi } from 'vitest'
import { LoginPage, SignupPage } from '../'

vi.mock('../../../hooks', () => ({
  useCurrentUser: vi.fn(),
}))

const { useCurrentUser } = await import('../../../hooks')
const mockedUseCurrentUser = vi.mocked(useCurrentUser)

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = (await importOriginal()) as typeof import('react-router-dom')
  return {
    ...actual,
    useNavigate: vi.fn(() => vi.fn()),
  }
})

const { useNavigate } = await import('react-router-dom')
const useNavigateMock = vi.mocked(useNavigate)

const renderWithProviders = (ui: ReactNode, initialEntries: string[] = ['/login']) => {
  const queryClient = new QueryClient()

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('Auth placeholder pages', () => {
  beforeEach(() => {
    mockedUseCurrentUser.mockReset()
    useNavigateMock.mockClear()
  })

  it('renders login form when user unauthenticated', () => {
    mockedUseCurrentUser.mockReturnValue({ data: null })
    renderWithProviders(
      <Routes>
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    )

    expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument()
  })

  it('redirects authenticated user away from login', () => {
    const navigateSpy = vi.fn()
    useNavigateMock.mockReturnValue(navigateSpy)
    mockedUseCurrentUser.mockReturnValue({ data: { id: 1 } })

    renderWithProviders(
      <Routes>
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    )

    expect(navigateSpy).toHaveBeenCalledWith('/dashboard', { replace: true })
  })

  it('redirects authenticated user away from signup', () => {
    const navigateSpy = vi.fn()
    useNavigateMock.mockReturnValue(navigateSpy)
    mockedUseCurrentUser.mockReturnValue({ data: { id: 1 } })

    renderWithProviders(
      <Routes>
        <Route path="/signup" element={<SignupPage />} />
      </Routes>,
      ['/signup']
    )

    expect(navigateSpy).toHaveBeenCalledWith('/dashboard', { replace: true })
  })
})

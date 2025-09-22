import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, vi } from 'vitest'
import { ThemeModeProvider } from '../../../app/providers/theme'
import { UiSettingsProvider } from '../../../app/providers/ui'
import { SettingsPage } from '../SettingsPage'

const mockCurrentUser = { id: 1, name: 'Admin', email: 'admin@example.com' }

vi.mock('../../../hooks', () => {
  const useUpdateUser = vi.fn()

  return {
    useCurrentUser: () => ({
      data: mockCurrentUser,
      isLoading: false,
    }),
    useUpdateUser,
  }
})

vi.mock('../../../app/providers/theme', async (importOriginal) => {
  const actual = (await importOriginal()) as typeof import('../../../app/providers/theme')
  return {
    ...actual,
    useThemeMode: vi.fn(),
  }
})

const { useUpdateUser } = await import('../../../hooks')
const updateUserMock = vi.mocked(useUpdateUser)

const { useThemeMode } = await import('../../../app/providers/theme')
const useThemeModeMock = vi.mocked(useThemeMode)

const renderSettingsPage = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <UiSettingsProvider>
        <ThemeModeProvider>{children}</ThemeModeProvider>
      </UiSettingsProvider>
    </QueryClientProvider>
  )

  return render(<SettingsPage />, { wrapper })
}

describe('SettingsPage', () => {
  const mutateAsyncMock = vi.fn()
  const toggleModeMock = vi.fn()

  beforeEach(() => {
    mutateAsyncMock.mockReset()
    toggleModeMock.mockReset()

    updateUserMock.mockReturnValue({ mutateAsync: mutateAsyncMock })
    useThemeModeMock.mockReturnValue({ mode: 'dark', toggleMode: toggleModeMock })
  })

  it('shows current user info and saves updates', async () => {
    renderSettingsPage()

    const nameInput = screen.getByLabelText(/display name/i)
    expect(nameInput).toHaveValue('Admin')

    fireEvent.change(nameInput, { target: { value: 'New Admin' } })
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))

    expect(mutateAsyncMock).toHaveBeenCalledWith({
      id: 1,
      payload: { name: 'New Admin', email: 'admin@example.com' },
    })
  })

  it('toggles theme mode', () => {
    renderSettingsPage()

    fireEvent.click(screen.getByRole('button', { name: /toggle theme/i }))

    expect(toggleModeMock).toHaveBeenCalled()
  })

  it('renders UI settings section with button labels toggle', () => {
    renderSettingsPage()

    // Check UI section is present
    expect(screen.getByText('UI')).toBeInTheDocument()
    expect(screen.getByLabelText(/show sidebar and navbar button labels/i)).toBeInTheDocument()
    expect(screen.getByText(/when disabled, only icons will be shown/i)).toBeInTheDocument()
  })
})

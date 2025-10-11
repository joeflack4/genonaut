import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { ThemeModeProvider } from '../../../app/providers/theme'
import { UiSettingsProvider } from '../../../app/providers/ui'
import { NotificationsPage } from '../NotificationsPage'
import type { NotificationListResponse, NotificationResponse } from '../../../services/notification-service'

const {
  mockGetNotifications,
  mockMarkAsRead,
  mockDeleteNotification,
  mockUseCurrentUser,
} = vi.hoisted(() => ({
  mockGetNotifications: vi.fn(),
  mockMarkAsRead: vi.fn(),
  mockDeleteNotification: vi.fn(),
  mockUseCurrentUser: vi.fn(),
}))

vi.mock('../../../hooks/useNotificationService', () => ({
  useNotificationService: () => ({
    getNotifications: mockGetNotifications,
    markAsRead: mockMarkAsRead,
    deleteNotification: mockDeleteNotification,
  }),
}))

vi.mock('../../../hooks', () => ({
  useCurrentUser: mockUseCurrentUser,
}))

const sampleNotifications: NotificationResponse[] = [
  {
    id: 1,
    user_id: 'user-1',
    title: 'Generation finished',
    message: 'Your job completed successfully',
    notification_type: 'job_completed',
    read_status: false,
    related_job_id: 42,
    related_content_id: 101,
    created_at: new Date('2024-01-10T10:00:00Z').toISOString(),
    read_at: null,
  },
  {
    id: 2,
    user_id: 'user-1',
    title: 'System update',
    message: 'A new feature is available',
    notification_type: 'system',
    read_status: true,
    related_job_id: null,
    related_content_id: null,
    created_at: new Date('2024-01-09T10:00:00Z').toISOString(),
    read_at: new Date('2024-01-09T12:00:00Z').toISOString(),
  },
  {
    id: 3,
    user_id: 'user-1',
    title: 'Experimental notification',
    message: 'This type is not yet recognized',
    notification_type: 'custom_type',
    read_status: false,
    related_job_id: null,
    related_content_id: null,
    created_at: new Date('2024-01-08T10:00:00Z').toISOString(),
    read_at: null,
  },
]

function renderNotificationsPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <UiSettingsProvider>
        <ThemeModeProvider>
          <MemoryRouter>{children}</MemoryRouter>
        </ThemeModeProvider>
      </UiSettingsProvider>
    </QueryClientProvider>
  )

  return render(<NotificationsPage />, { wrapper })
}

describe('NotificationsPage', () => {
  beforeEach(() => {
    mockGetNotifications.mockReset()
    mockMarkAsRead.mockReset()
    mockDeleteNotification.mockReset()
    mockUseCurrentUser.mockReset()

    mockUseCurrentUser.mockReturnValue({
      data: { id: 'user-1' },
      isLoading: false,
    })

    mockGetNotifications.mockResolvedValue({
      items: sampleNotifications,
      total: sampleNotifications.length,
      skip: 0,
      limit: 100,
    })

    mockMarkAsRead.mockResolvedValue({
      ...sampleNotifications[0],
      read_status: true,
      read_at: new Date('2024-01-10T11:00:00Z').toISOString(),
    })

    mockDeleteNotification.mockResolvedValue()
  })

  it('renders notifications with type and read indicators', async () => {
    renderNotificationsPage()

    expect(await screen.findByTestId('notifications-list')).toBeInTheDocument()
    expect(screen.getByTestId('notifications-list-item-1')).toBeInTheDocument()
    expect(screen.getByTestId('notifications-type-chip-1')).toHaveTextContent('Job Completed')
    expect(screen.getByTestId('notifications-unread-chip-1')).toBeInTheDocument()
    expect(screen.queryByTestId('notifications-unread-chip-2')).not.toBeInTheDocument()
    expect(screen.getByTestId('notifications-type-chip-3')).toHaveTextContent('Other')
  })

  it('applies type filters when selection changes', async () => {
    renderNotificationsPage()

    await screen.findByTestId('notifications-list')
    const filterTrigger = screen.getByRole('combobox', { name: /filter by type/i })
    await userEvent.click(filterTrigger)

    const deselectOptions = [
      'notifications-filter-option-other',
      'notifications-filter-option-job_completed',
      'notifications-filter-option-job_cancelled',
      'notifications-filter-option-system',
      'notifications-filter-option-recommendation',
    ]

    for (const optionTestId of deselectOptions) {
      await userEvent.click(await screen.findByTestId(optionTestId))
    }

    await waitFor(() => expect(mockGetNotifications.mock.calls.length).toBeGreaterThanOrEqual(2))
    const lastCallArgs = mockGetNotifications.mock.calls.at(-1)?.[0]
    expect(lastCallArgs?.notification_types).toEqual(['job_failed'])
  })

  it('marks notifications as read when clicked', async () => {
    renderNotificationsPage()

    await screen.findByTestId('notifications-list')
    await userEvent.click(screen.getByTestId('notifications-list-item-1'))

    await waitFor(() => expect(mockMarkAsRead).toHaveBeenCalled())
    expect(mockMarkAsRead).toHaveBeenCalledWith(1, 'user-1')
  })

  it('deletes notifications after confirmation', async () => {
    renderNotificationsPage()

    await screen.findByTestId('notifications-list')
    await userEvent.click(screen.getByTestId('notifications-delete-1'))

    const confirmButton = await screen.findByTestId('notifications-delete-confirm')
    await userEvent.click(confirmButton)

    await waitFor(() => expect(mockDeleteNotification).toHaveBeenCalled())
    expect(mockDeleteNotification).toHaveBeenCalledWith(1, 'user-1')
  })
})

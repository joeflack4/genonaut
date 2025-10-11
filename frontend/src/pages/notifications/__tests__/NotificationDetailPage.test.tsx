import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { ThemeModeProvider } from '../../../app/providers/theme'
import { UiSettingsProvider } from '../../../app/providers/ui'
import { NotificationDetailPage } from '../NotificationDetailPage'
import type { NotificationResponse } from '../../../services/notification-service'

const {
  mockGetNotification,
  mockMarkAsRead,
  mockMarkAsUnread,
  mockUseCurrentUserDetail,
} = vi.hoisted(() => ({
  mockGetNotification: vi.fn(),
  mockMarkAsRead: vi.fn(),
  mockMarkAsUnread: vi.fn(),
  mockUseCurrentUserDetail: vi.fn(),
}))

vi.mock('../../../hooks/useNotificationService', () => ({
  useNotificationService: () => ({
    getNotification: mockGetNotification,
    markAsRead: mockMarkAsRead,
    markAsUnread: mockMarkAsUnread,
  }),
}))

vi.mock('../../../hooks', () => ({
  useCurrentUser: mockUseCurrentUserDetail,
}))

const unreadNotification: NotificationResponse = {
  id: 5,
  user_id: 'user-1',
  title: 'Job failed',
  message: 'Generation did not complete',
  notification_type: 'job_failed',
  read_status: false,
  related_job_id: 77,
  related_content_id: null,
  created_at: new Date('2024-02-01T15:00:00Z').toISOString(),
  read_at: null,
}

const readNotification: NotificationResponse = {
  ...unreadNotification,
  id: 6,
  notification_type: 'system',
  read_status: true,
  message: 'Maintenance complete',
  read_at: new Date('2024-02-01T16:00:00Z').toISOString(),
}

function renderNotificationDetail(initialPath: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <UiSettingsProvider>
        <ThemeModeProvider>
         <MemoryRouter initialEntries={[initialPath]}>
           <Routes>
             <Route path="/notification/:id" element={children} />
              <Route path="/notifications" element={<div data-testid="notifications-route-placeholder" />} />
           </Routes>
         </MemoryRouter>
        </ThemeModeProvider>
      </UiSettingsProvider>
    </QueryClientProvider>
  )

  return render(<NotificationDetailPage />, { wrapper })
}

describe('NotificationDetailPage', () => {
  beforeEach(() => {
    mockGetNotification.mockReset()
    mockMarkAsRead.mockReset()
    mockMarkAsUnread.mockReset()
    mockUseCurrentUserDetail.mockReset()

    mockUseCurrentUserDetail.mockReturnValue({
      data: { id: 'user-1' },
      isLoading: false,
    })

    mockGetNotification.mockResolvedValue(readNotification)
    mockMarkAsRead.mockResolvedValue({ ...readNotification })
    mockMarkAsUnread.mockResolvedValue({ ...unreadNotification })
  })

  it('renders notification details', async () => {
    renderNotificationDetail('/notification/6')

    expect(await screen.findByTestId('notification-detail-title')).toHaveTextContent('Job failed')
    expect(screen.getByTestId('notification-detail-type')).toHaveTextContent('System')
    expect(screen.getByTestId('notification-detail-read-status')).toHaveTextContent('Read')
  })

  it('marks notification as read when it is initially unread', async () => {
    mockGetNotification.mockResolvedValueOnce(unreadNotification)
    mockMarkAsRead.mockResolvedValueOnce({ ...unreadNotification, read_status: true, read_at: new Date('2024-02-01T17:00:00Z').toISOString() })

    renderNotificationDetail('/notification/5')

    await waitFor(() => expect(mockMarkAsRead).toHaveBeenCalled())
    expect(mockMarkAsRead).toHaveBeenCalledWith(unreadNotification.id, 'user-1')
  })

  it('allows marking a notification as unread', async () => {
    mockGetNotification.mockResolvedValueOnce(readNotification)
    renderNotificationDetail('/notification/6')

    await screen.findByTestId('notification-detail-title')
    const unreadButton = screen.getByTestId('notification-detail-mark-unread')
    await userEvent.click(unreadButton)

    expect(mockMarkAsUnread).toHaveBeenCalledWith(readNotification.id, 'user-1')
  })

  it('handles invalid identifier', async () => {
    renderNotificationDetail('/notification/not-a-number')

    const invalidView = await screen.findByTestId('notification-detail-invalid')
    const backButton = within(invalidView).getByRole('button', { name: /all notifications/i })
    await userEvent.click(backButton)
    expect(await screen.findByTestId('notifications-route-placeholder')).toBeInTheDocument()
  })

  it('shows error state when fetch fails', async () => {
    mockGetNotification.mockRejectedValueOnce(new Error('failed'))

    renderNotificationDetail('/notification/7')

    expect(await screen.findByTestId('notification-detail-error')).toBeInTheDocument()
  })
})

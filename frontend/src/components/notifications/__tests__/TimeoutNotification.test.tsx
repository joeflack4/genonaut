import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { TimeoutNotificationProvider } from '../../../app/providers/timeout'
import { ApiClient } from '../../../services/api-client'
import { TimeoutNotification } from '../TimeoutNotification'

function createTimeoutResponse(): Response {
  const payload = {
    error_type: 'statement_timeout' as const,
    message: 'Query timed out',
    timeout_duration: '12s',
    details: {
      context: { path: '/api/v1/example' },
    },
  }

  return {
    ok: false,
    status: 504,
    headers: new Headers({ 'content-type': 'application/json' }),
    json: async () => payload,
    text: async () => JSON.stringify(payload),
    clone: () => createTimeoutResponse(),
    redirected: false,
    statusText: 'Gateway Timeout',
    type: 'default',
    url: 'http://test/api',
    body: null,
    bodyUsed: false,
    arrayBuffer: async () => new ArrayBuffer(0),
    blob: async () => new Blob(),
    formData: async () => new FormData(),
  } as Response
}

describe('TimeoutNotification', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders a warning when a statement timeout occurs', async () => {
    const fetchMock = vi.fn().mockResolvedValue(createTimeoutResponse())
    const client = new ApiClient({ baseUrl: 'http://test', fetchFn: fetchMock })

    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

    render(
      <TimeoutNotificationProvider>
        <TimeoutNotification />
      </TimeoutNotificationProvider>
    )

    await act(async () => {
      await expect(client.get('/api/v1/example')).rejects.toBeDefined()
    })

    const alert = await screen.findByTestId('timeout-notification-alert')
    expect(alert).toBeInTheDocument()
    expect(screen.getByTestId('timeout-notification-message')).toHaveTextContent('Query timed out')
    expect(screen.getByTestId('timeout-notification-helper')).toHaveTextContent('Timeout: 12s')
    expect(screen.getByTestId('timeout-notification-dismiss')).toBeInTheDocument()

    await userEvent.click(screen.getByTestId('timeout-notification-dismiss'))
    await waitFor(() => expect(screen.queryByTestId('timeout-notification-alert')).not.toBeInTheDocument())

    warnSpy.mockRestore()
  })

  it.skip('auto-dismisses after delay @skipped-autohide-test', () => {
    // TODO: requires reliable control over MUI transition timers with fake timers.
  })
})

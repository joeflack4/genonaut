import { describe, expect, it, vi } from 'vitest'

import {
  ApiClient,
  addStatementTimeoutListener,
  isStatementTimeoutError,
  type StatementTimeoutEvent,
} from '../api-client'

function createResponse(overrides: Partial<Response>): Response {
  const headers = new Headers({ 'content-type': 'application/json' })
  return {
    ok: false,
    status: 504,
    headers,
    json: async () => ({}),
    text: async () => '',
    clone: () => createResponse(overrides),
    redirected: false,
    statusText: 'Gateway Timeout',
    type: 'default',
    url: 'http://test/api',
    body: null,
    bodyUsed: false,
    arrayBuffer: async () => new ArrayBuffer(0),
    blob: async () => new Blob(),
    formData: async () => new FormData(),
    ...overrides,
  } as Response
}

describe('ApiClient timeout handling', () => {
  it('emits statement timeout events and annotates ApiError metadata', async () => {
    const timeoutPayload = {
      error_type: 'statement_timeout' as const,
      message: 'Query timed out',
      timeout_duration: '15s',
      details: {
        context: { path: '/api/v1/example' },
        query: 'SELECT 1',
      },
    }

    const fetchMock = vi.fn().mockResolvedValue(
      createResponse({
        json: async () => timeoutPayload,
      })
    )

    const client = new ApiClient({ baseUrl: 'http://test', fetchFn: fetchMock })

    const events: StatementTimeoutEvent[] = []
    const unsubscribe = addStatementTimeoutListener((event) => events.push(event))

    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

    let capturedError: unknown
    try {
      await client.get('/api/v1/example')
    } catch (error) {
      capturedError = error
    }

    unsubscribe()
    warnSpy.mockRestore()

    expect(events).toHaveLength(1)
    expect(events[0]).toMatchObject({ timeoutDuration: '15s' })

    expect(capturedError).toBeInstanceOf(Error)
    if (capturedError && typeof capturedError === 'object' && 'timeoutDuration' in capturedError) {
      expect((capturedError as { timeoutDuration?: string }).timeoutDuration).toBe('15s')
    }
    expect(isStatementTimeoutError(capturedError)).toBe(true)
  })
})

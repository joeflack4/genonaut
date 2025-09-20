import type { Page } from '@playwright/test'

interface MockDefinition {
  pattern: string
  method?: string
  body: unknown
  status?: number
}

export async function setupMockApi(page: Page, mocks: MockDefinition[]) {
  await page.addInitScript(() => {
    const registry: Array<{
      pattern: RegExp
      method: string
      responder: () => { body: unknown; status: number }
    }> = []
    const history: Array<{ url: string; method: string }> = []

    window.__pwRegisterMock = (pattern: string, method: string, body: unknown, status: number) => {
      registry.push({
        pattern: new RegExp(pattern),
        method,
        responder: () => ({ body, status }),
      })
    }

    window.__pwUpdateMock = (pattern: string, method: string, body: unknown, status: number) => {
      const entry = registry.find((mock) => mock.method === method && mock.pattern.source === pattern)
      if (entry) {
        entry.responder = () => ({ body, status })
      }
    }

    window.__pwReadMockHistory = () => [...history]

    const originalFetch = window.fetch.bind(window)
    window.fetch = async (input, init = {}) => {
      const url = typeof input === 'string' ? input : input.url
      const method = (init.method ?? (typeof input === 'string' ? 'GET' : input.method ?? 'GET')).toUpperCase()
      const entry = registry.find((mock) => mock.method === method && mock.pattern.test(url))

      if (entry) {
        history.push({ url, method })
        const { body, status } = entry.responder()
        return new Response(JSON.stringify(body), {
          status,
          headers: { 'Content-Type': 'application/json' },
        })
      }

      return originalFetch(input as RequestInfo, init)
    }
  })

  await page.addInitScript((definitions) => {
    definitions.forEach(({ pattern, method, body, status }) => {
      window.__pwRegisterMock(pattern, method, body, status)
    })
  }, mocks.map((mock) => ({
    pattern: mock.pattern,
    method: (mock.method ?? 'GET').toUpperCase(),
    body: mock.body,
    status: mock.status ?? 200,
  })))
}

declare global {
  interface Window {
    __pwRegisterMock: (pattern: string, method: string, body: unknown, status: number) => void
    __pwUpdateMock: (pattern: string, method: string, body: unknown, status: number) => void
    __pwReadMockHistory: () => Array<{ url: string; method: string }>
  }
}

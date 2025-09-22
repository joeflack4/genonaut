export interface ApiClientOptions {
  baseUrl?: string
  fetchFn?: typeof globalThis.fetch
}

export class ApiError extends Error {
  public readonly status: number
  public readonly body?: unknown

  constructor(message: string, status: number, body?: unknown) {
    super(message)
    this.status = status
    this.body = body
    this.name = 'ApiError'
  }
}

export class ApiClient {
  private readonly baseUrl: string
  private readonly fetchFn: typeof globalThis.fetch

  constructor(options: ApiClientOptions = {}) {
    const envBaseUrl = typeof import.meta !== 'undefined' ? import.meta.env?.VITE_API_BASE_URL : undefined
    this.baseUrl = options.baseUrl ?? envBaseUrl ?? 'http://localhost:8000'
    this.fetchFn = options.fetchFn ?? fetch.bind(globalThis)
  }

  async get<T>(endpoint: string, init?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...init, method: 'GET' })
  }

  async post<T, B = unknown>(endpoint: string, body?: B, init?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...init,
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : init?.body,
    })
  }

  async put<T, B = unknown>(endpoint: string, body?: B, init?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...init,
      method: 'PUT',
      body: body !== undefined ? JSON.stringify(body) : init?.body,
    })
  }

  async patch<T, B = unknown>(endpoint: string, body?: B, init?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...init,
      method: 'PATCH',
      body: body !== undefined ? JSON.stringify(body) : init?.body,
    })
  }

  async delete<T>(endpoint: string, init?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...init, method: 'DELETE' })
  }

  private async request<T>(endpoint: string, init: RequestInit): Promise<T> {
    const url = this.composeUrl(endpoint)
    const headers = this.createHeaders(init.headers)

    const response = await this.fetchFn(url, {
      ...init,
      headers,
    })

    if (!response.ok) {
      let errorBody: unknown

      try {
        const contentType = response.headers.get('content-type') ?? ''
        if (contentType.includes('application/json')) {
          errorBody = await response.json()
        } else {
          errorBody = await response.text()
        }
      } catch {
        errorBody = undefined
      }

      throw new ApiError(`Request to ${url} failed with status ${response.status}`, response.status, errorBody)
    }

    if (response.status === 204) {
      return undefined as T
    }

    const contentType = response.headers.get('content-type') ?? ''

    if (contentType.includes('application/json')) {
      return (await response.json()) as T
    }

    return (await response.text()) as T
  }

  private composeUrl(endpoint: string): string {
    try {
      return new URL(endpoint, this.baseUrl).toString()
    } catch {
      throw new Error(`Failed to construct URL from base ${this.baseUrl} and endpoint ${endpoint}`)
    }
  }

  private createHeaders(headers?: HeadersInit): HeadersInit {
    const merged = new Headers(headers)

    if (!merged.has('Content-Type')) {
      merged.set('Content-Type', 'application/json')
    }

    return merged
  }
}

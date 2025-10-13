export interface ApiClientOptions {
  baseUrl?: string
  fetchFn?: typeof globalThis.fetch
}

export interface StatementTimeoutErrorResponse {
  error_type: 'statement_timeout'
  message: string
  timeout_duration: string
  details?: {
    context?: Record<string, unknown>
    query?: string
  }
}

export interface StatementTimeoutEvent {
  message: string
  timeoutDuration: string
  details?: StatementTimeoutErrorResponse['details']
}

type StatementTimeoutListener = (event: StatementTimeoutEvent) => void

const statementTimeoutListeners = new Set<StatementTimeoutListener>()

export function addStatementTimeoutListener(listener: StatementTimeoutListener): () => void {
  statementTimeoutListeners.add(listener)
  return () => {
    statementTimeoutListeners.delete(listener)
  }
}

function notifyStatementTimeout(event: StatementTimeoutEvent) {
  statementTimeoutListeners.forEach((listener) => {
    try {
      listener(event)
    } catch (error) {
      console.error('Failed to handle statement timeout listener', error)
    }
  })
}

function isStatementTimeoutErrorResponse(body: unknown): body is StatementTimeoutErrorResponse {
  if (!body || typeof body !== 'object') {
    return false
  }

  const value = body as Record<string, unknown>
  return (
    value.error_type === 'statement_timeout' &&
    typeof value.message === 'string' &&
    typeof value.timeout_duration === 'string'
  )
}

export class ApiError extends Error {
  public readonly status: number
  public readonly body?: unknown
  public readonly errorType?: string
  public readonly timeoutDuration?: string
  public readonly details?: unknown

  constructor(
    message: string,
    status: number,
    body?: unknown,
    options?: { errorType?: string; timeoutDuration?: string; details?: unknown }
  ) {
    super(message)
    this.status = status
    this.body = body
    this.errorType = options?.errorType
    this.timeoutDuration = options?.timeoutDuration
    this.details = options?.details
    this.name = 'ApiError'
  }
}

export class ApiClient {
  private readonly baseUrl: string
  private readonly fetchFn: typeof globalThis.fetch

  constructor(options: ApiClientOptions = {}) {
    const envBaseUrl = typeof import.meta !== 'undefined' ? import.meta.env?.VITE_API_BASE_URL : undefined
    this.baseUrl = options.baseUrl ?? envBaseUrl ?? 'http://localhost:8001'
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
      let timeoutEvent: StatementTimeoutEvent | undefined

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

      if (isStatementTimeoutErrorResponse(errorBody)) {
        timeoutEvent = {
          message: errorBody.message,
          timeoutDuration: errorBody.timeout_duration,
          details: errorBody.details,
        }

        console.warn('API statement timeout', {
          endpoint: url,
          timeout: timeoutEvent.timeoutDuration,
          context: timeoutEvent.details?.context,
        })

        notifyStatementTimeout(timeoutEvent)
      }

      throw new ApiError(
        `Request to ${url} failed with status ${response.status}`,
        response.status,
        errorBody,
        timeoutEvent
          ? {
              errorType: 'statement_timeout',
              timeoutDuration: timeoutEvent.timeoutDuration,
              details: timeoutEvent.details,
            }
          : undefined
      )
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

// Default instance
export const apiClient = new ApiClient()

export function isStatementTimeoutError(error: unknown): error is ApiError {
  return error instanceof ApiError && error.errorType === 'statement_timeout'
}

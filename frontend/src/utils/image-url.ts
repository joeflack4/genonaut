/**
 * Utility functions for constructing image URLs that work across different environments.
 */

/**
 * Get the API base URL from environment or default to localhost:8001
 */
function getApiBaseUrl(): string {
  const envBaseUrl = typeof import.meta !== 'undefined' ? import.meta.env?.VITE_API_BASE_URL : undefined
  return envBaseUrl ?? 'http://localhost:8001'
}

/**
 * Construct a full image URL from a content ID.
 *
 * @param contentId - The content item ID
 * @param thumbnail - Optional thumbnail size ('small', 'medium', 'large')
 * @returns Full URL to the image
 */
export function getImageUrl(contentId: number, thumbnail?: 'small' | 'medium' | 'large'): string {
  const baseUrl = getApiBaseUrl()
  const path = `/api/v1/images/${contentId}`
  const url = `${baseUrl}${path}`

  if (thumbnail) {
    return `${url}?thumbnail=${thumbnail}`
  }

  return url
}

/**
 * Construct a full image URL from a relative or absolute path.
 * If the path is already absolute (starts with http), returns it as-is.
 *
 * @param path - The image path (relative or absolute)
 * @returns Full URL to the image
 */
export function getImageUrlFromPath(path: string): string {
  // If already an absolute URL, return as-is
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }

  const baseUrl = getApiBaseUrl()

  // If path starts with /api, it's a relative API path
  if (path.startsWith('/api/')) {
    return `${baseUrl}${path}`
  }

  // Otherwise, it's a file path - this shouldn't happen in production but handle it
  return path
}

/**
 * Resolve the best available image source from provided candidates.
 * Falls back to the API content endpoint when only filesystem paths are available.
 */
export function resolveImageSourceCandidates(contentId: number | undefined, ...candidates: Array<string | null | undefined>): string | null {
  const sanitized = candidates
    .map((candidate) => candidate?.trim())
    .filter((candidate): candidate is string => Boolean(candidate && candidate.length > 0))

  for (const candidate of sanitized) {
    if (candidate.startsWith('data:') || candidate.startsWith('blob:')) {
      return candidate
    }

    if (candidate.startsWith('http://') || candidate.startsWith('https://')) {
      return candidate
    }

    const resolved = getImageUrlFromPath(candidate)
    if (resolved.startsWith('http://') || resolved.startsWith('https://')) {
      return resolved
    }
  }

  if (typeof contentId === 'number' && Number.isFinite(contentId)) {
    return getImageUrl(contentId)
  }

  return sanitized.length > 0 ? sanitized[0] : null
}

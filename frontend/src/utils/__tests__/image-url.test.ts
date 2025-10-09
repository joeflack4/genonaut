import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { getImageUrl, getImageUrlFromPath, resolveImageSourceCandidates } from '../image-url'

describe('image-url utilities', () => {
  describe('getImageUrl', () => {
    beforeEach(() => {
      // Reset environment before each test
      vi.unstubAllEnvs()
    })

    afterEach(() => {
      vi.unstubAllEnvs()
    })

    it('should construct image URL with content ID', () => {
      const url = getImageUrl(12345)
      expect(url).toBe('http://localhost:8001/api/v1/images/12345')
    })

    it('should construct image URL with thumbnail parameter', () => {
      const url = getImageUrl(12345, 'medium')
      expect(url).toBe('http://localhost:8001/api/v1/images/12345?thumbnail=medium')
    })

    it('should use VITE_API_BASE_URL when set', () => {
      vi.stubEnv('VITE_API_BASE_URL', 'https://api.production.com')
      const url = getImageUrl(12345)
      expect(url).toBe('https://api.production.com/api/v1/images/12345')
    })

    it('should support all thumbnail sizes', () => {
      expect(getImageUrl(1, 'small')).toContain('thumbnail=small')
      expect(getImageUrl(1, 'medium')).toContain('thumbnail=medium')
      expect(getImageUrl(1, 'large')).toContain('thumbnail=large')
    })
  })

  describe('getImageUrlFromPath', () => {
    it('should return absolute HTTP URLs unchanged', () => {
      const url = 'http://example.com/image.png'
      expect(getImageUrlFromPath(url)).toBe(url)
    })

    it('should return absolute HTTPS URLs unchanged', () => {
      const url = 'https://example.com/image.png'
      expect(getImageUrlFromPath(url)).toBe(url)
    })

    it('should prepend base URL to relative API paths', () => {
      const path = '/api/v1/images/12345'
      expect(getImageUrlFromPath(path)).toBe('http://localhost:8001/api/v1/images/12345')
    })

    it('should return file paths unchanged', () => {
      const path = '/path/to/local/file.png'
      expect(getImageUrlFromPath(path)).toBe(path)
    })

    it('should use VITE_API_BASE_URL for API paths', () => {
      vi.stubEnv('VITE_API_BASE_URL', 'https://api.production.com')
      const path = '/api/v1/images/12345'
      expect(getImageUrlFromPath(path)).toBe('https://api.production.com/api/v1/images/12345')
    })
  })

  describe('resolveImageSourceCandidates', () => {
    beforeEach(() => {
      vi.unstubAllEnvs()
    })

    afterEach(() => {
      vi.unstubAllEnvs()
    })

    it('returns data URLs immediately', () => {
      const result = resolveImageSourceCandidates(10, 'data:image/png;base64,abc')
      expect(result).toBe('data:image/png;base64,abc')
    })

    it('returns absolute URLs without modification', () => {
      const result = resolveImageSourceCandidates(11, 'https://cdn.example.com/image.png')
      expect(result).toBe('https://cdn.example.com/image.png')
    })

    it('converts relative API paths using the base URL', () => {
      const result = resolveImageSourceCandidates(12, '/api/v1/images/12')
      expect(result).toBe('http://localhost:8001/api/v1/images/12')
    })

    it('falls back to content ID when only filesystem paths are available', () => {
      const result = resolveImageSourceCandidates(13, '/Users/test/image.png')
      expect(result).toBe('http://localhost:8001/api/v1/images/13')
    })

    it('returns null when no candidates and no content ID', () => {
      const result = resolveImageSourceCandidates(undefined, null, undefined)
      expect(result).toBeNull()
    })
  })
})

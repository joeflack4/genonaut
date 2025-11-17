/**
 * Feature flags and configuration for frontend functionality
 *
 * This file contains feature toggles and configuration that can be used to
 * enable/disable features or switch between different implementations.
 */

export const FEATURES_CONFIG = {
  /**
   * Pagination configuration
   */
  PAGINATION: {
    /**
     * Use cursor-based pagination vs offset-based pagination
     *
     * - false (default): Use simple offset-based pagination (?p=2).
     *   Reliable, debuggable, sufficient for datasets < 10,000 items
     *
     * - true: Use cursor-based pagination with internal cursor caching.
     *   Better performance for large datasets but more complex
     *
     * Note: The backend supports both modes automatically based on parameters sent.
     * This flag only controls what the frontend sends to the API.
     */
    USE_CURSOR_PAGINATION: false,

    /**
     * Page size for gallery pagination
     */
    DEFAULT_PAGE_SIZE: 50,

    /**
     * Maximum allowed page size
     */
    MAX_PAGE_SIZE: 100,
  },

  /**
   * Virtual scrolling configuration
   */
  VIRTUAL_SCROLLING: {
    /**
     * Enable virtual scrolling for large galleries
     */
    ENABLED: false,

    /**
     * Page size when virtual scrolling is enabled
     */
    PAGE_SIZE: 200,
  },
} as const

// Type export for type-safe access
export type FeaturesConfig = typeof FEATURES_CONFIG
/**
 * Frontend UI configuration
 *
 * This file contains configuration values for UI behavior, timeouts, and other
 * frontend-specific settings.
 */

export const UI_CONFIG = {
  /**
   * Time in milliseconds before showing "request taking longer than expected" warning
   * during image generation.
   */
  GENERATION_TIMEOUT_WARNING_MS: 60000, // 60 seconds

  /**
   * Minimum duration in milliseconds to show the submission state to prevent
   * UI flashing on fast requests.
   */
  MIN_SUBMIT_DURATION_MS: 300,
} as const

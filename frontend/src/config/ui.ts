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

  /**
   * Maximum number of recent search history items to display in dropdown widgets
   * (navbar and gallery sidebar).
   */
  SEARCH_HISTORY_DROPDOWN_LIMIT: 5,

  /**
   * Notification/Toast/Snackbar display configuration
   */
  NOTIFICATIONS: {
    /**
     * Default auto-hide durations for each notification severity type (in milliseconds).
     * Set to null to disable auto-hide for that type.
     */
    AUTO_HIDE_DURATION: {
      error: null, // Errors stay on screen until manually dismissed
      warning: 8000, // 8 seconds
      info: 6000, // 6 seconds
      success: 4000, // 4 seconds
    },

    /**
     * If true, all notifications will stay on screen until manually dismissed,
     * overriding individual AUTO_HIDE_DURATION settings.
     */
    DISABLE_AUTO_HIDE: false,

    /**
     * Default position for notifications
     */
    POSITION: {
      vertical: 'bottom' as const,
      horizontal: 'left' as const,
    },
  },
} as const

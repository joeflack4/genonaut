/**
 * Debug logging utilities
 *
 * These utilities provide conditional logging based on environment variables.
 * Debug logs are only shown when VITE_DEBUG_GENERATION is set to 'true'.
 *
 * Usage:
 * - Development (no debug): `npm run dev` or `make frontend-dev`
 * - Development (with debug): `npm run dev:debug` or `make frontend-dev-debug`
 */

/**
 * Check if generation debug logging is enabled
 */
export const isGenerationDebugEnabled = (): boolean => {
  return import.meta.env.VITE_DEBUG_GENERATION === 'true'
}

/**
 * Conditional debug logger for generation-related components
 * Only logs when VITE_DEBUG_GENERATION=true
 */
export const debugLog = {
  generation: (...args: unknown[]): void => {
    if (isGenerationDebugEnabled()) {
      console.log(...args)
    }
  },

  generationDebug: (...args: unknown[]): void => {
    if (isGenerationDebugEnabled()) {
      console.debug(...args)
    }
  },

  generationWarn: (...args: unknown[]): void => {
    if (isGenerationDebugEnabled()) {
      console.warn(...args)
    }
  },
}

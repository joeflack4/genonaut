/// <reference types="vite/client" />

// Global constants injected by Vite
declare const __ADMIN_USER_ID__: string

// Custom environment variables
interface ImportMetaEnv {
  readonly VITE_DEBUG_GENERATION?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

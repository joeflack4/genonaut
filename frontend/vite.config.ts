import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import { readFileSync } from 'fs'

// Read environment variables from the parent directory's env/.env file
function loadParentEnv() {
  try {
    const envPath = resolve(__dirname, '../env/.env')
    const envContent = readFileSync(envPath, 'utf-8')
    const envVars: Record<string, string> = {}

    for (const line of envContent.split('\n')) {
      const trimmed = line.trim()
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=')
        if (key && valueParts.length > 0) {
          envVars[key] = valueParts.join('=')
        }
      }
    }

    return envVars
  } catch (error) {
    console.warn('Could not load parent .env file:', error)
    return {}
  }
}

const parentEnv = loadParentEnv()

export default defineConfig({
  plugins: [react()],
  define: {
    // Inject the admin user UUID as a build-time constant
    __ADMIN_USER_ID__: JSON.stringify(parentEnv.DB_USER_ADMIN_UUID || '121e194b-4caa-4b81-ad4f-86ca3919d5b9'),
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: ['tests/e2e/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
    },
  },
})

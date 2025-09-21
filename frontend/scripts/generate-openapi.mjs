import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const schemaUrl = process.env.OPENAPI_SCHEMA_URL ?? 'http://localhost:8000/openapi.json'
const outputPath = process.env.OPENAPI_OUTPUT ?? 'src/types/openapi.ts'

const currentDir = dirname(fileURLToPath(import.meta.url))
const projectRoot = resolve(currentDir, '..')

const command = process.platform === 'win32' ? 'npx.cmd' : 'npx'

const result = spawnSync(command, ['openapi-typescript', schemaUrl, '--output', outputPath], {
  cwd: projectRoot,
  stdio: 'inherit',
})

if (result.error) {
  console.error(result.error)
  process.exit(1)
}

if (result.status !== 0) {
  process.exit(result.status ?? 1)
}

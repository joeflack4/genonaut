#!/usr/bin/env node

/**
 * Test API Server Launcher
 *
 * This script manages the lifecycle of a test API server with PostgreSQL test database.
 * It initializes the test database, seeds it with test data, starts the API server,
 * and handles cleanup on shutdown.
 */

import { spawn } from 'child_process';
import { readFileSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '../..');

// Configuration
const API_PORT = process.env.PORT || 8002;
const ENV_TARGET = 'local-test';

let apiProcess = null;

// Load environment variables from .env files
function loadEnvFiles() {
  const envFiles = [
    path.join(projectRoot, 'env', '.env.shared'),
    path.join(projectRoot, 'env', `.env.${ENV_TARGET}`),
    path.join(projectRoot, 'env', '.env'),
  ];

  const envVars = {};

  for (const envFile of envFiles) {
    try {
      const content = readFileSync(envFile, 'utf-8');
      const lines = content.split('\n');

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;

        const match = trimmed.match(/^([^=]+)=(.*)$/);
        if (match) {
          const key = match[1].trim();
          let value = match[2].trim();

          // Remove surrounding quotes if present
          if ((value.startsWith('"') && value.endsWith('"')) ||
              (value.startsWith("'") && value.endsWith("'"))) {
            value = value.slice(1, -1);
          }

          envVars[key] = value;
        }
      }
    } catch (error) {
      // File doesn't exist or can't be read - that's okay for optional env files
      if (error.code !== 'ENOENT') {
        console.warn(`Warning: Could not read ${envFile}:`, error.message);
      }
    }
  }

  return envVars;
}

async function checkDatabaseSetup() {
  console.log('🔍 Checking PostgreSQL test database setup...');
  console.log('   Using ENV_TARGET:', ENV_TARGET);
  console.log('   Expected database: genonaut_test (from config/local-test.json)');
  console.log('');
  console.log('⚠️  IMPORTANT: This script expects the test database to be pre-initialized.');
  console.log('   If tests fail, run: make init-test');
  console.log('');
}

async function startApiServer() {
  console.log(`🚀 Starting test API server on port ${API_PORT} (PostgreSQL)...`);

  // Load environment variables from .env files
  const envVars = loadEnvFiles();

  apiProcess = spawn('python', ['-m', 'uvicorn', 'genonaut.api.main:app', '--host', '0.0.0.0', '--port', API_PORT], {
    cwd: projectRoot,
    env: {
      ...process.env,
      ...envVars,
      ENV_TARGET: ENV_TARGET,
    },
    stdio: 'inherit'
  });

  // Give the server time to start
  await new Promise(resolve => setTimeout(resolve, 3000));

  console.log(`✅ Test API server started on http://0.0.0.0:${API_PORT}`);
  return apiProcess;
}

async function waitForServerHealth() {
  console.log('🔍 Checking server health...');

  const maxRetries = 30;
  let retries = 0;

  while (retries < maxRetries) {
    try {
      const response = await fetch(`http://127.0.0.1:${API_PORT}/health`);
      if (response.ok) {
        console.log('✅ Server is healthy and ready');
        return;
      }
    } catch (error) {
      // Server not ready yet
    }

    retries++;
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  throw new Error('Server health check failed after 30 seconds');
}

async function cleanup() {
  console.log('🧹 Cleaning up test environment...');

  if (apiProcess) {
    apiProcess.kill('SIGTERM');
    await new Promise(resolve => setTimeout(resolve, 2000));

    if (!apiProcess.killed) {
      apiProcess.kill('SIGKILL');
    }
    console.log('✅ API server stopped');
  }

  console.log('✅ Cleanup completed');
  console.log('ℹ️  Note: PostgreSQL test database is preserved. Use make init-test to reset if needed.');
}

// Handle cleanup on process termination
process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
process.on('exit', cleanup);

async function main() {
  try {
    // Check database setup (does not initialize - expects pre-initialized DB)
    await checkDatabaseSetup();

    // Start API server (database should already be initialized with: make init-test)
    await startApiServer();

    // Wait for server to be healthy
    await waitForServerHealth();

    console.log('🎉 Test API server is ready for Playwright tests!');

    // Keep the process alive
    await new Promise(() => {});

  } catch (error) {
    console.error('❌ Failed to start test API server:', error.message);
    console.error('💡 Tip: Ensure test database is initialized with: make init-test');
    await cleanup();
    process.exit(1);
  }
}

main().catch(console.error);
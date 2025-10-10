#!/usr/bin/env node

/**
 * Test API Server Launcher
 *
 * This script manages the lifecycle of a test API server with SQLite database.
 * It creates a test database, seeds it with test data, starts the API server,
 * and handles cleanup on shutdown.
 */

import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '../..');

// Configuration
const TEST_DB_PATH = path.join(projectRoot, 'frontend', 'tests', 'e2e', 'output', 'test_playwright.db');
const API_PORT = process.env.PORT || 8002;
const APP_ENV = 'test';

let apiProcess = null;

async function cleanupTestDatabase() {
  try {
    await fs.unlink(TEST_DB_PATH);
    console.log(`✅ Cleaned up test database: ${TEST_DB_PATH}`);
  } catch (error) {
    if (error.code !== 'ENOENT') {
      console.warn(`⚠️  Warning: Could not clean up test database: ${error.message}`);
    }
  }
}

async function initializeTestDatabase() {
  console.log('📦 Initializing test database...');

  const initProcess = spawn('python', ['-m', 'genonaut.db.init'], {
    cwd: projectRoot,
    env: {
      ...process.env,
      GENONAUT_DB_ENVIRONMENT: 'test',
      DATABASE_URL: `sqlite:///${TEST_DB_PATH}`,
      DATABASE_URL_TEST: `sqlite:///${TEST_DB_PATH}`,
    },
    stdio: 'inherit'
  });

  return new Promise((resolve, reject) => {
    initProcess.on('close', (code) => {
      if (code === 0) {
        console.log('✅ Test database initialized successfully');
        resolve();
      } else {
        reject(new Error(`Database initialization failed with code ${code}`));
      }
    });
  });
}

async function startApiServer() {
  console.log(`🚀 Starting test API server on port ${API_PORT}...`);

  apiProcess = spawn('python', ['-m', 'uvicorn', 'genonaut.api.main:app', '--host', '0.0.0.0', '--port', API_PORT], {
    cwd: projectRoot,
    env: {
      ...process.env,
      APP_ENV: APP_ENV,
      DATABASE_URL: `sqlite:///${TEST_DB_PATH}`,
      DATABASE_URL_TEST: `sqlite:///${TEST_DB_PATH}`,
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

  await cleanupTestDatabase();
  console.log('✅ Cleanup completed');
}

// Handle cleanup on process termination
process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
process.on('exit', cleanup);

async function main() {
  try {
    // Cleanup any existing test database
    await cleanupTestDatabase();

    // Initialize new test database
    await initializeTestDatabase();

    // Start API server
    await startApiServer();

    // Wait for server to be healthy
    await waitForServerHealth();

    console.log('🎉 Test API server is ready for Playwright tests!');

    // Keep the process alive
    await new Promise(() => {});

  } catch (error) {
    console.error('❌ Failed to start test API server:', error.message);
    await cleanup();
    process.exit(1);
  }
}

main().catch(console.error);
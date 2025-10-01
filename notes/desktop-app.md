# Desktop App Deployment Specification

## Executive Summary

This document outlines the strategy for packaging Genonaut as a cross-platform desktop application for Windows, macOS, and Linux using Electron. Genonaut is a full-stack application with a React frontend (Vite), FastAPI backend (Python), and PostgreSQL database, requiring careful architecture to bundle and run all components seamlessly.

## Architecture Overview

### Current Stack
- **Frontend**: React 19 + Vite + TypeScript + Material-UI
- **Backend**: FastAPI (Python 3.10+) with REST API
- **Database**: PostgreSQL with JSONB support
- **External Services**: ComfyUI integration for AI generation

### Desktop App Architecture
```
┌─────────────────────────────────────────┐
│          Electron Main Process          │
│  - Window Management                    │
│  - Process Orchestration                │
│  - IPC Communication                    │
│  - Auto-updates                         │
└──────────────┬──────────────────────────┘
               │
     ┌─────────┴──────────┐
     │                    │
┌────▼─────┐      ┌──────▼────────┐
│ Renderer │      │   Backend     │
│ Process  │      │   Processes   │
│          │      │               │
│ React    │◄────►│ FastAPI       │
│ Frontend │ HTTP │ (Bundled)     │
└──────────┘      │               │
                  │ PostgreSQL    │
                  │ (Embedded)    │
                  └───────────────┘
```

## Technology Selection

### Core Framework: Electron
- **Why Electron**:
  - Cross-platform compatibility (Windows, macOS, Linux)
  - Excellent TypeScript/React integration
  - Large ecosystem and tooling support
  - Active maintenance and security updates
  - Can bundle complex multi-process applications

### Key Dependencies
- **electron**: Main framework (~7.0.0)
- **electron-builder**: Build and packaging tool
- **electron-store**: Persistent configuration storage
- **electron-updater**: Auto-update functionality
- **node-pty**: Terminal emulation for backend processes
- **better-sqlite3** or **pg-native**: Embedded database options

### Backend Bundling Options
1. **PyInstaller** (Recommended): Freeze Python app into standalone executable
2. **Nuitka**: Compile Python to C for better performance
3. **PyOxidizer**: Rust-based Python packaging

### Database Options
1. **Embedded PostgreSQL**: Bundle postgres binaries per platform
2. **SQLite Migration**: Convert schema to SQLite for simpler distribution (requires code changes)
3. **Hybrid Approach**: SQLite for desktop, PostgreSQL optional for power users

## Implementation Phases

---

## Phase 1: Project Setup & Foundation
**Goal**: Establish Electron project structure and development environment

### Tasks

- [ ] **1.1 Initialize Electron project structure**
  - Create `desktop/` directory in project root
  - Initialize with `npm init` and install core dependencies:
    ```bash
    npm install --save electron electron-builder
    npm install --save-dev electron-dev electron-reload
    ```
  - Set up TypeScript configuration for Electron main process
  - Configure ESLint for Electron-specific patterns

- [ ] **1.2 Create main process entry point**
  - Create `desktop/src/main/main.ts`
  - Implement window creation with React DevTools support
  - Configure IPC (Inter-Process Communication) channels
  - Set up security policies (CSP, context isolation)
  - Handle app lifecycle events (ready, window-all-closed, activate)

- [ ] **1.3 Configure Electron development environment**
  - Set up hot-reload for main process changes
  - Configure environment variables for dev/prod modes
  - Create development startup script that:
    - Starts Vite dev server
    - Launches Electron with proper flags
  - Add npm scripts to `desktop/package.json`:
    ```json
    {
      "scripts": {
        "dev": "electron-dev",
        "dev:frontend": "npm run dev --prefix ../frontend",
        "dev:all": "concurrently \"npm run dev:frontend\" \"npm run dev\""
      }
    }
    ```

- [ ] **1.4 Integrate frontend with Electron**
  - Modify `frontend/vite.config.ts` for Electron compatibility:
    - Set base path to `./` for file:// protocol
    - Configure build output directory
    - Disable HMR for production builds
  - Create preload script (`desktop/src/preload/preload.ts`) for secure frontend-main communication
  - Test loading React app in Electron window
  - Verify React Router works in Electron environment

- [ ] **1.5 Set up basic IPC architecture**
  - Define IPC channel contracts (TypeScript interfaces)
  - Implement typed IPC handlers in main process
  - Create frontend IPC client utilities
  - Test bidirectional communication
  - Document IPC API for future development

**Verification Criteria**:
- ✅ Electron window opens and displays React frontend
- ✅ Hot reload works for both main process and renderer
- ✅ IPC communication successfully passes data between processes
- ✅ No console errors or warnings
- ✅ TypeScript compilation succeeds for all Electron code

**Estimated Time**: 3-5 days

---

## Phase 2: Backend Integration
**Goal**: Bundle and manage FastAPI backend within Electron

### Tasks

- [ ] **2.1 Research and select Python bundling solution**
  - Evaluate PyInstaller vs Nuitka vs PyOxidizer for Genonaut's requirements
  - Test each tool with a minimal FastAPI app
  - Consider factors:
    - Build time
    - Binary size
    - Startup time
    - Compatibility with dependencies (SQLAlchemy, Alembic, etc.)
    - Cross-compilation support
  - Document decision with benchmark results

- [ ] **2.2 Configure Python application bundling**
  - Create PyInstaller spec file (`genonaut.spec`) if using PyInstaller:
    ```python
    # Key considerations:
    # - Include all Python dependencies
    # - Bundle alembic migrations
    # - Include static files (flag-words.txt, etc.)
    # - Handle hidden imports (SQLAlchemy models, etc.)
    ```
  - Set up build scripts for each platform:
    - `scripts/build-backend-linux.sh`
    - `scripts/build-backend-macos.sh`
    - `scripts/build-backend-windows.bat`
  - Test bundled binary runs independently
  - Verify all API endpoints work in bundled version

- [ ] **2.3 Implement backend process management**
  - Create `desktop/src/main/backend-manager.ts`:
    - Start backend process on app launch
    - Monitor process health (ping health endpoint)
    - Capture stdout/stderr for logging
    - Restart on unexpected crashes (with exponential backoff)
    - Graceful shutdown on app quit
  - Implement port conflict detection and auto-assignment
  - Add timeout and retry logic for backend startup
  - Create status indicator for backend readiness

- [ ] **2.4 Handle backend binary paths and resources**
  - Detect correct binary path for dev vs production:
    ```typescript
    const backendPath = app.isPackaged
      ? path.join(process.resourcesPath, 'backend', 'genonaut')
      : path.join(__dirname, '../../backend/dist/genonaut');
    ```
  - Bundle Python environment and dependencies
  - Include migration files and seed data
  - Handle platform-specific binary names (.exe on Windows)
  - Set up proper file permissions on Unix systems

- [ ] **2.5 Configure backend for desktop environment**
  - Modify `genonaut/api/config.py` to detect Electron environment
  - Set default values suitable for desktop (e.g., `localhost` only)
  - Create desktop-specific configuration profile
  - Disable features not needed in desktop mode (cloud-specific features)
  - Add Electron-specific health check endpoint

- [ ] **2.6 Implement frontend-backend communication bridge**
  - Configure frontend to connect to dynamic backend port
  - Implement IPC channel to get backend URL: `ipcMain.handle('get-backend-url')`
  - Update frontend API client configuration:
    ```typescript
    const API_BASE_URL = await window.electron.getBackendUrl();
    ```
  - Handle backend connection errors gracefully in UI
  - Add retry logic for API requests during startup

- [ ] **2.7 Create logging and debugging infrastructure**
  - Set up Winston or similar logger in main process
  - Capture backend logs and write to user data directory
  - Create log viewer in app settings (Help > View Logs)
  - Implement log rotation to prevent disk space issues
  - Add "Open Logs Folder" menu item for troubleshooting

**Verification Criteria**:
- ✅ Backend starts automatically when app launches
- ✅ Frontend successfully connects to backend
- ✅ All API endpoints respond correctly
- ✅ Backend shuts down cleanly when app closes
- ✅ Logs are captured and viewable
- ✅ Backend restarts automatically if it crashes
- ✅ Works on all three target platforms

**Estimated Time**: 7-10 days

---

## Phase 3: Database Integration
**Goal**: Embed and manage PostgreSQL (or alternative) database

### Tasks

- [ ] **3.1 Evaluate database options**
  - **Option A: Embedded PostgreSQL**
    - Research pg-embed, embedded-postgres, or manual binary bundling
    - Test startup time and resource usage
    - Evaluate data portability and backup complexity
  - **Option B: SQLite Migration**
    - Analyze schema compatibility (JSONB, indexes, etc.)
    - Estimate code changes needed in repositories
    - Test performance with realistic data volumes
  - **Option C: Hybrid Approach**
    - SQLite as default, optional PostgreSQL for advanced users
    - Implement abstraction layer for database switching
  - Document recommendation with pros/cons analysis

- [ ] **3.2 Bundle database binaries (if using PostgreSQL)**
  - Download postgres binaries for each platform:
    - Linux: x64, arm64
    - macOS: x64 (Intel), arm64 (Apple Silicon)
    - Windows: x64
  - Strip unnecessary components (docs, dev headers, etc.)
  - Create platform-specific initialization scripts
  - Test binary sizes and optimize (target <100MB per platform)
  - Verify binaries work on older OS versions (Windows 10, macOS 10.15, Ubuntu 20.04)

- [ ] **3.3 Implement database lifecycle management**
  - Create `desktop/src/main/database-manager.ts`:
    - Initialize database on first run (create data directory)
    - Start database process with appropriate configuration
    - Generate random password on first init
    - Store connection details in electron-store
    - Monitor database health
    - Handle port conflicts
    - Backup database on version upgrades
    - Graceful shutdown on app quit
  - Implement database version detection
  - Add database reset functionality (for troubleshooting)

- [ ] **3.4 Run Alembic migrations on app startup**
  - Bundle alembic.ini and migrations/ directory
  - Create migration runner that:
    - Checks current database schema version
    - Applies pending migrations automatically
    - Shows progress indicator in UI
    - Handles migration failures gracefully (rollback)
    - Logs migration history
  - Test upgrade path from older versions
  - Implement pre-migration backup

- [ ] **3.5 Configure data persistence and location**
  - Store database files in app.getPath('userData'):
    - Windows: `%APPDATA%/Genonaut/data/`
    - macOS: `~/Library/Application Support/Genonaut/data/`
    - Linux: `~/.config/genonaut/data/`
  - Implement database backup functionality:
    - Automatic backups before migrations
    - Manual backup option in settings
    - Configurable backup retention (default: keep last 5)
  - Add database size monitoring
  - Create "Open Data Folder" menu item

- [ ] **3.6 Handle database initialization and seeding**
  - Run database initialization on first launch:
    - Create schema via Alembic
    - Create default admin user
    - Optionally load demo data (user choice)
  - Show first-run welcome screen with setup options
  - Create progress indicator for long-running operations
  - Handle initialization failures with clear error messages

- [ ] **3.7 Implement database export/import**
  - Add "Export Database" feature:
    - pg_dump for PostgreSQL or .db copy for SQLite
    - Save to user-selected location
    - Include metadata (version, timestamp)
  - Add "Import Database" feature:
    - Validate backup file before import
    - Show confirmation dialog (data will be overwritten)
    - Create safety backup before import
  - Document backup file format and location

**Verification Criteria**:
- ✅ Database initializes successfully on first run
- ✅ Database starts/stops with application lifecycle
- ✅ Migrations run automatically on app updates
- ✅ Data persists between app restarts
- ✅ Database can be backed up and restored
- ✅ Database size stays reasonable (<500MB for demo data)
- ✅ No data corruption after force quit
- ✅ Works on all three target platforms

**Estimated Time**: 10-14 days

---

## Phase 4: Build Configuration & Packaging
**Goal**: Configure electron-builder for multi-platform distribution

### Tasks

- [ ] **4.1 Configure electron-builder**
  - Create `desktop/electron-builder.json`:
    ```json
    {
      "appId": "com.genonaut.app",
      "productName": "Genonaut",
      "directories": {
        "output": "dist"
      },
      "files": [
        "dist/**/*",
        "resources/**/*"
      ],
      "extraResources": [
        {
          "from": "../genonaut/dist/",
          "to": "backend/",
          "filter": ["**/*"]
        },
        {
          "from": "db-binaries/${platform}/",
          "to": "database/",
          "filter": ["**/*"]
        }
      ]
    }
    ```
  - Configure compression settings for size optimization
  - Set up file associations for .genonaut project files (future)

- [ ] **4.2 Set up macOS build configuration**
  - Configure macOS-specific settings:
    ```json
    "mac": {
      "category": "public.app-category.graphics-design",
      "target": ["dmg", "zip"],
      "icon": "resources/icons/mac/icon.icns",
      "hardenedRuntime": true,
      "gatekeeperAssess": false,
      "entitlements": "resources/entitlements.mac.plist",
      "entitlementsInherit": "resources/entitlements.mac.plist"
    }
    ```
  - Create .icns icon file (1024x1024 base resolution)
  - Configure DMG appearance (background image, window size, icon position)
  - Set up code signing with Apple Developer certificate:
    - Obtain Developer ID Application certificate
    - Configure notarization for macOS Catalina+
    - Add signing identities to build config
  - Create entitlements.plist for necessary permissions
  - Test on both Intel and Apple Silicon Macs

- [ ] **4.3 Set up Windows build configuration**
  - Configure Windows-specific settings:
    ```json
    "win": {
      "target": ["nsis", "portable"],
      "icon": "resources/icons/win/icon.ico",
      "publisherName": "Genonaut",
      "verifyUpdateCodeSignature": false
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true,
      "shortcutName": "Genonaut"
    }
    ```
  - Create .ico icon file (256x256 max resolution in ICO)
  - Configure installer settings (custom install location, add to PATH option)
  - Set up code signing with Windows certificate (optional for initial release)
  - Test on Windows 10 and Windows 11

- [ ] **4.4 Set up Linux build configuration**
  - Configure Linux-specific settings:
    ```json
    "linux": {
      "target": ["AppImage", "deb", "rpm", "snap"],
      "icon": "resources/icons/linux/",
      "category": "Graphics",
      "synopsis": "AI Art Generation & Recommendation Platform",
      "description": "Genonaut: Recommender systems & perpetual generation for gen AI"
    }
    ```
  - Create icon set (16x16 to 512x512 PNG files)
  - Configure desktop file (.desktop) for app launcher integration
  - Set up AppImage configuration (universal Linux binary)
  - Test on Ubuntu 22.04, Fedora, and Arch Linux

- [ ] **4.5 Optimize bundle size**
  - Analyze bundle size with electron-builder's size analyzer
  - Exclude development dependencies from production build
  - Compress database binaries
  - Strip debug symbols from Python binaries
  - Use asarUnpack for specific files that must remain uncompressed
  - Target goals:
    - macOS: <300MB DMG
    - Windows: <350MB installer
    - Linux: <300MB AppImage
  - Document size optimization decisions

- [ ] **4.6 Create build automation scripts**
  - Create platform-specific build scripts:
    - `scripts/build-desktop-mac.sh`
    - `scripts/build-desktop-windows.bat`
    - `scripts/build-desktop-linux.sh`
  - Create cross-platform build orchestrator script
  - Add build scripts to package.json:
    ```json
    {
      "scripts": {
        "build:desktop:mac": "electron-builder --mac",
        "build:desktop:win": "electron-builder --win",
        "build:desktop:linux": "electron-builder --linux",
        "build:desktop:all": "electron-builder -mwl"
      }
    }
    ```
  - Document required environment variables for builds
  - Test builds on fresh systems (CI environment)

- [ ] **4.7 Set up CI/CD for desktop builds**
  - Configure GitHub Actions or similar for automated builds
  - Create separate workflows for each platform:
    - macOS builds on macOS runners (required for signing)
    - Windows builds on Windows runners
    - Linux builds on Ubuntu runners
  - Set up secrets for code signing certificates
  - Configure artifact storage for build outputs
  - Add build status badges to README
  - Test full CI pipeline end-to-end

**Verification Criteria**:
- ✅ Builds complete successfully for all platforms
- ✅ Installers run without errors on target systems
- ✅ App launches and all features work
- ✅ Bundle sizes are within acceptable limits
- ✅ Code signing works on macOS and Windows (if configured)
- ✅ Icons display correctly in all contexts
- ✅ CI builds produce valid artifacts
- ✅ Build process is documented and reproducible

**Estimated Time**: 10-12 days

---

## Phase 5: Desktop-Specific Features
**Goal**: Implement native desktop functionality and user experience improvements

### Tasks

- [ ] **5.1 Create native application menus**
  - Implement macOS menu bar (File, Edit, View, Window, Help):
    ```typescript
    const template: MenuItemConstructorOptions[] = [
      {
        label: 'Genonaut',
        submenu: [
          { label: 'About Genonaut', role: 'about' },
          { type: 'separator' },
          { label: 'Preferences...', accelerator: 'CmdOrCtrl+,', click: openSettings },
          { type: 'separator' },
          { role: 'services' },
          { type: 'separator' },
          { role: 'hide' },
          { role: 'hideOthers' },
          { role: 'unhide' },
          { type: 'separator' },
          { role: 'quit' }
        ]
      },
      // ... more menus
    ];
    ```
  - Create Windows/Linux menu bar with equivalent functionality
  - Add keyboard shortcuts consistent with platform conventions
  - Implement context menus for right-click actions
  - Add "Open Recent" menu for recent projects/sessions

- [ ] **5.2 Implement system tray integration**
  - Create system tray icon (16x16 for Windows, 22x22 for Linux, template for macOS)
  - Add tray menu with quick actions:
    - Show/Hide window
    - Quick generate (uses last settings)
    - View generation queue status
    - Pause/Resume background tasks
    - Quit application
  - Implement tray notifications for completed generations
  - Add option to minimize to tray instead of closing
  - Handle single-instance enforcement (no duplicate app instances)

- [ ] **5.3 Configure auto-updater**
  - Integrate electron-updater:
    ```typescript
    import { autoUpdater } from 'electron-updater';

    autoUpdater.checkForUpdatesAndNotify();
    autoUpdater.on('update-available', showUpdateNotification);
    autoUpdater.on('download-progress', showProgressBar);
    autoUpdater.on('update-downloaded', promptUserToInstall);
    ```
  - Configure update server (GitHub Releases or custom)
  - Implement update notification UI:
    - "Update available" dialog
    - Progress bar during download
    - "Restart to install" prompt
  - Add "Check for Updates" menu item
  - Configure update channels (stable, beta, alpha)
  - Test update flow end-to-end

- [ ] **5.4 Implement native notifications**
  - Use Electron's Notification API for system notifications:
    - Generation completed
    - Download finished (models, etc.)
    - Background tasks completed
    - Errors requiring user attention
  - Implement notification preferences (enable/disable per type)
  - Handle notification click actions (bring to front, open specific page)
  - Respect system Do Not Disturb settings
  - Test on all platforms (notification APIs differ)

- [ ] **5.5 Add file system integration**
  - Implement native file dialogs:
    - Import images for generation
    - Export generated content
    - Import/export database backups
    - Select ComfyUI installation directory
  - Add drag-and-drop support:
    - Drop images to upload
    - Drop folders to batch import
  - Register file type associations (optional):
    - .genonaut project files
    - Associate with image types for "Open With"
  - Implement "Open Recent Files" menu
  - Add default save locations with system integration

- [ ] **5.6 Create desktop settings page**
  - Add "Desktop Settings" section in Settings UI:
    - Launch at startup (add to system startup items)
    - Minimize to tray
    - Notification preferences
    - Auto-update settings
    - Hardware acceleration toggle
    - Database location and size
    - Cache settings
  - Implement IPC handlers for system preference changes
  - Use electron-store for persistent desktop-specific settings
  - Add "Reset to Defaults" button

- [ ] **5.7 Implement keyboard shortcuts**
  - Register global shortcuts for common actions:
    - `CmdOrCtrl+N`: New generation
    - `CmdOrCtrl+,`: Open settings
    - `CmdOrCtrl+R`: Refresh current view
    - `CmdOrCtrl+Q`: Quit app
    - `F11`: Toggle fullscreen
  - Add shortcut customization in settings
  - Create "Keyboard Shortcuts" help menu
  - Handle platform-specific differences (Cmd vs Ctrl)
  - Prevent conflicts with system shortcuts

- [ ] **5.8 Add protocol handler**
  - Register custom URL protocol (`genonaut://`):
    ```typescript
    app.setAsDefaultProtocolClient('genonaut');
    ```
  - Handle protocol URLs for deep linking:
    - `genonaut://generate?prompt=...` - Start generation from browser
    - `genonaut://view/content/123` - Open specific content item
    - `genonaut://settings/models` - Open settings page
  - Implement URL parsing and routing
  - Test with external links (emails, web pages)

**Verification Criteria**:
- ✅ All menu items work correctly on each platform
- ✅ System tray functions properly
- ✅ Auto-update downloads and installs successfully
- ✅ Notifications appear and are clickable
- ✅ File dialogs and drag-drop work smoothly
- ✅ Desktop settings persist between sessions
- ✅ Keyboard shortcuts function correctly
- ✅ Protocol handler opens correct pages
- ✅ Features feel native to each platform

**Estimated Time**: 10-14 days

---

## Phase 6: Performance & Optimization
**Goal**: Optimize for desktop performance, memory usage, and user experience

### Tasks

- [ ] **6.1 Optimize application startup time**
  - Profile startup sequence to identify bottlenecks:
    - Measure Electron main process initialization
    - Measure backend startup time
    - Measure database connection time
    - Measure renderer load time
  - Implement lazy loading for non-critical components
  - Defer backend startup until after window is shown
  - Use splash screen during initialization:
    - Show progress indicator
    - Display current initialization step
    - Show app version and branding
  - Optimize backend binary size and loading
  - Target: <3 seconds to visible window, <10 seconds to fully functional
  - Document optimization decisions and trade-offs

- [ ] **6.2 Implement caching strategies**
  - Add disk cache for API responses:
    - Cache model lists (refresh on app start)
    - Cache tag hierarchies
    - Cache user preferences
  - Implement image caching:
    - Store thumbnails locally
    - Set cache size limits (configurable, default 1GB)
    - Implement LRU eviction policy
  - Add in-memory cache for frequently accessed data
  - Use electron-store for persistent app state
  - Add "Clear Cache" option in settings
  - Show cache size in settings UI

- [ ] **6.3 Optimize memory usage**
  - Profile memory consumption during typical usage
  - Implement memory limits for backend process
  - Configure V8 heap size appropriately
  - Optimize image loading (progressive loading, downsampling)
  - Release resources when windows are closed
  - Monitor memory leaks in development:
    - Use Chrome DevTools memory profiler
    - Test with prolonged usage sessions
    - Check for event listener leaks
  - Target: <500MB RAM for idle app, <1.5GB under load

- [ ] **6.4 Implement background task management**
  - Create task queue for background operations:
    - Model downloads
    - Image generations
    - Database maintenance
  - Implement task prioritization
  - Add pause/resume functionality
  - Show task progress in UI:
    - Overall queue status
    - Individual task progress
    - Estimated time remaining
  - Handle task cancellation gracefully
  - Persist task queue state (resume after app restart)

- [ ] **6.5 Optimize database performance**
  - Add connection pooling for database connections
  - Implement query result caching
  - Add database vacuum/optimization on schedule:
    - Run maintenance during idle time
    - Show progress notification
    - Allow manual trigger in settings
  - Optimize indexes for common queries (already done, verify)
  - Monitor and log slow queries (>1 second)
  - Add database performance metrics to health check

- [ ] **6.6 Configure hardware acceleration**
  - Enable GPU acceleration for rendering:
    - Verify on all platforms
    - Add disable option for compatibility
  - Optimize for high-DPI displays:
    - Test on 4K monitors
    - Verify Retina display support on macOS
    - Test Windows scaling factors (100%, 125%, 150%, 200%)
  - Configure for low-end hardware:
    - Reduced animations option
    - Disable non-essential visual effects
    - Optimize for integrated GPUs
  - Test on variety of hardware configurations

- [ ] **6.7 Implement error recovery**
  - Add automatic crash recovery:
    - Save app state before crashes
    - Restore state on restart
    - Show "App crashed, restore previous session?" dialog
  - Implement backend crash recovery:
    - Auto-restart with exponential backoff
    - Show notification if restart fails multiple times
    - Provide manual restart button
  - Add database corruption recovery:
    - Detect corruption on startup
    - Attempt automatic repair
    - Offer restore from backup option
  - Create diagnostic report generator for bug reports

- [ ] **6.8 Add performance monitoring**
  - Implement performance metrics collection:
    - App startup time
    - API response times
    - Memory usage over time
    - Database query performance
  - Create performance dashboard in settings (optional):
    - Real-time metrics
    - Historical graphs
    - Performance score
  - Add telemetry opt-in (with user consent):
    - Anonymous usage statistics
    - Crash reports
    - Performance metrics
  - Document data collection and privacy policy

**Verification Criteria**:
- ✅ App starts in <10 seconds
- ✅ Memory usage stays under 1.5GB during active use
- ✅ No memory leaks after 1-hour stress test
- ✅ Background tasks work reliably
- ✅ Database performance is acceptable (queries <100ms)
- ✅ Hardware acceleration works on all platforms
- ✅ App recovers gracefully from crashes
- ✅ Performance metrics are accurate and useful

**Estimated Time**: 8-10 days

---

## Phase 7: Testing & Quality Assurance
**Goal**: Comprehensive testing across platforms and scenarios

### Tasks

- [ ] **7.1 Set up automated testing for Electron**
  - Configure Spectron or Playwright for Electron testing
  - Create test suite for main process:
    - Window creation and management
    - IPC communication
    - Backend process lifecycle
    - Database initialization
  - Create test suite for integration:
    - Frontend-backend communication
    - File operations
    - Menu actions
    - Keyboard shortcuts
  - Set up CI for automated test runs
  - Achieve 70%+ code coverage for desktop-specific code

- [ ] **7.2 Platform-specific testing**
  - **macOS Testing**:
    - Test on macOS 12 (Monterey), 13 (Ventura), 14 (Sonoma)
    - Test on Intel and Apple Silicon
    - Verify notarization and Gatekeeper
    - Test system permissions (files, notifications)
  - **Windows Testing**:
    - Test on Windows 10 21H2, Windows 11
    - Test with different user permission levels
    - Verify installer/uninstaller
    - Test Windows Defender compatibility
  - **Linux Testing**:
    - Test on Ubuntu 20.04, 22.04, 24.04
    - Test on Fedora latest, Arch Linux
    - Test AppImage, .deb, and .rpm packages
    - Verify Wayland and X11 compatibility

- [ ] **7.3 Create manual testing checklist**
  - **Installation & First Run**:
    - [ ] Clean install completes successfully
    - [ ] First-run wizard works correctly
    - [ ] Database initializes properly
    - [ ] Demo data loads (if selected)
    - [ ] Default settings are appropriate
  - **Core Functionality**:
    - [ ] All API endpoints work
    - [ ] Image generation works
    - [ ] Model downloads work
    - [ ] Search and filtering work
    - [ ] Tag system functions
    - [ ] Recommendations generate
  - **Desktop Features**:
    - [ ] All menu items work
    - [ ] System tray functions
    - [ ] Notifications appear
    - [ ] File dialogs work
    - [ ] Drag-and-drop works
    - [ ] Keyboard shortcuts work
    - [ ] Settings persist
  - **Performance**:
    - [ ] Startup time acceptable
    - [ ] Memory usage reasonable
    - [ ] No UI lag during operations
    - [ ] Background tasks work smoothly
  - **Error Handling**:
    - [ ] Backend crash recovery works
    - [ ] Database errors handled gracefully
    - [ ] Network errors handled
    - [ ] Invalid input handled
  - **Updates**:
    - [ ] Update detection works
    - [ ] Update download works
    - [ ] Update installation works
    - [ ] Data persists after update

- [ ] **7.4 Perform stress testing**
  - Test with large datasets:
    - 10,000+ content items
    - 100+ models installed
    - Multiple concurrent generations
  - Test extended runtime (24+ hours)
  - Test rapid window open/close cycles
  - Test network interruptions during operations
  - Test disk space exhaustion scenarios
  - Test concurrent multi-user scenarios (if applicable)
  - Document performance under stress

- [ ] **7.5 Security testing**
  - Review IPC channel security (no arbitrary code execution)
  - Verify no XSS vulnerabilities in renderer
  - Check for insecure file operations
  - Verify no hardcoded credentials
  - Test with malicious input (SQL injection, path traversal)
  - Run security audit tools:
    - `npm audit`
    - Electron's security checker
  - Review and update dependencies for vulnerabilities

- [ ] **7.6 Accessibility testing**
  - Test keyboard-only navigation
  - Test screen reader compatibility (NVDA, JAWS, VoiceOver)
  - Verify color contrast ratios (WCAG AA)
  - Test with system font size increases
  - Test with reduced motion preferences
  - Verify focus indicators on all interactive elements

- [ ] **7.7 Create beta testing program**
  - Recruit 10-20 beta testers across platforms
  - Create beta distribution channel
  - Set up feedback collection system:
    - Bug reporting form
    - Feature request form
    - Automated crash reporting
  - Document known issues and workarounds
  - Schedule regular beta releases (weekly or bi-weekly)
  - Collect and prioritize beta feedback

- [ ] **7.8 Write test documentation**
  - Create testing guide for contributors
  - Document platform-specific test requirements
  - Create troubleshooting guide for common issues
  - Document performance benchmarks and expectations
  - Create release testing checklist
  - Write end-user testing guide for beta testers

**Verification Criteria**:
- ✅ Automated tests pass on all platforms
- ✅ Manual testing checklist 100% complete
- ✅ No critical bugs remain
- ✅ Performance meets targets
- ✅ Security review complete with no high-severity issues
- ✅ Beta testers report satisfactory experience
- ✅ All documentation is complete and accurate

**Estimated Time**: 10-14 days

---

## Phase 8: Distribution & Release
**Goal**: Publish application and establish update infrastructure

### Tasks

- [ ] **8.1 Set up distribution infrastructure**
  - Choose distribution strategy:
    - **GitHub Releases**: Free, simple, good for open source
    - **Custom update server**: More control, can track analytics
    - **App stores** (future consideration):
      - Mac App Store (requires Apple Developer Program membership)
      - Microsoft Store (requires developer account)
      - Snap Store (Linux)
  - Configure electron-updater for chosen distribution method
  - Set up update server if using custom solution
  - Configure CDN or file hosting for large downloads
  - Set up SSL certificates for update server

- [ ] **8.2 Create release assets**
  - Build production releases for all platforms:
    - macOS: .dmg and .zip
    - Windows: .exe installer and portable .exe
    - Linux: AppImage, .deb, .rpm
  - Generate checksums (SHA256) for all artifacts
  - Code sign macOS and Windows releases
  - Notarize macOS build with Apple
  - Test all release artifacts on clean systems
  - Document file sizes and system requirements

- [ ] **8.3 Write release documentation**
  - Create installation guides per platform:
    - macOS installation guide
    - Windows installation guide
    - Linux installation guide (per distribution)
  - Write upgrade guide (migrating from web version)
  - Create troubleshooting guide:
    - Common installation issues
    - Performance issues
    - Compatibility issues
  - Write changelog (CHANGELOG.md):
    - New features
    - Bug fixes
    - Breaking changes
    - Known issues
  - Create quick start guide for first-time users

- [ ] **8.4 Configure auto-update system**
  - Set up update manifest (latest.yml, latest-mac.yml, latest-linux.yml)
  - Configure update channels:
    - Stable channel (default)
    - Beta channel (opt-in)
    - Alpha channel (for testers)
  - Implement version checking and update prompts
  - Test update from previous version:
    - Full update (new installation)
    - Delta updates (if supported)
  - Configure rollback mechanism for failed updates
  - Test update on all platforms

- [ ] **8.5 Create marketing materials**
  - Design app icon and branding assets (if not already done)
  - Create screenshots and demo videos:
    - Feature highlights
    - Installation walkthrough
    - Quick start tutorial
  - Write app description and feature list
  - Create download landing page on website
  - Prepare social media announcement content
  - Create press release (if applicable)

- [ ] **8.6 Set up analytics and crash reporting**
  - Implement opt-in analytics:
    - Usage statistics
    - Feature adoption rates
    - Performance metrics
  - Configure crash reporting (Sentry, Bugsnag, or similar):
    - Automatic crash uploads
    - Symbolication for stack traces
    - Error grouping and deduplication
  - Set up analytics dashboard
  - Write privacy policy for data collection
  - Implement user consent UI

- [ ] **8.7 Launch beta release**
  - Release beta version to test group:
    - Upload to GitHub Releases (pre-release)
    - Announce on beta testing channels
    - Send download instructions
  - Monitor beta feedback closely:
    - Check crash reports daily
    - Respond to bug reports within 24 hours
    - Collect feature requests
  - Iterate on beta releases (target 2-3 beta versions)
  - Fix critical issues before stable release
  - Update documentation based on feedback

- [ ] **8.8 Launch stable release (v1.0)**
  - Finalize all release assets
  - Upload to all distribution channels
  - Update website with download links
  - Publish announcement:
    - Blog post
    - Social media
    - Email newsletter
    - Reddit, forums, etc.
  - Submit to software directories:
    - AlternativeTo
    - Product Hunt
    - SourceForge (if open source)
  - Monitor initial release:
    - Watch for critical bugs
    - Respond to user questions
    - Track download numbers
  - Plan v1.1 release with feedback and fixes

**Verification Criteria**:
- ✅ All distribution channels are live
- ✅ Auto-update system works reliably
- ✅ Installation guides are clear and accurate
- ✅ Marketing materials are professional
- ✅ Analytics and crash reporting functional
- ✅ Beta testing provides positive feedback
- ✅ Stable release has no critical bugs
- ✅ Community response is positive

**Estimated Time**: 7-10 days

---

## Technical Considerations

### Security
- **Code Signing**: Essential for macOS (notarization required) and recommended for Windows (SmartScreen warnings otherwise)
- **Content Security Policy**: Restrict renderer process capabilities
- **Context Isolation**: Separate renderer and main process contexts
- **nodeIntegration**: Disabled in renderer for security
- **Remote Code Execution**: Prevent via careful IPC design and input validation
- **Update Security**: Verify update signatures before installation

### Performance
- **Bundle Size**: Target <400MB per platform after compression
- **Memory Usage**: Target <500MB idle, <1.5GB under load
- **Startup Time**: <10 seconds to fully functional
- **Database**: PostgreSQL may add 50-100MB and 5-10s startup time
- **Backend**: Python binary adds 30-50MB depending on dependencies

### Platform-Specific Challenges
- **macOS**: Notarization required for Catalina+, code signing complexity, Gatekeeper issues
- **Windows**: SmartScreen warnings without code signing, antivirus false positives, PATH setup
- **Linux**: Multiple package formats needed, varying dependencies, Wayland vs X11 compatibility

### Database Decisions
- **PostgreSQL Pros**: No code changes, full feature parity, JSONB support
- **PostgreSQL Cons**: Large binary size (50-100MB), slower startup, more complex
- **SQLite Pros**: Smaller (<5MB), faster startup, simpler distribution
- **SQLite Cons**: Requires code changes, limited JSONB support, migration effort

### Maintenance Considerations
- **Regular Electron Updates**: New version every 8 weeks
- **Security Patches**: Critical updates may require immediate releases
- **Dependency Updates**: Python, Node.js, and library updates
- **Platform Changes**: OS updates may break functionality
- **Auto-update Infrastructure**: Requires ongoing hosting and monitoring

## Success Metrics

### Pre-Release Goals
- [ ] Builds successfully on all three platforms without errors
- [ ] All core features work identically to web version
- [ ] <10 seconds startup time on modern hardware
- [ ] <400MB installer size per platform
- [ ] <500MB memory usage at idle
- [ ] Zero critical bugs in beta testing
- [ ] 80%+ test coverage for desktop-specific code

### Post-Release Metrics (First 90 Days)
- Downloads: 1,000+ total across platforms
- Crash rate: <1% of sessions
- Update adoption: 70%+ update within 1 week
- User retention: 40%+ weekly active users
- Support requests: <5% of users require support
- Performance: 95%+ of users report acceptable performance
- NPS Score: 40+ (promoters minus detractors)

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Database bundle size too large | High | Medium | Consider SQLite migration or hybrid approach |
| Backend fails to start on some systems | High | Medium | Comprehensive error handling and fallback mechanisms |
| Code signing/notarization issues | High | Low | Research requirements early, test on fresh machines |
| Update mechanism breaks | Medium | Low | Extensive testing, rollback capability |
| Platform-specific bugs | Medium | High | Allocate time for platform-specific fixes |
| Performance issues on low-end hardware | Medium | Medium | Optimize early, test on range of hardware |
| User data loss during updates | High | Low | Backup before updates, test migration paths |
| Antivirus false positives | Medium | Medium | Code signing, submit binaries to vendors |

## Timeline Estimate

- **Phase 1**: 3-5 days
- **Phase 2**: 7-10 days
- **Phase 3**: 10-14 days
- **Phase 4**: 10-12 days
- **Phase 5**: 10-14 days
- **Phase 6**: 8-10 days
- **Phase 7**: 10-14 days
- **Phase 8**: 7-10 days

**Total Estimated Time**: 65-89 days (13-18 weeks)

**Recommended Approach**:
- 1-2 full-time developers: 4-5 months
- 3-4 part-time contributors: 5-7 months
- Include 20% buffer for unexpected issues

## Resources & Next Steps

### Required Skills
- Electron and Node.js expertise
- React and TypeScript knowledge
- Python packaging experience (PyInstaller, etc.)
- Cross-platform build system knowledge
- CI/CD pipeline setup
- Code signing and notarization experience (macOS/Windows)

### External Services Needed
- **Apple Developer Program**: $99/year (for code signing and notarization)
- **Windows Code Signing Certificate**: ~$200-500/year (optional for initial release)
- **File Hosting**: GitHub Releases (free) or CDN ($10-50/month)
- **Crash Reporting Service**: Sentry free tier or paid ($26+/month)
- **Analytics**: Plausible, Mixpanel free tier, or custom

### Recommended Reading
- [Electron Documentation](https://www.electronjs.org/docs)
- [electron-builder Documentation](https://www.electron.build/)
- [Electron Security Best Practices](https://www.electronjs.org/docs/latest/tutorial/security)
- [PyInstaller Manual](https://pyinstaller.org/en/stable/)
- [Code Signing Guide for macOS](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)

### First Steps
1. **Validate Approach**: Create proof-of-concept with Phase 1 tasks (1 week)
2. **Database Decision**: Test PostgreSQL embedding vs SQLite migration (3-5 days)
3. **Backend Bundling**: Test PyInstaller with FastAPI app (2-3 days)
4. **Assess Resources**: Determine team availability and timeline
5. **Create Project Plan**: Break down phases into sprint-ready tasks
6. **Set Up Infrastructure**: Create desktop/ directory, initialize repositories

### Alternative Approaches
- **Tauri** (instead of Electron): Smaller binaries, Rust-based, less mature ecosystem
- **Progressive Web App**: Avoid desktop packaging, limited native features
- **Docker Desktop**: Container-based distribution, more technical users only
- **Native Apps**: Separate Swift/Kotlin/C++ apps per platform, 3x development time

---

## Appendix

### Recommended Project Structure
```
genonaut/
├── desktop/                      # Desktop app root
│   ├── src/
│   │   ├── main/                # Electron main process
│   │   │   ├── main.ts
│   │   │   ├── backend-manager.ts
│   │   │   ├── database-manager.ts
│   │   │   ├── menu.ts
│   │   │   ├── tray.ts
│   │   │   └── updater.ts
│   │   ├── preload/             # Preload scripts
│   │   │   └── preload.ts
│   │   └── renderer/            # Renderer-specific code
│   │       └── ipc-client.ts
│   ├── resources/               # Desktop assets
│   │   ├── icons/
│   │   │   ├── mac/
│   │   │   ├── win/
│   │   │   └── linux/
│   │   ├── splash.html
│   │   └── entitlements.mac.plist
│   ├── scripts/                 # Build scripts
│   │   ├── build-backend.sh
│   │   ├── build-desktop-mac.sh
│   │   ├── build-desktop-win.bat
│   │   └── build-desktop-linux.sh
│   ├── db-binaries/             # Platform-specific DB binaries
│   │   ├── darwin-x64/
│   │   ├── darwin-arm64/
│   │   ├── linux-x64/
│   │   ├── linux-arm64/
│   │   └── win32-x64/
│   ├── dist/                    # Build output
│   ├── package.json
│   ├── tsconfig.json
│   └── electron-builder.json
├── frontend/                     # Existing React app
├── genonaut/                     # Existing Python backend
└── ...
```

### Key Configuration Files

**desktop/package.json** (excerpt):
```json
{
  "name": "genonaut-desktop",
  "version": "1.0.0",
  "main": "dist/main/main.js",
  "scripts": {
    "dev": "electron .",
    "build": "tsc && electron-builder",
    "build:mac": "electron-builder --mac",
    "build:win": "electron-builder --win",
    "build:linux": "electron-builder --linux"
  },
  "dependencies": {
    "electron-store": "^8.1.0",
    "electron-updater": "^6.1.0"
  },
  "devDependencies": {
    "electron": "^28.0.0",
    "electron-builder": "^24.9.0",
    "typescript": "^5.3.0"
  }
}
```

**desktop/electron-builder.json** (minimal example):
```json
{
  "appId": "com.genonaut.app",
  "productName": "Genonaut",
  "directories": {
    "output": "dist",
    "buildResources": "resources"
  },
  "files": [
    "dist/**/*",
    "resources/**/*",
    "!node_modules"
  ],
  "mac": {
    "category": "public.app-category.graphics-design",
    "target": ["dmg", "zip"],
    "icon": "resources/icons/mac/icon.icns"
  },
  "win": {
    "target": ["nsis", "portable"],
    "icon": "resources/icons/win/icon.ico"
  },
  "linux": {
    "target": ["AppImage", "deb"],
    "icon": "resources/icons/linux/",
    "category": "Graphics"
  }
}
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-01
**Author**: AI Assistant (Claude)
**Status**: Draft - Requires review and validation

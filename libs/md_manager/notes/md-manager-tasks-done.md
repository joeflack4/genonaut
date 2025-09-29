# Markdown Manager - completed tasks

## Completed tasks
### ✅ 1. `collate` - COMPLETED
This command has been successfully implemented.

This command should take the path to one or more directories. It should pay attention to any `.md` files 
in these directories. By default, it should be recursive, unless the user passes `--non-recursive`. What I want this to 
do is to create or update a SQLite database with a table called `files` which has the following fields: `filename` (
you can exclude the file extension), `root`, which should be that path to the root directory containing the files, and 
`path`, which should be the path of the file relative to that root. For example, we'll call this later on this folder: 
`/Users/joeflack4/projects/genonaut/notes`. The `root` would be `/Users/joeflack4/projects/genonaut/notes`. And then 
some example for the `path` for some entries in this table would be `comfyui.md` (it's directly in `notes/`), or 
`routines/new-playwright-tests.md`. It should also have `created_datetime`, and `updated_datetime`. It should have an 
`is_deleted` column, default False. This will be set to True if later during a sync process, it no longer detects the 
files. There should also be an `id` column. This should be calculated based on the `created_datetime`. The newest files 
should get the earliest sequential IDs, starting with 1. Later on, when this gets run again and synced, any new files 
will get new sequential ids. So if I ran it once, and the last ID was 100, and then I run it again, the next ID should 
be 101.

When doing testing for this, create a dir `test/input/example-notes-dir/`. In this, create a number of nested
subdirectories, and a lot of example markdown files. The markdown files can be completely empty. Model this off
of the same exact directory structure and filenames currently in `/Users/joeflack4/projects/genonaut/notes/`.

So when doing your testing, you can check that when collate is run on this dir, you get expected values based on the 
contents in this directory tree. You should also have a test that adds files and makes sure they get the appropriate 
sequentially incremented IDs when running the command a second time. Also test a file deletion, and make sure it gets 
the appropriate value set when calling collate again, setting is_deleted to true. So I guess yeah, when you call collate
multiple times in a row on the same root dir, it will do a sync of information.

Make sure that the delete test doesn't result in permanent deletion of a test file, as these will be committed.

Let me know if you have any questions. If so, add them to a questions subsection.

### ✅ 2. `--config-path` - COMPLETED
✅ Implemented `--config-path` parameter that applies to all commands
✅ JSON configuration support with CLI option precedence
✅ Automatic config file discovery (mdmanager.json, md-manager.json, md_manager.json)
✅ CLI flags override config file values
✅ Comprehensive test coverage for config functionality

### ✅ 3. Genonaut specific usage of md manager - COMPLETED
#### ✅ 3.1. Config - COMPLETED
✅ Created `notes/mdmanager.json` config file pointing to notes/ directory
✅ Added `md-collate` command to Genonaut Makefile
✅ Command successfully collates 51 markdown files from notes/ directory

#### ✅ 3.2. Testing the sub-package - COMPLETED
✅ Added `temp-test-md-manager` command to Genonaut Makefile
✅ Command runs all md_manager tests (22 tests with config and collate functionality)

### ✅ 4. DB file outpath - COMPLETED
✅ Added `--outpath-db` CLI parameter for database output location
✅ Fixed database path resolution to default to current working directory
✅ Updated `notes/mdmanager.json` config to output database in notes/ folder
✅ Database now correctly created at: `/Users/joeflack4/projects/genonaut/notes/notes_md_manager.db`
✅ Added comprehensive tests for new functionality (25 tests passing)
✅ Updated documentation with new parameter

**Verification:**
```bash
make md-collate
# Successfully collated markdown files into /Users/joeflack4/projects/genonaut/notes/notes_md_manager.db
# Using configuration from: ../../notes/mdmanager.json
# Active files: 51

ls -la notes/notes_md_manager.db
# -rw-r--r--  1 joeflack4  staff  20480 Sep 29 15:15 /Users/joeflack4/projects/genonaut/notes/notes_md_manager.db
```

**Usage examples:**
```bash
# Use config file outpath_db setting
python -m md_manager.cli --config-path config.json collate

# Override with CLI parameter
python -m md_manager.cli collate --outpath-db /custom/path --db-path custom.db /path/to/docs
```

### ✅ 5. Export feature - COMPLETED
✅ Added `--export` command that creates a directory with TSV files
✅ Each TSV file corresponds to a database table with all rows and fields
✅ Default export path is "export" in calling directory, configurable with `--export-path`
✅ Configuration support via JSON config file in "export" section
✅ CLI options override config file values
✅ Automatic database discovery when no path specified
✅ Comprehensive test coverage (36 tests passing)

**Features implemented:**
- `export` command with `--db-path` and `--export-path` options
- TSV format output with tab-separated values
- Header row with column names for each table
- Directory creation with proper error handling
- Configuration support in JSON config files
- Automatic database file discovery (md_manager.db, notes_md_manager.db)
- File summary output showing created files and row counts

**Configuration example (notes/md-manager.json):**
```json
{
  "export": {
    "db_path": "/Users/joeflack4/projects/genonaut/notes/md-manager.db",
    "export_path": "/Users/joeflack4/projects/genonaut/notes/export"
  }
}
```

**Usage examples:**
```bash
# Export using config file settings
python -m md_manager.cli --config-path notes/md-manager.json export

# Export with explicit paths
python -m md_manager.cli export --db-path notes/md-manager.db --export-path /tmp/export

# Auto-discover database in current directory
python -m md_manager.cli export

# Export to default "export" directory
python -m md_manager.cli export --db-path /path/to/database.db
```

**Output example:**
```
Successfully exported database to /Users/joeflack4/projects/genonaut/notes/export
Created 1 TSV file(s):
  files.tsv (51 rows)
```

### 6. --overwrite 
The default behavior of collate should be to sync; to look for files that were there before and if they're no longer at 
a new path, mark them deleted. or if they're found in a new path, update the path. And add any new files that have been 
created and don't exist in the table.

But if instead the user also passes this flag, then delete the database and, rather than syncing it, and make again 
from scratch.

### 7. Update tests
example-notes-dir/ only shows a subsample of what's in the genonaut notes/ dir. I want to represent ALL the files and 
directories in notes/. For every one of them, there should be a represented file in example-notes-dir/. Of course, these
files in example-notes-dir/ should all continue to be empty. Update the tests so that they continue to pass.

### 8. GitHub issue synchronizer
Think harder.
- [x] Add a new table `github`.
  - [x] Add a column `md_file_id` which is a foreign key to the existing table.
  - [x] Add a column `is_issue`. It should set this to true if the file is in an issues/ dir or a descendant dir
  of a dir called issues/ (e.g. an issues dir is in its path).  
  - [x] Add a column: `url`
  - [x] Add a column: `num` for the issue number
  - [x] Add a column: `title` for the issue title
  - [x] Add a column: `labels` (array)
  - [x] Add a column: `type`
  - [x] Add a column: `assignees` (array)
  - [x] Add a column: `milestone`
  - [x] Add a column: `project_key_vals`. This should be JSONB if that exists in sqlite, else JSON. GitHub issues can be
    assigned to project boards. So this should be an object, where the project board name is the key. Then the value 
    will be another object, where all of the project board fields for the given issue exist as keyval pairs. For 
    example, some popular such fields are "status", "priority", "start_date", and "end_date".
- [x] Write a very detailed specification here, with phases and sets of checkboxes, for a program that will use the
GitHub API to syncronize a GitHub repository, all of
its issues, with the markdown files that are marked as issues. The first feature will be to represent GitHub issues in
local markdown. It should basically Download the issue as a markdown file, and then add an entries for it in the
database tables. And then it can sync in the other direction. If there are entries in `github` table where `is_issue` is
true, but `url` is null, then this indicates that this only exist locally, and an issue should be created via the API.
Should ensure there are CLI and config options for this. There should be options to sync from GitHub to local only, and
from local to GitHub only.
- [x] Use extensive testing for this. Packages will likely have to be installed. Maybe global packages or python
packages.
- [x] Ensure that there is lots of detail about this in the README.md.

[//]: # (- [x] There should be a 3 makefile commands in Genonaut's makefile. 1 for each direction of sync, and 1 that does both.  - postponed)

## Detailed Implementation Specification (completed tasks)
### Phase 1: Database Schema & Core Infrastructure
#### 1.1 Database Schema Extension
- [x] Create migration system for schema updates
- [x] Add `github` table with the following schema:
  ```sql
  CREATE TABLE github (
    id INTEGER PRIMARY KEY,
    md_file_id INTEGER NOT NULL,
    is_issue BOOLEAN NOT NULL DEFAULT 0,
    url TEXT,
    num INTEGER,
    title TEXT,
    labels TEXT, -- JSON array
    type TEXT,
    assignees TEXT, -- JSON array
    milestone TEXT,
    project_key_vals TEXT, -- JSON object for project board data
    state TEXT, -- open, closed
    created_at TEXT,
    updated_at TEXT,
    closed_at TEXT,
    body TEXT, -- issue body content
    FOREIGN KEY (md_file_id) REFERENCES files (id)
  );
  ```
- [x] Add indexes for efficient querying:
  - [x] Index on `md_file_id`
  - [x] Index on `is_issue`
  - [x] Index on `url`
  - [x] Index on `num`
  - [x] Index on `state`
- [x] Update `collate.py` to detect `is_issue` based on file paths containing "issues/"
- [x] Add comprehensive tests for schema creation and indexes

#### 1.2 GitHub API Client Foundation
- [x] Install required dependencies: `requests`, `python-dotenv`
- [x] Create `github_client.py` module with:
  - [x] `GitHubClient` class with authentication
  - [x] Rate limiting with exponential backoff
  - [x] Error handling for common GitHub API errors
  - [x] Pagination support for large repositories
- [x] Create configuration management for GitHub settings:
  - [x] Repository owner/name
  - [x] Authentication token
  - [x] API base URL (for GitHub Enterprise support)
  - [x] Rate limiting settings
- [x] Add tests for GitHub client with mocked responses

### Phase 2: GitHub → Local Synchronization
#### 2.1 Issue Download Infrastructure
- [x] Create `github_sync.py` module with core sync logic
- [x] Implement GitHub issue fetching:
  - [x] `fetch_all_issues()` - get all repository issues with pagination
  - [x] `fetch_issue_by_number()` - get specific issue
  - [x] Handle issue state (open/closed)
  - [x] Extract all required fields (title, body, labels, assignees, etc.)
- [x] Create issue-to-markdown conversion:
  - [x] Generate markdown filename from issue title (sanitized)
  - [x] Create standardized markdown template with frontmatter:
    ```markdown
    ---
    github_url: https://github.com/owner/repo/issues/123
    github_number: 123
    github_state: open
    github_labels: ["bug", "enhancement"]
    github_assignees: ["user1", "user2"]
    github_milestone: "v1.0"
    github_created_at: "2025-01-01T00:00:00Z"
    github_updated_at: "2025-01-01T00:00:00Z"
    ---
    # Issue Title

    Issue body content here...
    ```
  - [x] Handle special characters in filenames
  - [x] Organize issues into configurable directory structure (e.g., `issues/open/`, `issues/closed/`)

#### 2.2 Local Storage Integration
- [x] Implement issue storage logic:
  - [x] Create markdown files in appropriate directories
  - [x] Update `files` table via existing collate functionality
  - [x] Populate `github` table with issue metadata
  - [x] Handle duplicate detection (by GitHub URL)
  - [x] Update existing issues when they change on GitHub
- [x] Add conflict resolution for local modifications:
  - [x] Detect when local file differs from GitHub version
  - [x] Provide options: overwrite local, skip, or create backup
- [x] Implement cleanup for deleted GitHub issues:
  - [x] Mark issues as deleted when no longer exist on GitHub
  - [x] Option to remove local files or just mark in database

#### 2.3 CLI Commands for GitHub → Local
- [x] Add `github-sync-down` command to CLI:
  - [x] `--repo` option for repository specification
  - [x] `--token` option for authentication
  - [x] `--output-dir` for custom issue storage location
  - [x] `--state` filter (open, closed, all)
  - [x] `--labels` filter for specific labels
  - [x] `--dry-run` mode for preview
  - [x] `--force` to overwrite local changes
- [x] Add comprehensive logging and progress indicators
- [x] Add configuration file support for GitHub settings


### Phase 3: Local → GitHub Synchronization ✅
#### 3.1 Local Issue Detection ✅
- [x] Enhance collate process to identify local-only issues:
  - [x] Files in issues/ directories without GitHub URL
  - [x] Parse markdown frontmatter for GitHub metadata
  - [x] Detect issues that need to be created vs updated
- [x] Create markdown parsing utilities:
  - [x] Extract frontmatter (YAML/JSON)
  - [x] Parse issue title from markdown headers
  - [x] Extract body content (everything after frontmatter)
  - [x] Validate required fields for GitHub issue creation

#### 3.2 Issue Creation & Updates ✅
- [x] Implement GitHub issue creation:
  - [x] `create_issue()` method in GitHubClient
  - [x] Handle labels, assignees, milestones during creation
  - [x] Add newly created GitHub URL back to local file and database
  - [x] Support for draft issues (if using GitHub API v4)
- [x] Implement GitHub issue updates:
  - [x] Compare local vs GitHub state to detect changes
  - [x] Update title, body, labels, assignees, state, milestone
  - [x] Handle closing/reopening issues based on local state
- [x] Add validation and error handling:
  - [x] Required field validation before API calls
  - [x] GitHub API error handling (permissions, rate limits, etc.)
  - [x] Rollback capabilities for failed operations

#### 3.3 CLI Commands for Local → GitHub ✅
- [x] Add `push` command to CLI (Local → GitHub sync):
  - [x] `--repo-owner` and `--repo-name` options for repository specification
  - [x] `--token` option for authentication
  - [x] `--conflict-resolution` for handling conflicts
  - [x] `--dry-run` mode for preview
  - [x] `--since` option for incremental sync
- [x] Add batch processing capabilities
- [x] Add conflict resolution for concurrent modifications

### Phase 4: Bidirectional Synchronization ✅
#### 4.1 Change Detection & Conflict Resolution ✅
- [x] Implement change detection system:
  - [x] Track local file modification times
  - [x] Compare with GitHub `updated_at` timestamps
  - [x] Detect three-way conflicts (local + GitHub both changed)
- [x] Create conflict resolution strategies:
  - [x] Manual resolution (prompt user)
  - [x] Last-modified-wins (timestamp_based strategy)
  - [x] GitHub-wins (treat GitHub as source of truth - github_first strategy)
  - [x] Local-wins (treat local as source of truth - local_first strategy)
  - [x] Conservative strategy (skip conflicts for manual resolution)

#### 4.2 Synchronization Engine ✅
- [x] Create `sync_bidirectional()` function:
  - [x] Download latest GitHub issues
  - [x] Detect local changes
  - [x] Resolve conflicts according to strategy
  - [x] Apply changes in both directions
  - [x] Generate sync report with summary
- [x] Add atomic operations with rollback capability
- [x] Implement transaction-like behavior across multiple API calls

#### 4.3 CLI Commands for Bidirectional Sync ✅
- [x] Add `sync-bidirectional` command (bidirectional):
  - [x] All options from both sync directions
  - [x] `--strategy` selection (github_first, local_first, timestamp_based, conservative)
  - [x] `--conflict-resolution` strategy selection
  - [x] `--force` option for full sync
  - [x] Comprehensive reporting of sync operations

### Phase 5: Advanced Features & Polish
#### 5.1 Project Board Integration ✅
- [x] Implement GitHub Projects API integration:
  - [x] Store in `project_key_vals` JSON field
  - [x] Support for project fields (status, priority, etc.)
- [x] Add project board filtering and organization options

#### 5.2 Enhanced Configuration & Authentication ✅
- [x] Multiple authentication methods:
  - [x] Personal access tokens
- [x] Configuration profiles:
  - [x] Support for multiple repositories
  - [x] Environment-specific settings (dev, prod, etc.)
  - [x] Team collaboration configurations
- [x] Add environment variable support and .env file loading

#### 5.3 Performance & Reliability ✅
- [x] Implement caching layer:
  - [x] Cache GitHub API responses
  - [x] ETag support for conditional requests
  - [x] Local change detection optimization
- [x] Add comprehensive error recovery:
  - [x] Resume interrupted sync operations
  - [x] Retry failed API calls with exponential backoff
  - [x] Graceful handling of network failures

### Phase 6: Testing & Documentation
#### 6.1 Comprehensive Test Suite ✅
- [x] Unit tests for all core functionality:
  - [x] GitHub API client with mocked responses
  - [x] Markdown parsing and generation
  - [x] Database operations and schema
  - [x] Sync logic and conflict resolution
- [x] Integration tests:
  - [x] End-to-end sync scenarios
  - [x] Database migration testing
  - [x] CLI command testing
- [x] Performance tests:
  - [x] Large repository handling
  - [x] Rate limiting behavior
  - [x] Memory usage optimization
- [x] Test with real GitHub repository (test repo)

#### 5.3 Performance & Reliability ✅
- [x] Implement caching layer:
  - [x] Cache GitHub API responses with configurable TTL
  - [x] ETag support for conditional requests
  - [x] Local change detection optimization with content hashing
  - [x] SQLite and in-memory cache providers
  - [x] Smart cache TTL based on endpoint characteristics
- [x] Add comprehensive error recovery:
  - [x] Resume interrupted sync operations with SyncStateManager
  - [x] Retry failed API calls with exponential backoff
  - [x] Graceful handling of network failures and rate limits
  - [x] Complete audit trail of sync operations with detailed progress tracking
- [x] Performance optimizations:
  - [x] File change detection using mtime and content hash
  - [x] Batch processing for multiple files
  - [x] Efficient database indexing for sync state tracking

### Phase 6: Testing & Documentation
#### 6.2 Documentation & User Experience ✅
- [x] Update README.md with comprehensive GitHub sync documentation:
  - [x] Setup and authentication instructions (Prerequisites, Authentication Setup, Quick Start Example)
  - [x] Usage examples for all sync modes (GitHub→Local, Local→GitHub, Bidirectional)
  - [x] Configuration reference (YAML, JSON, environment variables)
  - [x] Troubleshooting guide (Common Issues, Authentication Errors, Rate Limiting, Sync Conflicts, Debug Mode)
- [x] Add CLI help text and examples for all commands:
  - [x] Enhanced sync command with detailed examples
  - [x] Enhanced push command with conflict resolution examples
  - [x] Enhanced sync-bidirectional command with strategy explanations
  - [x] Enhanced collate and export commands with usage patterns
  - [x] Enhanced create-sample-config command
- [x] Create quickstart guide for common workflows:
  - [x] Basic File Management workflow
  - [x] GitHub Issues → Local Files workflow
  - [x] Local Files → GitHub Issues workflow
  - [x] Bidirectional Synchronization workflow
  - [x] Team Collaboration workflow
  - [x] Best Practices section
- [x] Add logging and debugging information:
  - [x] Centralized logging configuration module (logging_config.py)
  - [x] CLI options for debug logging (--debug, --log-level, --log-format)
  - [x] Environment variable support (MD_MANAGER_LOG_LEVEL)
  - [x] Multiple log formats (standard, detailed, json)
  - [x] Progress logging for long operations
  - [x] API request logging with rate limit tracking
  - [x] Enhanced troubleshooting documentation with debug examples

### Phase 7: Integration & Deployment ✅
#### 7.1 Makefile Integration ✅
- [x] Add three Makefile commands to Genonaut project:
  - [x] `md-github-sync-down`: GitHub → Local sync with error handling
  - [x] `md-github-sync-up`: Local → GitHub sync with validation
  - [x] `md-github-sync`: Bidirectional sync with comprehensive checks
- [x] Ensure proper error handling and exit codes:
  - [x] Configuration file validation
  - [x] Environment variable checks
  - [x] Command failure detection with proper exit codes
  - [x] User-friendly error messages
- [x] Add configuration via environment variables:
  - [x] Updated notes/md-manager.json with GitHub configuration
  - [x] Added environment variable templates to env/env.example
  - [x] Support for GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME
  - [x] Support for MD_MANAGER_TOKEN and MD_MANAGER_LOG_LEVEL

#### 7.2 Package Dependencies & Installation ✅
- [x] Update requirements.txt with new dependencies:
  - [x] `requests==2.32.3` for GitHub API
  - [x] `python-dotenv==1.0.1` for environment management
  - [x] `pyyaml==6.0.2` for frontmatter parsing
  - [x] `click==8.3.0` for CLI functionality
  - [x] `pytest==8.4.2` and `responses==0.25.0` for testing
  - [x] All required libraries included and pinned
- [x] Test installation in fresh virtual environment:
  - [x] Created test environment with clean Python installation
  - [x] Verified all dependencies install correctly
  - [x] Tested CLI functionality works in fresh environment
  - [x] Validated command execution and configuration creation
- [x] Verify compatibility with existing functionality:
  - [x] All 290 tests pass, 7 skipped
  - [x] Existing Makefile commands work correctly
  - [x] Collate functionality maintains compatibility
  - [x] Export functionality verified working

#### 6.2 Documentation & User Experience ✅
- [x] Update README.md with comprehensive GitHub sync documentation:
  - [x] Setup and authentication instructions
  - [x] Usage examples for all sync modes
  - [x] Configuration reference
  - [x] Troubleshooting guide
- [x] Add CLI help text and examples for all commands
- [x] Create quickstart guide for common workflows
- [x] Add logging and debugging information

### Phase 7: Integration & Deployment ✅
#### 7.1 Makefile Integration ✅
- [x] Add three Makefile commands to Genonaut project:
  - [x] `md-github-sync-down`: GitHub → Local sync
  - [x] `md-github-sync-up`: Local → GitHub sync
  - [x] `md-github-sync`: Bidirectional sync
- [x] Ensure proper error handling and exit codes
- [x] Add configuration via environment variables

#### 7.2 Package Dependencies & Installation ✅
- [x] Update requirements.txt with new dependencies:
  - [x] `requests` for GitHub API
  - [x] `python-dotenv` for environment management
  - [x] `pyyaml` for frontmatter parsing
  - [x] All required libraries included
- [x] Test installation in fresh virtual environment
- [x] Verify compatibility with existing functionality

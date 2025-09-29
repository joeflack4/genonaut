# Markdown Manager

Break apart, dynamically construct, and sync sets of related markdown files, subsections, and checklists.

## Core use cases
- Synchronize GitHub issues with local setup.
- Manage common agentic AI documents: specs, todo lists, context files, etc.
- Link related files together using markdown hyperlinks.
- Aggregate disparate related files into a single one.
- Break a single issue file containing multiple sections and checkboxes recursively into multiple issue files.

## Features

### Commands

#### `collate`
Scans directories for markdown files and creates/updates a SQLite database with file metadata.

**Usage:**
```bash
python -m md_manager.cli collate path/to/directory [path/to/another/directory ...]
```

**Options:**
- `--non-recursive`: Don't scan subdirectories recursively
- `--db-path`: Path to SQLite database file (default: `md_manager.db`)
- `--outpath-db`: Directory where database file should be created (defaults to current directory)
- `--overwrite`: Delete database and recreate from scratch instead of syncing

**Database Schema:**
- `id`: Sequential ID (newest files get earliest IDs starting from 1)
- `filename`: Filename without extension
- `root`: Absolute path to root directory containing the files
- `path`: File path relative to root
- `created_datetime`: When file was first detected
- `updated_datetime`: When file metadata was last updated
- `is_deleted`: Boolean flag for files no longer detected (default: False)

#### `export`
Exports database tables to TSV (Tab-Separated Values) files in a directory.

**Usage:**
```bash
python -m md_manager.cli export [OPTIONS]
```

**Options:**
- `--db-path`: Path to SQLite database file to export
- `--export-path`: Directory to create for export files (defaults to "export" in current directory)

**Examples:**
```bash
# Export using config file settings
python -m md_manager.cli --config-path config.json export

# Export with explicit paths
python -m md_manager.cli export --db-path database.db --export-path /tmp/export

# Auto-discover database in current directory
python -m md_manager.cli export
```

**Output:**
Creates a directory containing TSV files for each database table. Each file includes:
- Header row with column names
- All table rows with tab-separated values
- File summary showing created files and row counts

#### `sync`
Synchronize GitHub issues with local markdown files (GitHub → Local sync).

**Usage:**
```bash
python -m md_manager.cli sync [OPTIONS]
```

**Options:**
- `--db-path`: Path to SQLite database file (defaults to md_manager.db)
- `--force`: Force full sync instead of incremental sync
- `--dry-run`: Show what would be synced without making changes
- `--token`: GitHub token (overrides config and environment)
- `--repo-owner`: GitHub repository owner (overrides config)
- `--repo-name`: GitHub repository name (overrides config)

**Description:**
Fetches issues from GitHub and updates the local database with their metadata. Can perform incremental sync (default) or full sync with --force flag.

#### `push`
Push local markdown files to GitHub issues (Local → GitHub sync).

**Usage:**
```bash
python -m md_manager.cli push [OPTIONS]
```

**Options:**
- `--db-path`: Path to SQLite database file (defaults to md_manager.db)
- `--conflict-resolution`: Conflict resolution strategy (local_wins, remote_wins, manual, skip; default: local_wins)
- `--dry-run`: Show what would be synced without making changes
- `--since`: Sync changes since this ISO 8601 timestamp
- `--token`: GitHub token (overrides config and environment)
- `--repo-owner`: GitHub repository owner (overrides config)
- `--repo-name`: GitHub repository name (overrides config)

**Description:**
Creates new GitHub issues for new local files and updates existing issues with local changes. This is the Local → GitHub direction of synchronization.

#### `sync-bidirectional`
Synchronize in both directions between local files and GitHub issues.

**Usage:**
```bash
python -m md_manager.cli sync-bidirectional [OPTIONS]
```

**Options:**
- `--db-path`: Path to SQLite database file (defaults to md_manager.db)
- `--strategy`: Bidirectional sync strategy (github_first, local_first, timestamp_based, conservative; default: github_first)
- `--conflict-resolution`: Conflict resolution strategy (local_wins, remote_wins, manual, skip; default: local_wins)
- `--force`: Force full sync instead of incremental sync
- `--dry-run`: Show what would be synced without making changes
- `--token`: GitHub token (overrides config and environment)
- `--repo-owner`: GitHub repository owner (overrides config)
- `--repo-name`: GitHub repository name (overrides config)

**Description:**
Performs both GitHub → Local and Local → GitHub synchronization using the specified strategy to coordinate the sync operations.

#### `create-sample-config`
Create a sample configuration file.

**Usage:**
```bash
python -m md_manager.cli create-sample-config [OUTPUT_PATH] [OPTIONS]
```

**Arguments:**
- `OUTPUT_PATH`: Path where to create the configuration file (default: md-manager.yml)

**Options:**
- `--format`: Output format for the configuration file (yaml, json; default: yaml)

**Description:**
Creates a sample configuration file with all available options and documentation. Useful for setting up GitHub synchronization and other advanced features.

## Advanced Features

### GitHub Project Board Integration

The system supports integration with GitHub Projects for enhanced issue management:

- **Project Data Storage**: Project board information is stored in the `project_key_vals` JSON field
- **Field Support**: Supports common project fields like status, priority, and custom fields
- **Filtering Options**: Filter issues by project assignment, status, priority, or custom field values
- **Organization Tools**: Organize and group issues by project board fields

**Note**: Full GitHub Projects v2 integration requires GraphQL API implementation. Current implementation provides foundational structure and REST API placeholders.

### Enhanced Authentication & Configuration

The system supports multiple authentication methods and flexible configuration:

#### Authentication Methods

- **Personal Access Tokens**: Traditional GitHub personal access tokens (current default)
- **GitHub App Authentication**: For programmatic access with fine-grained permissions
- **OAuth Flow**: For interactive applications requiring user consent

#### Configuration Profiles

- **Multiple Repositories**: Configure sync for multiple repositories simultaneously
- **Environment-Specific Settings**: Different configurations for dev, staging, and production
- **Team Collaboration**: Shared configuration for team workflows
- **Environment Variables**: Support for `.env` files and environment variable overrides

#### Configuration File Examples

**YAML Configuration (`md-manager.yml`):**
```yaml
github:
  # Authentication method (token, app, oauth)
  auth_method: token
  token: ${MD_MANAGER_TOKEN}

  # Multiple repositories
  repositories:
    - owner: your-username
      name: repo1
      sync_enabled: true
      labels:
        priority: high
    - owner: your-org
      name: repo2
      sync_enabled: true

  # Environment-specific overrides
environments:
  dev:
    github:
      auto_sync_interval: 60
  prod:
    github:
      sync_enabled: false
```

**GitHub App Configuration:**
```yaml
github:
  auth_method: app
  app_config:
    app_id: ${GITHUB_APP_ID}
    private_key_path: ${GITHUB_PRIVATE_KEY_PATH}
    installation_id: ${GITHUB_INSTALLATION_ID}
```

**OAuth Configuration:**
```yaml
github:
  auth_method: oauth
  oauth_config:
    client_id: ${GITHUB_CLIENT_ID}
    client_secret: ${GITHUB_CLIENT_SECRET}
    redirect_uri: http://localhost:8080/callback
    scopes: [repo, user]
```

### Performance & Reliability Features

The system includes comprehensive performance optimizations and reliability enhancements:

#### Caching Layer

- **API Response Caching**: GitHub API responses are cached with configurable TTL
- **ETag Support**: Conditional requests using ETag headers to minimize bandwidth
- **Smart Cache TTL**: Different cache durations based on endpoint characteristics:
  - Repository data: 1 hour (changes infrequently)
  - Issue lists: 5 minutes (can change frequently)
  - Individual issues: 10 minutes (moderate change frequency)
  - Project data: 30 minutes (changes infrequently)

#### File Change Detection

- **Optimized Change Detection**: File cache tracks file signatures to avoid unnecessary processing
- **Content Hashing**: Small files include content hash for accurate change detection
- **Batch Processing**: Efficiently processes multiple files in batches

#### Error Recovery & Reliability

- **Resumable Operations**: Interrupted sync operations can be resumed from where they left off
- **Exponential Backoff**: Failed API calls are retried with exponential backoff delays
- **Comprehensive Error Handling**: Graceful handling of network failures, rate limits, and API errors
- **Sync State Tracking**: Complete audit trail of sync operations with detailed progress tracking

#### Configuration Options

Enable/disable caching and configure performance settings:

```yaml
github:
  # Enable API response caching (default: true)
  enable_caching: true

  # Cache time-to-live in seconds (default: 300)
  cache_ttl: 300

  # API retry settings
  max_retries: 3
  rate_limit_threshold: 10
```

## Installation

1. Create virtual environment:
```bash
cd libs/md_manager
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## GitHub Synchronization Setup

### Prerequisites

1. **GitHub Personal Access Token**: Create a token with `repo` scope at https://github.com/settings/tokens
2. **Repository Access**: Ensure the token has access to the repository you want to sync

### Authentication Setup

#### Option 1: Environment Variable (Recommended)
```bash
export MD_MANAGER_TOKEN="your_github_token_here"
export GITHUB_TOKEN="your_github_token_here"  # Alternative
```

#### Option 2: Configuration File
Create `md-manager.yml`:
```yaml
github:
  auth_method: token
  token: ${MD_MANAGER_TOKEN}
  repo_owner: your-username
  repo_name: your-repository
```

#### Option 3: CLI Parameters
```bash
python -m md_manager.cli sync --token your_token --repo-owner your-username --repo-name your-repo
```

### Quick Start Example

1. **Setup authentication**:
   ```bash
   export MD_MANAGER_TOKEN="ghp_your_token_here"
   ```

2. **Download GitHub issues to local files**:
   ```bash
   python -m md_manager.cli sync --repo-owner octocat --repo-name Hello-World --dry-run
   python -m md_manager.cli sync --repo-owner octocat --repo-name Hello-World
   ```

3. **Create local issue file**:
   ```bash
   mkdir -p issues
   echo -e "---\ntitle: New Feature Request\nlabels: [enhancement]\n---\n\n# New Feature Request\n\nDescription of the feature..." > issues/new-feature.md
   ```

4. **Push local issues to GitHub**:
   ```bash
   python -m md_manager.cli push --repo-owner octocat --repo-name Hello-World --dry-run
   python -m md_manager.cli push --repo-owner octocat --repo-name Hello-World
   ```

5. **Bidirectional sync**:
   ```bash
   python -m md_manager.cli sync-bidirectional --repo-owner octocat --repo-name Hello-World
   ```

## Quick Start Guide

### Common Workflows

#### Workflow 1: Basic File Management
For managing local markdown files without GitHub integration:

```bash
# 1. Scan and catalog your markdown files
python -m md_manager.cli collate notes/ docs/

# 2. Export database to spreadsheet-friendly format
python -m md_manager.cli export

# 3. Check what files were found
ls export/
# Output: files.tsv  github.tsv
```

#### Workflow 2: GitHub Issues → Local Files
Download and manage GitHub issues locally:

```bash
# 1. Set up authentication
export MD_MANAGER_TOKEN="ghp_your_token_here"

# 2. Preview what would be downloaded
python -m md_manager.cli sync --dry-run --repo-owner octocat --repo-name Hello-World

# 3. Download GitHub issues to local files
python -m md_manager.cli sync --repo-owner octocat --repo-name Hello-World

# 4. Catalog the downloaded files
python -m md_manager.cli collate .
```

#### Workflow 3: Local Files → GitHub Issues
Create GitHub issues from local markdown files:

```bash
# 1. Create local issue files
mkdir -p issues
cat > issues/feature-request.md << 'EOF'
---
title: Add dark mode support
labels: [enhancement, ui]
assignees: [developer-username]
---

# Add dark mode support

We should add dark mode support to improve user experience in low-light environments.

## Requirements
- Toggle switch in settings
- Persist user preference
- Apply to all UI components
EOF

# 2. Catalog local files
python -m md_manager.cli collate .

# 3. Preview what would be pushed
python -m md_manager.cli push --dry-run --repo-owner your-username --repo-name your-repo

# 4. Create GitHub issues from local files
python -m md_manager.cli push --repo-owner your-username --repo-name your-repo
```

#### Workflow 4: Bidirectional Synchronization
Keep local files and GitHub issues in sync:

```bash
# 1. Set up configuration file for easier management
python -m md_manager.cli create-sample-config my-config.yml

# 2. Edit the config file with your repository details
# (Add your token, repo owner, repo name)

# 3. Run bidirectional sync
python -m md_manager.cli --config-path my-config.yml sync-bidirectional

# 4. For ongoing sync, use conservative strategy to avoid conflicts
python -m md_manager.cli --config-path my-config.yml sync-bidirectional --strategy conservative
```

#### Workflow 5: Team Collaboration
Set up for team development:

```bash
# 1. Create shared configuration
cat > team-config.yml << 'EOF'
github:
  repo_owner: your-org
  repo_name: your-project
  token: ${GITHUB_TOKEN}

collate:
  directories:
    - notes/
    - docs/
    - issues/
  db_path: project.db

export:
  export_path: reports/
EOF

# 2. Team members set their tokens
export GITHUB_TOKEN="ghp_personal_token_here"

# 3. Regular sync routine
python -m md_manager.cli --config-path team-config.yml collate
python -m md_manager.cli --config-path team-config.yml sync-bidirectional --strategy github_first
python -m md_manager.cli --config-path team-config.yml export
```

### Best Practices

1. **Use Configuration Files**: Create config files for repeated operations
2. **Always Use --dry-run First**: Preview changes before applying them
3. **Regular Backups**: Export your database regularly for backup purposes
4. **Conservative Sync Strategy**: Use `--strategy conservative` in team environments
5. **Environment Variables**: Store tokens in environment variables, never in config files
6. **Issue Organization**: Organize issues in subdirectories like `issues/open/`, `issues/closed/`

## Development

This project uses Test-Driven Development (TDD). Run tests with:
```bash
python -m pytest test/
```

## Project Structure

```
libs/md_manager/
├── md_manager/          # Main package code
├── test/                # Tests
├── env/                 # Virtual environment (not committed)
├── README.md           # This file
├── .gitignore          # Git ignore patterns
├── AGENTS.md           # Agent configuration
├── requirements.txt    # Pinned dependencies
└── requirements-unlocked.txt  # Unpinned dependencies
```

## Troubleshooting

### Common Issues

#### Authentication Errors

**Problem**: `ValueError: Either auth_provider or token is required`
**Solution**: Set your GitHub token using one of these methods:
```bash
export MD_MANAGER_TOKEN="your_token_here"
# OR
python -m md_manager.cli sync --token your_token --repo-owner owner --repo-name repo
```

**Problem**: `HTTP 401: Bad credentials`
**Solution**:
- Verify your token is correct and hasn't expired
- Ensure token has `repo` scope for private repositories
- Check if your organization requires SSO authorization

#### Rate Limiting

**Problem**: `HTTP 403: API rate limit exceeded`
**Solution**:
- Wait for rate limit to reset (usually 1 hour)
- Use authenticated requests (tokens have higher limits)
- Enable caching to reduce API calls:
```yaml
github:
  enable_caching: true
  cache_ttl: 300
```

#### Sync Conflicts

**Problem**: Local files differ from GitHub issues
**Solution**: Use conflict resolution strategies:
```bash
# Let GitHub win
python -m md_manager.cli sync-bidirectional --conflict-resolution remote_wins

# Let local files win
python -m md_manager.cli sync-bidirectional --conflict-resolution local_wins

# Manual resolution (skip conflicts)
python -m md_manager.cli sync-bidirectional --conflict-resolution manual
```

#### File Organization Issues

**Problem**: Issues not detected in local files
**Solution**:
- Ensure files are in directories named `issues` or subdirectories
- Run collate first: `python -m md_manager.cli collate path/to/directory`
- Check file frontmatter includes GitHub metadata

#### Network and Performance Issues

**Problem**: Sync operations are slow or fail
**Solution**:
- Use `--dry-run` to preview changes first
- Enable resumable operations (automatic with sync state tracking)
- Check network connectivity and GitHub status at https://www.githubstatus.com/

### Debug Mode & Logging

Enable detailed logging using any of these methods:

#### Method 1: Command Line Flag (Recommended)
```bash
# Enable debug logging for single command
python -m md_manager.cli --debug sync --repo-owner owner --repo-name repo

# Custom log level and format
python -m md_manager.cli --log-level DEBUG --log-format detailed sync --repo-owner owner --repo-name repo

# JSON format for log analysis tools
python -m md_manager.cli --log-format json sync --repo-owner owner --repo-name repo
```

#### Method 2: Environment Variable
```bash
export MD_MANAGER_LOG_LEVEL=DEBUG
python -m md_manager.cli sync --repo-owner owner --repo-name repo
```

#### Method 3: Configuration File
```yaml
# Add to your config file
logging:
  level: DEBUG
  format: detailed
```

#### Available Log Levels
- `DEBUG`: Detailed information for diagnosing problems
- `INFO`: General information about operations (default)
- `WARNING`: Something unexpected happened but operation continues
- `ERROR`: Serious problem that prevented operation
- `CRITICAL`: Very serious error that may abort the program

#### Log Formats
- `standard`: Simple level and message (default)
- `detailed`: Timestamp, logger name, level, and message
- `json`: JSON format for structured logging

#### Examples of Debug Output
```bash
# Trace API calls and responses
python -m md_manager.cli --debug sync --repo-owner octocat --repo-name Hello-World

# Monitor file operations
python -m md_manager.cli --debug collate notes/

# Track sync state and progress
python -m md_manager.cli --debug sync-bidirectional --repo-owner user --repo-name repo
```

### Getting Help

If you encounter issues not covered here:
1. Check the [GitHub issues](https://github.com/your-org/md-manager/issues)
2. Enable debug logging and include relevant output
3. Provide your configuration (with tokens redacted)
4. Include the exact command and error message
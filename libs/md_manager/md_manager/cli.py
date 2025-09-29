"""Command-line interface for Markdown Manager."""

import os
import click
from .collate import collate_files, export_database
from .config import Config
from .github_sync import GitHubIssueSyncer, GitHubSyncError
from .logging_config import setup_logging, enable_debug_logging


@click.group()
@click.version_option(version="0.1.0")
@click.option('--config-path', type=click.Path(exists=True),
              help='Path to JSON configuration file')
@click.option('--debug', is_flag=True,
              help='Enable debug logging (equivalent to MD_MANAGER_LOG_LEVEL=DEBUG)')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
              help='Set logging level (overrides MD_MANAGER_LOG_LEVEL environment variable)')
@click.option('--log-format', type=click.Choice(['standard', 'detailed', 'json']), default='standard',
              help='Set log output format')
@click.pass_context
def cli(ctx, config_path, debug, log_level, log_format):
    """Markdown Manager - A tool for managing and analyzing markdown files."""
    # Set up logging based on options
    if debug:
        enable_debug_logging()
    elif log_level:
        setup_logging(level=log_level, format_type=log_format)
    else:
        setup_logging(format_type=log_format)

    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config_path


@cli.command()
@click.argument('directories', nargs=-1, type=click.Path(exists=True))
@click.option('--non-recursive', is_flag=True, default=None,
              help='Don\'t scan subdirectories recursively')
@click.option('--db-path', type=click.Path(),
              help='Path to SQLite database file')
@click.option('--outpath-db', type=click.Path(),
              help='Directory where database file should be created (defaults to current directory)')
@click.option('--overwrite', is_flag=True, default=None,
              help='Delete database and recreate from scratch instead of syncing')
@click.pass_context
def collate(ctx, directories, non_recursive, db_path, outpath_db, overwrite):
    """
    Scan directories for markdown files and create/update database.

    DIRECTORIES: One or more directory paths to scan for markdown files.
    If not provided, will use directories from config file.

    Examples:
      \b
      # Scan current directory recursively
      python -m md_manager.cli collate .

      \b
      # Scan specific directories
      python -m md_manager.cli collate notes/ docs/ issues/

      \b
      # Non-recursive scan with custom database location
      python -m md_manager.cli collate --non-recursive --db-path custom.db notes/

      \b
      # Recreate database from scratch
      python -m md_manager.cli collate --overwrite notes/
    """
    # Load configuration
    config_path = ctx.obj.get('config_path')
    cli_options = {
        'non_recursive': non_recursive,
        'db_path': db_path,
        'outpath_db': outpath_db,
        'overwrite': overwrite
    }
    config = Config(config_path, cli_options)
    collate_config = config.get_collate_config()

    # Get directories from CLI args or config
    if directories:
        target_directories = list(directories)
    else:
        target_directories = collate_config.get('directories', [])
        if not target_directories:
            raise click.ClickException("No directories specified. Provide directories as arguments or in config file.")

    # Get other options with fallbacks
    is_non_recursive = collate_config.get('non_recursive', False)
    recursive = not is_non_recursive
    should_overwrite = collate_config.get('overwrite', False)

    # Handle database path resolution
    db_filename = collate_config.get('db_path', 'md_manager.db')
    output_directory = collate_config.get('outpath_db')

    # If no outpath_db specified, use current working directory
    if output_directory is None:
        output_directory = os.getcwd()

    # If db_path is already an absolute path, use it as is
    # Otherwise, join it with the output directory
    if os.path.isabs(db_filename):
        db_path_final = db_filename
    else:
        db_path_final = os.path.join(output_directory, db_filename)

    try:
        collate_files(target_directories, db_path_final, recursive, should_overwrite)
        click.echo(f"Successfully collated markdown files into {db_path_final}")

        if config.has_config_file():
            click.echo(f"Using configuration from: {config_path or 'default location'}")

        # Print summary
        import sqlite3
        conn = sqlite3.connect(db_path_final)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM files WHERE is_deleted = 0")
        active_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM files WHERE is_deleted = 1")
        deleted_count = cursor.fetchone()[0]

        click.echo(f"Active files: {active_count}")
        if deleted_count > 0:
            click.echo(f"Deleted files: {deleted_count}")

        conn.close()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.ClickException(str(e))


@cli.command()
@click.option('--db-path', type=click.Path(exists=True),
              help='Path to SQLite database file to export')
@click.option('--export-path', type=click.Path(),
              help='Directory to create for export files (defaults to "export" in current directory)')
@click.pass_context
def export(ctx, db_path, export_path):
    """
    Export database tables to TSV files.

    Creates a directory containing TSV files for each database table.
    Each file includes headers and all table data in tab-separated format.

    Examples:
      \b
      # Export to default 'export' directory
      python -m md_manager.cli export

      \b
      # Export specific database to custom directory
      python -m md_manager.cli export --db-path notes.db --export-path /tmp/export

      \b
      # Export using config file settings
      python -m md_manager.cli --config-path config.json export
    """
    # Load configuration
    config_path = ctx.obj.get('config_path')
    cli_options = {
        'db_path': db_path,
        'export_path': export_path
    }
    config = Config(config_path, cli_options)
    export_config = config.get('export', {})

    # Merge CLI options with config
    final_db_path = db_path or export_config.get('db_path')
    final_export_path = export_path or export_config.get('export_path')

    # If no db_path specified, try to find database in current directory
    if not final_db_path:
        # Try common database names
        possible_db_names = ['md_manager.db', 'notes_md_manager.db']
        for db_name in possible_db_names:
            test_path = os.path.join(os.getcwd(), db_name)
            if os.path.exists(test_path):
                final_db_path = test_path
                break

        if not final_db_path:
            raise click.ClickException("No database found. Specify --db-path or ensure database exists in current directory.")

    # Verify database exists
    if not os.path.exists(final_db_path):
        raise click.ClickException(f"Database file not found: {final_db_path}")

    try:
        export_database(final_db_path, final_export_path)

        export_dir = final_export_path or os.path.join(os.getcwd(), "export")
        click.echo(f"Successfully exported database to {export_dir}")

        # List exported files
        if os.path.exists(export_dir):
            files = [f for f in os.listdir(export_dir) if f.endswith('.tsv')]
            if files:
                click.echo(f"Created {len(files)} TSV file(s):")
                for file in sorted(files):
                    file_path = os.path.join(export_dir, file)
                    # Count lines (minus header)
                    with open(file_path, 'r') as f:
                        line_count = sum(1 for _ in f) - 1
                    click.echo(f"  {file} ({line_count} rows)")

    except Exception as e:
        click.echo(f"Error during export: {e}", err=True)
        raise click.ClickException(str(e))


@cli.command()
@click.option('--db-path', type=click.Path(),
              help='Path to SQLite database file (defaults to md_manager.db)')
@click.option('--force', is_flag=True,
              help='Force full sync instead of incremental sync')
@click.option('--dry-run', is_flag=True,
              help='Show what would be synced without making changes')
@click.option('--token',
              help='GitHub token (overrides config and environment)')
@click.option('--repo-owner',
              help='GitHub repository owner (overrides config)')
@click.option('--repo-name',
              help='GitHub repository name (overrides config)')
@click.pass_context
def sync(ctx, db_path, force, dry_run, token, repo_owner, repo_name):
    """
    Synchronize GitHub issues with local markdown files (GitHub → Local).

    Fetches issues from GitHub and updates the local database with their metadata.
    Can perform incremental sync (default) or full sync with --force flag.

    Examples:
      \b
      # Preview sync without making changes
      python -m md_manager.cli sync --dry-run --repo-owner octocat --repo-name Hello-World

      \b
      # Sync issues from GitHub repository
      python -m md_manager.cli sync --repo-owner octocat --repo-name Hello-World

      \b
      # Force full sync (re-downloads all issues)
      python -m md_manager.cli sync --force --repo-owner octocat --repo-name Hello-World

      \b
      # Use custom token and database
      python -m md_manager.cli sync --token ghp_xxx --db-path custom.db --repo-owner user --repo-name repo
    """
    # Load configuration
    config_path = ctx.obj.get('config_path')
    cli_options = {
        'token': token,
        'repo_owner': repo_owner,
        'repo_name': repo_name
    }
    config = Config(config_path, cli_options)

    try:
        github_config = config.get_github_config()

        # Validate configuration for sync
        github_config = config.validate_github_config(github_config)

    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        click.echo("\nTo configure GitHub sync:")
        click.echo("1. Set environment variables:")
        click.echo("   export MD_MANAGER_TOKEN=your_github_token")
        click.echo("   export MD_MANAGER_REPO_OWNER=your_username")
        click.echo("   export MD_MANAGER_REPO_NAME=your_repo")
        click.echo("\n2. Or create a configuration file:")
        click.echo("   Run: md-manager config create-sample")
        raise click.ClickException("GitHub sync configuration is incomplete")

    # Handle database path
    if not db_path:
        # Try to find database in current directory
        possible_db_names = ['md_manager.db', 'notes_md_manager.db']
        for db_name in possible_db_names:
            test_path = os.path.join(os.getcwd(), db_name)
            if os.path.exists(test_path):
                db_path = test_path
                break

        if not db_path:
            raise click.ClickException("No database found. Run 'md-manager collate' first or specify --db-path")

    # Verify database exists
    if not os.path.exists(db_path):
        raise click.ClickException(f"Database file not found: {db_path}")

    # Show configuration info
    click.echo(f"GitHub Repository: {github_config.repo_owner}/{github_config.repo_name}")
    click.echo(f"Database: {db_path}")
    click.echo(f"Sync mode: {'Full' if force else 'Incremental'}")

    if dry_run:
        click.echo("DRY RUN: No changes will be made")

    try:
        # Initialize syncer
        syncer = GitHubIssueSyncer(db_path, github_config)

        if dry_run:
            # For dry run, just fetch issues but don't update database
            click.echo("\nFetching issues from GitHub...")
            since = None if force else syncer.get_last_sync_time()
            issues = syncer.fetch_issues(since=since)

            click.echo(f"\nWould process {len(issues)} issues:")
            for issue in issues:
                issue_info = f"#{issue['number']}: {issue['title']}"
                if len(issue_info) > 80:
                    issue_info = issue_info[:77] + "..."
                click.echo(f"  {issue_info}")

            click.echo(f"\nDry run complete. {len(issues)} issues would be processed.")

        else:
            # Perform actual sync
            click.echo("\nStarting GitHub sync...")

            with click.progressbar(length=100, label='Syncing issues') as bar:
                stats = syncer.sync_issues(force_full_sync=force)
                bar.update(100)

            # Display results
            click.echo(f"\nSync completed successfully!")
            click.echo(f"  Issues fetched: {stats['total_fetched']}")
            click.echo(f"  Files matched: {stats['matched_files']}")
            click.echo(f"  Files updated: {stats['updated_files']}")
            click.echo(f"  Orphaned issues: {stats['orphaned_issues']}")

            # Display rate limit information if available
            if 'api_requests_made' in stats:
                click.echo(f"\nAPI Usage:")
                click.echo(f"  Requests made: {stats['api_requests_made']}")
                if stats.get('rate_limit_hits', 0) > 0:
                    click.echo(f"  Rate limit hits: {stats['rate_limit_hits']}")
                if stats.get('total_delay_time', 0) > 0:
                    click.echo(f"  Total delay time: {stats['total_delay_time']:.1f}s")

            if stats['errors'] > 0:
                click.echo(f"  Errors: {stats['errors']}", err=True)

            # Show orphaned issues if any
            if stats['orphaned_issues'] > 0:
                click.echo(f"\nNote: {stats['orphaned_issues']} issue(s) don't have matching local files.")
                click.echo("These are stored in the database and can be accessed via export.")

    except GitHubSyncError as e:
        click.echo(f"Sync error: {e}", err=True)
        raise click.ClickException(str(e))
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.ClickException(str(e))


@cli.command()
@click.argument('output_path', required=False, default='md-manager.yml')
@click.option('--format', 'output_format', type=click.Choice(['yaml', 'json']), default='yaml',
              help='Output format for the configuration file')
@click.pass_context
def create_sample_config(ctx, output_path, output_format):
    """
    Create a sample configuration file with all available options.

    OUTPUT_PATH: Path where to create the configuration file (default: md-manager.yml)

    Examples:
      \b
      # Create YAML config (default)
      python -m md_manager.cli create-sample-config

      \b
      # Create JSON config
      python -m md_manager.cli create-sample-config --format json config.json

      \b
      # Create config in specific location
      python -m md_manager.cli create-sample-config /path/to/my-config.yml
    """
    # Determine format from file extension if not specified
    if output_format == 'yaml' and output_path.endswith('.json'):
        output_format = 'json'
    elif output_format == 'json' and output_path.endswith(('.yml', '.yaml')):
        output_format = 'yaml'

    # Adjust extension to match format
    if output_format == 'yaml' and not output_path.endswith(('.yml', '.yaml')):
        if not output_path.endswith('.json'):
            output_path += '.yml'
    elif output_format == 'json' and not output_path.endswith('.json'):
        if output_path.endswith(('.yml', '.yaml')):
            output_path = output_path.rsplit('.', 1)[0] + '.json'
        else:
            output_path += '.json'

    try:
        config = Config()
        config.create_sample_config(output_path)

        click.echo(f"Created sample configuration file: {output_path}")
        click.echo("\nTo get started with GitHub sync:")
        click.echo("1. Edit the configuration file with your GitHub details")
        click.echo("2. Set your GitHub token in environment variable: MD_MANAGER_TOKEN")
        click.echo("3. Run: md-manager sync")

    except Exception as e:
        click.echo(f"Error creating configuration file: {e}", err=True)
        raise click.ClickException(str(e))


@cli.command()
@click.option('--db-path', type=click.Path(),
              help='Path to SQLite database file (defaults to md_manager.db)')
@click.option('--conflict-resolution', type=click.Choice(['local_wins', 'remote_wins', 'manual', 'skip']),
              default='local_wins', help='Conflict resolution strategy')
@click.option('--dry-run', is_flag=True,
              help='Show what would be synced without making changes')
@click.option('--since', help='Sync changes since this ISO 8601 timestamp')
@click.option('--token', help='GitHub token (overrides config and environment)')
@click.option('--repo-owner', help='GitHub repository owner (overrides config)')
@click.option('--repo-name', help='GitHub repository name (overrides config)')
@click.pass_context
def push(ctx, db_path, conflict_resolution, dry_run, since, token, repo_owner, repo_name):
    """
    Push local markdown files to GitHub issues (Local → GitHub sync).

    Creates new GitHub issues for new local files and updates existing issues
    with local changes. This is the Local → GitHub direction of synchronization.

    Examples:
      \b
      # Preview what would be pushed without making changes
      python -m md_manager.cli push --dry-run --repo-owner octocat --repo-name Hello-World

      \b
      # Push local issues to GitHub repository
      python -m md_manager.cli push --repo-owner octocat --repo-name Hello-World

      \b
      # Push with conflict resolution (GitHub wins conflicts)
      python -m md_manager.cli push --conflict-resolution remote_wins --repo-owner user --repo-name repo

      \b
      # Push changes since specific timestamp
      python -m md_manager.cli push --since 2025-01-01T00:00:00Z --repo-owner user --repo-name repo
    """
    # Load configuration
    config_path = ctx.obj.get('config_path')
    cli_options = {
        'token': token,
        'repo_owner': repo_owner,
        'repo_name': repo_name
    }
    config = Config(config_path, cli_options)

    try:
        github_config = config.get_github_config()
        github_config = config.validate_github_config(github_config)

    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        raise click.ClickException("GitHub sync configuration is incomplete")

    # Handle database path
    if not db_path:
        possible_db_names = ['md_manager.db', 'notes_md_manager.db']
        for db_name in possible_db_names:
            test_path = os.path.join(os.getcwd(), db_name)
            if os.path.exists(test_path):
                db_path = test_path
                break

        if not db_path:
            raise click.ClickException("No database found. Run 'md-manager collate' first or specify --db-path")

    if not os.path.exists(db_path):
        raise click.ClickException(f"Database file not found: {db_path}")

    # Parse conflict resolution strategy
    from .local_sync import ConflictResolution
    resolution_map = {
        'local_wins': ConflictResolution.LOCAL_WINS,
        'remote_wins': ConflictResolution.REMOTE_WINS,
        'manual': ConflictResolution.MANUAL,
        'skip': ConflictResolution.SKIP
    }
    resolution_strategy = resolution_map[conflict_resolution]

    # Show configuration info
    click.echo(f"GitHub Repository: {github_config.repo_owner}/{github_config.repo_name}")
    click.echo(f"Database: {db_path}")
    click.echo(f"Conflict Resolution: {conflict_resolution}")

    if dry_run:
        click.echo("DRY RUN: No changes will be made")

    try:
        # Initialize syncer
        from .local_sync import LocalToGitHubSyncer, LocalSyncError, ConflictError
        syncer = LocalToGitHubSyncer(db_path, github_config)

        if dry_run:
            click.echo("\nDetecting local changes...")
            stats = syncer.sync_to_github(
                conflict_resolution=resolution_strategy,
                dry_run=True,
                since=since
            )

            click.echo(f"\nDry run complete. Would process {stats['total_files']} files:")
            click.echo(f"  New issues to create: {stats['new_issues']}")
            click.echo(f"  Issues to update: {stats['updated_issues']}")
            click.echo(f"  Files to skip: {stats['skipped_files']}")

        else:
            click.echo("\nStarting Local → GitHub sync...")

            with click.progressbar(length=100, label='Pushing to GitHub') as bar:
                stats = syncer.sync_to_github(
                    conflict_resolution=resolution_strategy,
                    dry_run=False,
                    since=since
                )
                bar.update(100)

            # Display results
            click.echo(f"\nPush completed successfully!")
            click.echo(f"  New issues created: {stats['new_issues']}")
            click.echo(f"  Issues updated: {stats['updated_issues']}")
            click.echo(f"  Files skipped: {stats['skipped_files']}")
            click.echo(f"  Conflicts resolved: {stats['conflicts_resolved']}")

            # Display rate limit information if available
            if 'api_requests_made' in stats:
                click.echo(f"\nAPI Usage:")
                click.echo(f"  Requests made: {stats['api_requests_made']}")
                if stats.get('rate_limit_hits', 0) > 0:
                    click.echo(f"  Rate limit hits: {stats['rate_limit_hits']}")
                if stats.get('total_delay_time', 0) > 0:
                    click.echo(f"  Total delay time: {stats['total_delay_time']:.1f}s")

            if stats['errors'] > 0:
                click.echo(f"  Errors: {stats['errors']}", err=True)

    except ConflictError as e:
        click.echo(f"Sync stopped due to conflicts: {e}", err=True)
        click.echo("\nConflicts found:")
        for conflict in e.conflicts[:5]:  # Show first 5 conflicts
            click.echo(f"  {conflict.file_path}: {conflict.conflict_type} conflict")
        if len(e.conflicts) > 5:
            click.echo(f"  ... and {len(e.conflicts) - 5} more conflicts")
        click.echo("\nUse --conflict-resolution to specify how to handle conflicts")
        raise click.ClickException("Sync failed due to unresolved conflicts")

    except LocalSyncError as e:
        click.echo(f"Local sync error: {e}", err=True)
        raise click.ClickException(str(e))

    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.ClickException(str(e))


@cli.command()
@click.option('--db-path', type=click.Path(),
              help='Path to SQLite database file (defaults to md_manager.db)')
@click.option('--strategy', type=click.Choice(['github_first', 'local_first', 'timestamp_based', 'conservative']),
              default='github_first', help='Bidirectional sync strategy')
@click.option('--conflict-resolution', type=click.Choice(['local_wins', 'remote_wins', 'manual', 'skip']),
              default='local_wins', help='Conflict resolution strategy')
@click.option('--force', is_flag=True,
              help='Force full sync instead of incremental sync')
@click.option('--dry-run', is_flag=True,
              help='Show what would be synced without making changes')
@click.option('--token', help='GitHub token (overrides config and environment)')
@click.option('--repo-owner', help='GitHub repository owner (overrides config)')
@click.option('--repo-name', help='GitHub repository name (overrides config)')
@click.pass_context
def sync_bidirectional(ctx, db_path, strategy, conflict_resolution, force, dry_run, token, repo_owner, repo_name):
    """
    Synchronize in both directions between local files and GitHub issues.

    Performs both GitHub → Local and Local → GitHub synchronization using
    the specified strategy to coordinate the sync operations.

    Strategies:
      github_first: Download from GitHub first, then push local changes
      local_first: Push local changes first, then download from GitHub
      timestamp_based: Sync based on modification timestamps
      conservative: Skip conflicts for manual resolution

    Examples:
      \b
      # Preview bidirectional sync without making changes
      python -m md_manager.cli sync-bidirectional --dry-run --repo-owner octocat --repo-name Hello-World

      \b
      # GitHub-first strategy (recommended)
      python -m md_manager.cli sync-bidirectional --strategy github_first --repo-owner user --repo-name repo

      \b
      # Conservative strategy (skip conflicts)
      python -m md_manager.cli sync-bidirectional --strategy conservative --conflict-resolution manual

      \b
      # Force full sync with local wins conflicts
      python -m md_manager.cli sync-bidirectional --force --conflict-resolution local_wins --repo-owner user --repo-name repo
    """
    # Load configuration
    config_path = ctx.obj.get('config_path')
    cli_options = {
        'token': token,
        'repo_owner': repo_owner,
        'repo_name': repo_name
    }
    config = Config(config_path, cli_options)

    try:
        github_config = config.get_github_config()
        github_config = config.validate_github_config(github_config)

    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        raise click.ClickException("GitHub sync configuration is incomplete")

    # Handle database path
    if not db_path:
        possible_db_names = ['md_manager.db', 'notes_md_manager.db']
        for db_name in possible_db_names:
            test_path = os.path.join(os.getcwd(), db_name)
            if os.path.exists(test_path):
                db_path = test_path
                break

        if not db_path:
            raise click.ClickException("No database found. Run 'md-manager collate' first or specify --db-path")

    if not os.path.exists(db_path):
        raise click.ClickException(f"Database file not found: {db_path}")

    # Parse strategies
    from .bidirectional_sync import SyncStrategy
    from .local_sync import ConflictResolution

    strategy_map = {
        'github_first': SyncStrategy.GITHUB_FIRST,
        'local_first': SyncStrategy.LOCAL_FIRST,
        'timestamp_based': SyncStrategy.TIMESTAMP_BASED,
        'conservative': SyncStrategy.CONSERVATIVE
    }
    sync_strategy = strategy_map[strategy]

    resolution_map = {
        'local_wins': ConflictResolution.LOCAL_WINS,
        'remote_wins': ConflictResolution.REMOTE_WINS,
        'manual': ConflictResolution.MANUAL,
        'skip': ConflictResolution.SKIP
    }
    resolution_strategy = resolution_map[conflict_resolution]

    # Show configuration info
    click.echo(f"GitHub Repository: {github_config.repo_owner}/{github_config.repo_name}")
    click.echo(f"Database: {db_path}")
    click.echo(f"Sync Strategy: {strategy}")
    click.echo(f"Conflict Resolution: {conflict_resolution}")
    click.echo(f"Sync Mode: {'Full' if force else 'Incremental'}")

    if dry_run:
        click.echo("DRY RUN: No changes will be made")

    try:
        # Initialize bidirectional syncer
        from .bidirectional_sync import BidirectionalSyncer, BidirectionalSyncError
        syncer = BidirectionalSyncer(db_path, github_config)

        click.echo("\nStarting bidirectional synchronization...")

        if dry_run:
            result = syncer.sync_bidirectional(
                strategy=sync_strategy,
                conflict_resolution=resolution_strategy,
                force_full_sync=force,
                dry_run=True
            )

            click.echo(f"\nDry run complete. Duration: {result.total_duration:.2f}s")

        else:
            with click.progressbar(length=100, label='Bidirectional sync') as bar:
                result = syncer.sync_bidirectional(
                    strategy=sync_strategy,
                    conflict_resolution=resolution_strategy,
                    force_full_sync=force,
                    dry_run=False
                )
                bar.update(100)

            # Display results
            click.echo(f"\nBidirectional sync completed!")
            click.echo(f"  Duration: {result.total_duration:.2f}s")
            click.echo(f"  Success: {result.success}")

            if result.github_to_local_stats:
                gh_stats = result.github_to_local_stats
                click.echo(f"\nGitHub → Local:")
                click.echo(f"  Issues fetched: {gh_stats.get('total_fetched', 0)}")
                click.echo(f"  Files matched: {gh_stats.get('matched_files', 0)}")
                click.echo(f"  Files updated: {gh_stats.get('updated_files', 0)}")

            if result.local_to_github_stats:
                local_stats = result.local_to_github_stats
                click.echo(f"\nLocal → GitHub:")
                click.echo(f"  New issues created: {local_stats.get('new_issues', 0)}")
                click.echo(f"  Issues updated: {local_stats.get('updated_issues', 0)}")
                click.echo(f"  Files skipped: {local_stats.get('skipped_files', 0)}")

            if result.conflicts:
                click.echo(f"\nConflicts: {len(result.conflicts)} unresolved")
                for conflict in result.conflicts[:3]:
                    click.echo(f"  {conflict.file_path}: {conflict.conflict_type}")

            if result.error_message:
                click.echo(f"\nError: {result.error_message}", err=True)

    except BidirectionalSyncError as e:
        click.echo(f"Bidirectional sync error: {e}", err=True)
        raise click.ClickException(str(e))

    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.ClickException(str(e))


if __name__ == '__main__':
    cli()
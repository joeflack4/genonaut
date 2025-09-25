"""CLI commands for ComfyUI model management."""

import click
import logging
from pathlib import Path
from typing import List

from genonaut.api.config import get_settings
from genonaut.api.services.model_discovery_service import ModelDiscoveryService
from genonaut.db.database import get_database_session

logger = logging.getLogger(__name__)


@click.group()
def models():
    """ComfyUI model management commands."""
    pass


@models.command()
@click.option(
    '--paths',
    '-p',
    multiple=True,
    help='Additional model paths to scan (can be specified multiple times)'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be discovered without updating database'
)
@click.option(
    '--verbose',
    '-v',
    is_flag=True,
    help='Enable verbose output'
)
def discover(paths: List[str], dry_run: bool, verbose: bool):
    """Discover available ComfyUI models."""
    if verbose:
        logging.basicConfig(level=logging.INFO)

    with get_database_session() as db:
        service = ModelDiscoveryService(db)

        # Add custom paths if provided
        search_paths = list(paths) if paths else None

        click.echo("🔍 Discovering ComfyUI models...")
        discovered_models = service.discover_models(search_paths)

        if not discovered_models:
            click.echo("❌ No models found")
            return

        total_models = sum(len(models) for models in discovered_models.values())
        click.echo(f"✅ Found {total_models} models across {len(discovered_models)} types")

        for model_type, models in discovered_models.items():
            click.echo(f"\n📁 {model_type.upper()} ({len(models)} models):")
            for model in models[:5]:  # Show first 5 models of each type
                size_mb = round(model['file_size'] / (1024 * 1024), 1)
                click.echo(f"  • {model['name']} ({size_mb}MB)")

            if len(models) > 5:
                click.echo(f"  ... and {len(models) - 5} more")

        if not dry_run:
            click.echo("\n💾 Updating database...")
            stats = service.update_model_database(discovered_models)

            click.echo("📊 Update Statistics:")
            click.echo(f"  Added: {stats['added']}")
            click.echo(f"  Updated: {stats['updated']}")
            click.echo(f"  Deactivated: {stats['deactivated']}")
            if stats['errors'] > 0:
                click.echo(f"  Errors: {stats['errors']}")
        else:
            click.echo("\n🔍 Dry run - no changes made to database")


@models.command()
@click.option(
    '--model-type',
    '-t',
    help='Filter by model type (checkpoint, lora, etc.)'
)
@click.option(
    '--active-only',
    is_flag=True,
    default=True,
    help='Show only active models'
)
@click.option(
    '--format-json',
    is_flag=True,
    help='Output in JSON format'
)
def list(model_type: str, active_only: bool, format_json: bool):
    """List available models."""
    with get_database_session() as db:
        service = ModelDiscoveryService(db)

        if model_type:
            models = service.repository.get_models_by_type(model_type, active_only)
        else:
            models = service.repository.get_all_models(active_only)

        if format_json:
            import json
            model_data = []
            for model in models:
                model_data.append({
                    'id': model.id,
                    'name': model.name,
                    'type': model.model_type,
                    'file_path': model.file_path,
                    'file_size': model.file_size,
                    'is_active': model.is_active,
                    'format': model.format
                })
            click.echo(json.dumps(model_data, indent=2))
        else:
            if not models:
                click.echo("No models found")
                return

            click.echo(f"Found {len(models)} models:")

            # Group by type
            by_type = {}
            for model in models:
                if model.model_type not in by_type:
                    by_type[model.model_type] = []
                by_type[model.model_type].append(model)

            for model_type, type_models in by_type.items():
                click.echo(f"\n📁 {model_type.upper()} ({len(type_models)} models):")
                for model in type_models:
                    size_mb = round(model.file_size / (1024 * 1024), 1)
                    status = "✅" if model.is_active else "❌"
                    click.echo(f"  {status} {model.name} ({size_mb}MB)")


@models.command()
def stats():
    """Show model statistics."""
    with get_database_session() as db:
        service = ModelDiscoveryService(db)
        stats = service.get_model_statistics()

        click.echo("📊 Model Statistics:")
        click.echo(f"  Total models: {stats['total_models']}")
        click.echo(f"  Active models: {stats['active_models']}")
        click.echo(f"  Inactive models: {stats['inactive_models']}")

        click.echo("\n📁 By Type:")
        for key, value in stats.items():
            if key.endswith('_models') and not key.startswith('total') and not key.startswith('active') and not key.startswith('inactive'):
                model_type = key.replace('_models', '')
                click.echo(f"  {model_type}: {value}")


@models.command()
@click.option(
    '--model-id',
    type=int,
    help='Model ID to activate/deactivate'
)
@click.option(
    '--name',
    help='Model name to activate/deactivate'
)
@click.option(
    '--activate',
    is_flag=True,
    help='Activate the model'
)
@click.option(
    '--deactivate',
    is_flag=True,
    help='Deactivate the model'
)
def toggle(model_id: int, name: str, activate: bool, deactivate: bool):
    """Activate or deactivate a model."""
    if not (model_id or name):
        click.echo("❌ Either --model-id or --name must be specified")
        return

    if activate and deactivate:
        click.echo("❌ Cannot specify both --activate and --deactivate")
        return

    if not (activate or deactivate):
        click.echo("❌ Either --activate or --deactivate must be specified")
        return

    with get_database_session() as db:
        service = ModelDiscoveryService(db)

        if name:
            model = service.repository.get_model_by_name(name)
            if not model:
                click.echo(f"❌ Model '{name}' not found")
                return
            model_id = model.id

        new_status = activate
        success = service.repository.update_model_status(model_id, new_status)

        if success:
            action = "activated" if new_status else "deactivated"
            click.echo(f"✅ Model {action} successfully")
        else:
            click.echo("❌ Failed to update model status")


@models.command()
@click.confirmation_option(
    prompt='Are you sure you want to remove orphaned models?'
)
def cleanup():
    """Remove model records for files that no longer exist."""
    with get_database_session() as db:
        service = ModelDiscoveryService(db)
        removed_count = service.cleanup_orphaned_models()

        if removed_count > 0:
            click.echo(f"✅ Removed {removed_count} orphaned model records")
        else:
            click.echo("✅ No orphaned models found")


@models.command()
@click.argument('model_names', nargs=-1, required=True)
def validate(model_names):
    """Validate that specified models are available."""
    with get_database_session() as db:
        service = ModelDiscoveryService(db)
        availability = service.validate_model_availability(list(model_names))

        click.echo("📋 Model Availability:")
        for model_name, is_available in availability.items():
            status = "✅" if is_available else "❌"
            click.echo(f"  {status} {model_name}")


@models.command()
@click.option(
    '--config-file',
    type=click.Path(exists=True),
    help='Path to ComfyUI config file to search for model paths'
)
def scan_config(config_file: str):
    """Scan ComfyUI configuration for additional model paths."""
    # This is a placeholder for more advanced config scanning
    click.echo("🔍 Scanning ComfyUI configuration...")

    if config_file:
        config_path = Path(config_file)
        click.echo(f"Reading config from: {config_path}")
        # TODO: Implement config file parsing

    # For now, just show the default paths that would be searched
    with get_database_session() as db:
        service = ModelDiscoveryService(db)

        click.echo("\n📂 Default search paths:")
        for path in service.model_base_paths:
            exists = "✅" if Path(path).exists() else "❌"
            click.echo(f"  {exists} {path}")


if __name__ == "__main__":
    models()
"""Genonaut CLI for running services with proper configuration."""

import os
from pathlib import Path
from typing import Optional

import typer
import uvicorn

from genonaut.config_loader import load_env_for_runtime, load_config


app = typer.Typer(add_completion=False, help="Genonaut CLI for running services")


def _load_envs(explicit_env: Optional[str]):
    """Load environment files with proper precedence."""
    # load_env_for_runtime handles: shared + explicit + local .env
    load_env_for_runtime(explicit_env)


def _derive_paths_from_target(
    env_target: Optional[str],
    env_path: Optional[str],
    config_path: Optional[str]
) -> tuple[Optional[str], Optional[str]]:
    """Derive file paths from ENV_TARGET if not explicitly provided.

    Args:
        env_target: Environment target (e.g., 'local-dev', 'cloud-prod')
        env_path: Explicit env file path (takes precedence)
        config_path: Explicit config file path (takes precedence)

    Returns:
        Tuple of (env_path, config_path)
    """
    # Only fill in missing values
    if env_target and not env_path:
        candidate = f"env/.env.{env_target}"
        if Path(candidate).is_file():
            env_path = candidate

    if env_target and not config_path:
        candidate = f"config/{env_target}.json"
        if Path(candidate).is_file():
            config_path = candidate

    return env_path, config_path


@app.command()
def run_api(
    host: Optional[str] = typer.Option(None, help="Host to bind to (overrides config)"),
    port: Optional[int] = typer.Option(None, help="Port to bind to (overrides config)"),
    reload: bool = typer.Option(True, help="Enable auto-reload"),
    workers: Optional[int] = typer.Option(None, help="Number of worker processes"),
    env_path: Optional[str] = typer.Option(None, help="Path to .env file to load"),
    config_path: Optional[str] = typer.Option(None, help="Path to app config file"),
    env_target: Optional[str] = typer.Option(
        None,
        help="Environment target (e.g., 'local-dev', 'local-test', 'cloud-prod')"
    ),
):
    """Run the Genonaut API server with proper configuration.

    Examples:
        # Using env-target shortcut
        python -m genonaut.cli run-api --env-target local-dev

        # Using explicit paths
        python -m genonaut.cli run-api --env-path env/.env.local-dev --config-path config/local-dev.json

        # With workers
        python -m genonaut.cli run-api --env-target local-dev --workers 4
    """
    # Derive defaults from ENV_TARGET, then load envs
    env_path, config_path = _derive_paths_from_target(env_target, env_path, config_path)

    # Validate that we have a config path
    if not config_path:
        typer.echo("Error: Either --config-path or --env-target must be provided", err=True)
        raise typer.Exit(1)

    # Load configuration to get host/port defaults
    config = load_config(config_path, env_path)

    # Use config values if not explicitly provided via CLI
    actual_host = host if host is not None else config.get("api-host", "0.0.0.0")
    actual_port = port if port is not None else config.get("api-port", 8001)

    # Export ENV_TARGET and config path for the app to read on startup
    if env_target:
        os.environ["ENV_TARGET"] = env_target
    if config_path:
        os.environ["APP_CONFIG_PATH"] = str(config_path)

    typer.echo(f"Starting Genonaut API server...")
    typer.echo(f"  ENV_TARGET: {env_target or 'not set'}")
    typer.echo(f"  Config: {config_path}")
    typer.echo(f"  Env file: {env_path or 'not specified'}")
    typer.echo(f"  Host: {actual_host}:{actual_port}")
    typer.echo(f"  Reload: {reload}")
    typer.echo(f"  Workers: {workers or 'default'}")

    # Build uvicorn kwargs
    uvicorn_kwargs = dict(host=actual_host, port=actual_port, reload=reload)
    if workers:
        uvicorn_kwargs["workers"] = workers
        # Can't use reload with multiple workers
        if workers > 1:
            uvicorn_kwargs["reload"] = False

    uvicorn.run("genonaut.api.main:app", **uvicorn_kwargs)


@app.command()
def init_db(
    env_path: Optional[str] = typer.Option(None, help="Path to .env file to load"),
    config_path: Optional[str] = typer.Option(None, help="Path to app config file"),
    env_target: Optional[str] = typer.Option(
        None,
        help="Environment target (e.g., 'local-dev', 'local-test', 'cloud-prod')"
    ),
    drop_existing: bool = typer.Option(False, help="Drop existing tables"),
):
    """Initialize the database with proper configuration.

    Examples:
        # Initialize dev database
        python -m genonaut.cli init-db --env-target local-dev

        # Initialize and drop existing
        python -m genonaut.cli init-db --env-target local-demo --drop-existing
    """
    # Derive defaults from ENV_TARGET, then load envs
    env_path, config_path = _derive_paths_from_target(env_target, env_path, config_path)

    # Validate that we have a config path
    if not config_path:
        typer.echo("Error: Either --config-path or --env-target must be provided", err=True)
        raise typer.Exit(1)

    # Load environment files
    _load_envs(env_path)

    # Export ENV_TARGET and config path for the app to read
    if env_target:
        os.environ["ENV_TARGET"] = env_target
    if config_path:
        os.environ["APP_CONFIG_PATH"] = str(config_path)

    typer.echo(f"Initializing database...")
    typer.echo(f"  ENV_TARGET: {env_target or 'not set'}")
    typer.echo(f"  Config: {config_path}")
    typer.echo(f"  Env file: {env_path or 'not specified'}")
    typer.echo(f"  Drop existing: {drop_existing}")

    # Import and call the initialization function
    from genonaut.db.init import initialize_database
    initialize_database(drop_existing=drop_existing)


if __name__ == "__main__":
    app()

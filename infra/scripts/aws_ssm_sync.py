#!/usr/bin/env python3
"""
AWS SSM Parameter Store synchronization script.

This script:
1. Loads environment variables from .env files based on cloud environment targets
2. Pushes each environment variable as a SecureString parameter to AWS SSM
3. Generates a Terraform configuration file (ecs_secrets.auto.tf) with SSM references

Environment detection:
- Scans env/ directory for files matching .env.cloud-*
- The * portion becomes the environment name (e.g., demo, dev, prod, test)

Environment variable precedence (lowest to highest):
1. env/.env.shared - Shared secrets across all environments
2. env/.env.cloud-{env} - Environment-specific secrets
3. Process environment variables - Shell exports

Usage:
    python infra/scripts/aws_ssm_sync.py [options]

    # Dry run (show what would be done without making changes)
    python infra/scripts/aws_ssm_sync.py --dry-run

    # Sync specific environment(s)
    python infra/scripts/aws_ssm_sync.py --env demo
    python infra/scripts/aws_ssm_sync.py --env demo --env prod

    # Generate Terraform file only (no SSM push)
    python infra/scripts/aws_ssm_sync.py --terraform-only

    # Skip Terraform generation
    python infra/scripts/aws_ssm_sync.py --no-terraform
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(msg: str) -> None:
    """Print a header message."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {msg} ==={Colors.ENDC}")


def print_info(msg: str) -> None:
    """Print an info message."""
    print(f"{Colors.OKBLUE}{msg}{Colors.ENDC}")


def print_success(msg: str) -> None:
    """Print a success message."""
    print(f"{Colors.OKGREEN}{msg}{Colors.ENDC}")


def print_warning(msg: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}{msg}{Colors.ENDC}")


def print_error(msg: str) -> None:
    """Print an error message."""
    print(f"{Colors.FAIL}{msg}{Colors.ENDC}", file=sys.stderr)


def find_cloud_environments(env_dir: Path) -> List[str]:
    """
    Scan env/ directory for .env.cloud-* files and extract environment names.

    Args:
        env_dir: Path to the env directory

    Returns:
        List of environment names (e.g., ['demo', 'dev', 'prod', 'test'])
    """
    cloud_env_files = list(env_dir.glob(".env.cloud-*"))

    if not cloud_env_files:
        print_warning(f"No .env.cloud-* files found in {env_dir}")
        return []

    environments = []
    for env_file in cloud_env_files:
        # Extract environment name from .env.cloud-{env}
        env_name = env_file.name.replace(".env.cloud-", "")
        environments.append(env_name)

    return sorted(environments)


def load_env_file(env_file: Path) -> Dict[str, str]:
    """
    Load environment variables from a .env file.

    Args:
        env_file: Path to the .env file

    Returns:
        Dictionary of environment variables
    """
    env_vars = {}

    if not env_file.exists():
        return env_vars

    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                env_vars[key] = value

    return env_vars


def load_environment_variables(env_dir: Path, environment: str) -> Dict[str, str]:
    """
    Load environment variables with proper precedence order.

    Load order (lowest to highest priority):
    1. env/.env.shared - Shared secrets
    2. env/.env.cloud-{env} - Environment-specific secrets
    3. Process environment variables

    Args:
        env_dir: Path to the env directory
        environment: Environment name (e.g., 'demo', 'dev', 'prod', 'test')

    Returns:
        Dictionary of environment variables
    """
    env_vars = {}

    # 1. Load shared secrets
    shared_env_file = env_dir / ".env.shared"
    if shared_env_file.exists():
        shared_vars = load_env_file(shared_env_file)
        env_vars.update(shared_vars)
        print_info(f"  Loaded {len(shared_vars)} variables from .env.shared")

    # 2. Load environment-specific secrets
    env_specific_file = env_dir / f".env.cloud-{environment}"
    if env_specific_file.exists():
        env_specific_vars = load_env_file(env_specific_file)
        env_vars.update(env_specific_vars)
        print_info(f"  Loaded {len(env_specific_vars)} variables from .env.cloud-{environment}")

    # 3. Override with process environment variables
    # Only override if the key already exists in our loaded env vars
    process_overrides = 0
    for key in env_vars.keys():
        if key in os.environ:
            env_vars[key] = os.environ[key]
            process_overrides += 1

    if process_overrides > 0:
        print_info(f"  Applied {process_overrides} overrides from process environment")

    return env_vars


def push_to_ssm(
    environment: str,
    env_vars: Dict[str, str],
    aws_profile: Optional[str],
    aws_region: Optional[str],
    dry_run: bool = False,
    use_env_prefix: bool = True
) -> bool:
    """
    Push environment variables to AWS SSM Parameter Store.

    Args:
        environment: Environment name (e.g., 'demo', 'dev', 'prod', 'test')
        env_vars: Dictionary of environment variables to push
        aws_profile: AWS profile to use (optional)
        aws_region: AWS region to use (optional)
        dry_run: If True, only show what would be done without making changes
        use_env_prefix: If True, use /genonaut/{env}/{key} path format

    Returns:
        True if successful, False otherwise
    """
    if not env_vars:
        print_warning(f"No environment variables to push for {environment}")
        return True

    print_header(f"Pushing {len(env_vars)} parameters to SSM for environment: {environment}")

    success_count = 0
    error_count = 0

    for key, value in env_vars.items():
        # Construct SSM parameter name
        if use_env_prefix:
            parameter_name = f"/genonaut/{environment}/{key}"
        else:
            parameter_name = f"/genonaut/{key}"

        # Build AWS CLI command
        cmd = [
            "aws", "ssm", "put-parameter",
            "--name", parameter_name,
            "--value", value,
            "--type", "SecureString",
            "--overwrite"
        ]

        if aws_profile:
            cmd.extend(["--profile", aws_profile])

        if aws_region:
            cmd.extend(["--region", aws_region])

        if dry_run:
            # Show what would be done
            cmd_str = ' '.join(cmd[:6])  # Don't show the actual value
            print(f"  [DRY RUN] Would execute: {cmd_str} --value '***' ...")
            success_count += 1
        else:
            # Execute the command
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                print_success(f"  Pushed: {parameter_name}")
                success_count += 1
            except subprocess.CalledProcessError as e:
                print_error(f"  Failed to push {parameter_name}: {e.stderr}")
                error_count += 1

    print(f"\n{Colors.OKGREEN}Success: {success_count}{Colors.ENDC}, "
          f"{Colors.FAIL}Errors: {error_count}{Colors.ENDC}")

    return error_count == 0


def generate_terraform_file(
    environments: List[str],
    env_vars_by_env: Dict[str, Dict[str, str]],
    output_file: Path,
    use_env_prefix: bool = True,
    dry_run: bool = False
) -> bool:
    """
    Generate Terraform configuration file with SSM secret references.

    Args:
        environments: List of environment names
        env_vars_by_env: Dictionary mapping environment names to their variables
        output_file: Path to output Terraform file
        use_env_prefix: If True, use /genonaut/{env}/{key} path format
        dry_run: If True, only show what would be done without making changes

    Returns:
        True if successful, False otherwise
    """
    print_header(f"Generating Terraform configuration: {output_file}")

    if not environments:
        print_warning("No environments found, skipping Terraform generation")
        return True

    # Start building the Terraform configuration
    tf_content = []
    tf_content.append("# Auto-generated by infra/scripts/aws_ssm_sync.py")
    tf_content.append("# DO NOT EDIT MANUALLY - Changes will be overwritten")
    tf_content.append("")
    tf_content.append("# ECS task definition secrets configuration")
    tf_content.append("# These reference AWS SSM Parameter Store secrets")
    tf_content.append("")

    # Generate secrets block for each environment
    for env in environments:
        env_vars = env_vars_by_env.get(env, {})

        if not env_vars:
            tf_content.append(f"# No secrets defined for environment: {env}")
            tf_content.append("")
            continue

        tf_content.append(f"# Secrets for {env} environment")
        tf_content.append(f"locals {{")
        tf_content.append(f"  ecs_secrets_{env} = [")

        # Sort keys for consistent output
        for key in sorted(env_vars.keys()):
            if use_env_prefix:
                parameter_path = f"/genonaut/{env}/{key}"
            else:
                parameter_path = f"/genonaut/{key}"

            tf_content.append(f"    {{")
            tf_content.append(f"      name      = \"{key}\"")
            tf_content.append(f"      valueFrom = \"{parameter_path}\"")
            tf_content.append(f"    }},")

        tf_content.append(f"  ]")
        tf_content.append(f"}}")
        tf_content.append("")

    # Join all lines
    tf_file_content = "\n".join(tf_content)

    if dry_run:
        print("[DRY RUN] Would write the following to", output_file)
        print("-" * 80)
        print(tf_file_content[:500] + "..." if len(tf_file_content) > 500 else tf_file_content)
        print("-" * 80)
    else:
        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(tf_file_content)
        print_success(f"Wrote Terraform configuration to {output_file}")

    return True


def get_aws_credentials_from_env(env_vars: Dict[str, str]) -> tuple[Optional[str], Optional[str]]:
    """
    Extract AWS profile and region from environment variables.

    Args:
        env_vars: Dictionary of environment variables

    Returns:
        Tuple of (aws_profile, aws_region)
    """
    aws_profile = env_vars.get('DEPLOY_AWS_PROFILE') or os.environ.get('DEPLOY_AWS_PROFILE')
    aws_region = env_vars.get('DEPLOY_AWS_REGION') or os.environ.get('DEPLOY_AWS_REGION')

    return aws_profile, aws_region


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Sync environment variables to AWS SSM Parameter Store and generate Terraform config",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--env',
        action='append',
        dest='environments',
        help="Specific environment(s) to sync (can be specified multiple times). "
             "If not specified, all cloud environments will be synced."
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be done without making any changes"
    )

    parser.add_argument(
        '--action',
        choices=['all', 'ssm', 'terraform'],
        default='all',
        help="Which action to perform: 'all' (both SSM and Terraform), 'ssm' (push to SSM only), "
             "'terraform' (generate Terraform file only). Default: all"
    )

    # Deprecated flags for backward compatibility
    parser.add_argument(
        '--terraform-only',
        action='store_true',
        help="(Deprecated: use --action terraform) Only generate Terraform file, skip pushing to SSM"
    )

    parser.add_argument(
        '--no-terraform',
        action='store_true',
        help="(Deprecated: use --action ssm) Skip Terraform file generation"
    )

    parser.add_argument(
        '--no-env-prefix',
        action='store_true',
        help="Don't use environment prefix in SSM path (use /genonaut/{key} instead of /genonaut/{env}/{key})"
    )

    parser.add_argument(
        '--aws-profile',
        help="AWS profile to use (overrides DEPLOY_AWS_PROFILE from .env files)"
    )

    parser.add_argument(
        '--aws-region',
        help="AWS region to use (overrides DEPLOY_AWS_REGION from .env files)"
    )

    parser.add_argument(
        '--env-dir',
        type=Path,
        default=Path('env'),
        help="Path to env directory (default: env/)"
    )

    parser.add_argument(
        '--output-file',
        type=Path,
        default=Path('infra/main/ecs_secrets.auto.tf'),
        help="Output path for Terraform file (default: infra/main/ecs_secrets.auto.tf)"
    )

    args = parser.parse_args()

    # Resolve project root (assuming script is in infra/scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    env_dir = project_root / args.env_dir

    if not env_dir.exists():
        print_error(f"Environment directory not found: {env_dir}")
        return 1

    print_header("AWS SSM Parameter Store Sync")
    print_info(f"Project root: {project_root}")
    print_info(f"Environment directory: {env_dir}")

    if args.dry_run:
        print_warning("DRY RUN MODE - No changes will be made")

    # Find cloud environments
    all_environments = find_cloud_environments(env_dir)

    if not all_environments:
        print_error("No cloud environments found. Looking for .env.cloud-* files in env/ directory.")
        return 1

    # Determine which environments to sync
    if args.environments:
        # Validate specified environments
        invalid_envs = set(args.environments) - set(all_environments)
        if invalid_envs:
            print_error(f"Invalid environments specified: {', '.join(invalid_envs)}")
            print_error(f"Available environments: {', '.join(all_environments)}")
            return 1
        environments_to_sync = args.environments
    else:
        environments_to_sync = all_environments

    # Determine action based on flags (handle backward compatibility)
    action = args.action
    if args.terraform_only:
        print_warning("--terraform-only is deprecated, use --action terraform")
        action = 'terraform'
    if args.no_terraform:
        print_warning("--no-terraform is deprecated, use --action ssm")
        action = 'ssm'

    print_info(f"Found cloud environments: {', '.join(all_environments)}")

    # For SSM action: only sync specified environments
    # For Terraform action: always process ALL environments
    if action in ['ssm', 'all']:
        environments_for_ssm = environments_to_sync
        print_info(f"Will push to SSM: {', '.join(environments_for_ssm)}")

    if action in ['terraform', 'all']:
        environments_for_terraform = all_environments  # Always ALL environments for Terraform
        if action == 'terraform':
            print_info(f"Will generate Terraform for ALL environments: {', '.join(environments_for_terraform)}")

    # Determine which environments to load
    environments_to_load = set()
    if action in ['ssm', 'all']:
        environments_to_load.update(environments_to_sync)
    if action in ['terraform', 'all']:
        environments_to_load.update(all_environments)

    # Load environment variables for each environment
    env_vars_by_env = {}
    aws_profile = args.aws_profile
    aws_region = args.aws_region

    for env in sorted(environments_to_load):
        print_header(f"Loading environment variables for: {env}")
        env_vars = load_environment_variables(env_dir, env)
        env_vars_by_env[env] = env_vars
        print_success(f"Total variables loaded: {len(env_vars)}")

        # Get AWS credentials from first environment if not specified
        if not aws_profile or not aws_region:
            profile, region = get_aws_credentials_from_env(env_vars)
            if not aws_profile:
                aws_profile = profile
            if not aws_region:
                aws_region = region

    if aws_profile:
        print_info(f"\nUsing AWS profile: {aws_profile}")
    if aws_region:
        print_info(f"Using AWS region: {aws_region}")

    # Push to SSM
    if action in ['ssm', 'all']:
        all_success = True
        for env in environments_for_ssm:
            env_vars = env_vars_by_env[env]
            success = push_to_ssm(
                env,
                env_vars,
                aws_profile,
                aws_region,
                dry_run=args.dry_run,
                use_env_prefix=not args.no_env_prefix
            )
            if not success:
                all_success = False

        if not all_success:
            print_error("\nSome parameters failed to push to SSM")
            return 1

    # Generate Terraform file (always for ALL environments)
    if action in ['terraform', 'all']:
        output_file = project_root / args.output_file
        success = generate_terraform_file(
            environments_for_terraform,
            env_vars_by_env,
            output_file,
            use_env_prefix=not args.no_env_prefix,
            dry_run=args.dry_run
        )
        if not success:
            print_error("\nFailed to generate Terraform configuration")
            return 1

    print_header("Sync completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

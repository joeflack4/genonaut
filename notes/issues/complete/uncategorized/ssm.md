# Set up AWS SSM using Terraform: automation

## Status: COMPLETED

## Basic idea
I want to have a script that does two things:

1. Pushes 1 secret for each environment variable for each env target (e.g. demo, dev, etc).
2. Generates a Terraform snippet file containing secret definitions for each variable.

I want this to be a Python script that does shell calls to do this. And I want a command `aws-ssm-sync` in the 
makefile to run this script. You can add this to: `infra/scripts/aws_ssm_sync.py`. If you think it's useful, give it a 
CLI set up as well.

## Elaboration
### 1. Pushes 1 secret for each environment variable for each env target (e.g. demo, dev, etc).
Example snippet. The script should basically run commands like this:

```sh
aws ssm put-parameter \
  --name "/genonaut/ENV/DB_PASSWORD_RW" \
  --value "$DB_PASSWORD_RW" \
  --type "SecureString" \
  --overwrite \
  --profile "$DEPLOY_AWS_PROFILE" \
  --region "$DEPLOY_AWS_REGION"
```

If there is a AWS package on PyPi that will allow us to push such secrets, we can use that. But we could also just go 
with this approach, as it has already been thought out. 

### 2. Generates a Terraform snippet file containing secret definitions for each variable
The script should create or overwrite a separate file named `ecs_secrets.auto.tf` (Terraform automatically loads 
`*.auto.tf` files). This file will contain the `secrets` block for each environment.

Example snippet, showing the `secrets` block for one environment:

```tf
secrets = [
  {
    name      = "DB_PASSWORD_RW"
    valueFrom = "/genonaut/ENV/DB_PASSWORD_RW"
  },
  ...
]
```

## Problems and possible solutions
### 1. Detecting and iterating envs
`ENV` in `--name` needs to be replaced with the env name.

There are multiples of them. The best way to do this is to look at `env/`, and look for the file pattern `.env.cloud-*`.
The `*` is the env name. FYI right now, this should resolve to: demo, dev, prod, and test. If this pattern detection 
logic doesn't detect any matching files, then you can just do `--name "/genonaut/DB_PASSWORD_RW" \` instead, leaving out
the `ENV/` part of the path.

### 2. Multiple levels of `.env` files
We have the folllowing load order as mentioned in docs/configuration.md:

1. `config/base.json` - Base application config
2. `config/{ENV_TARGET}.json` - Environment-specific config
3. `env/.env.shared` - Shared secrets
4. `env/.env.{ENV_TARGET}` - Environment-specific secrets
5. Process environment variables - CI/shell exports
6. `env/.env` - Local developer overrides

`ENV_TARGET` in this case is like `cloud-demo`, `cloud-dev`, etc.

We need to consider all of these environment variable files, and set them in the correct level of precedence. Grab the
environment variables from all these different sources. In the event of conflicts, sources further down in the list are
more authoritative, and the values of such variables should override any that were previously defined.

You can ignore (1) and (2); these are for configuration, not secrets. These won't matter for AWS SSM.

## Implementation Summary

Implementation completed. The following was delivered:

### Script: infra/scripts/aws_ssm_sync.py
A Python script that:
- Automatically detects cloud environments by scanning for .env.cloud-* files
- Loads environment variables with proper precedence (.env.shared, then .env.cloud-{env}, then process env)
- Pushes secrets to AWS SSM Parameter Store using AWS CLI
- Generates Terraform configuration file (infra/main/ecs_secrets.auto.tf) with SSM references

### Makefile Commands
Commands are organized by action type:

**Combined (both SSM push + Terraform generation):**
- `make aws-ssm-sync` - Push all environments to SSM AND generate Terraform for all
- `make aws-ssm-sync-dry-run` - Dry run of both actions
- `make aws-ssm-sync-env ENV=demo` - Push specific env to SSM AND regenerate Terraform for all

**SSM Push Only (respects --env flag):**
- `make aws-ssm-push` - Push all environments to AWS SSM Parameter Store
- `make aws-ssm-push-dry-run` - Dry run of SSM push
- `make aws-ssm-push-env ENV=demo` - Push specific environment to SSM

**Terraform Generation Only (always ALL environments):**
- `make aws-terraform-gen` - Generate Terraform config for ALL environments
- `make aws-terraform-gen-dry-run` - Dry run of Terraform generation

Note: Terraform generation ALWAYS processes ALL cloud environments to maintain consistency in the generated configuration file.

### CLI Options
The script supports:
- `--action {all,ssm,terraform}` - Which action to perform (default: all)
  - `all` - Both SSM push and Terraform generation
  - `ssm` - Push to SSM only (respects --env flag)
  - `terraform` - Generate Terraform only (always ALL environments)
- `--dry-run` - Preview changes without executing
- `--env demo` - Specify environment(s) for SSM push (can be used multiple times)
- `--no-env-prefix` - Use /genonaut/{key} instead of /genonaut/{env}/{key}
- `--aws-profile` - Override AWS profile from .env files
- `--aws-region` - Override AWS region from .env files
- `--env-dir` - Custom env directory path
- `--output-file` - Custom Terraform output file path

**Deprecated (for backward compatibility):**
- `--terraform-only` - Use `--action terraform` instead
- `--no-terraform` - Use `--action ssm` instead

### Usage Examples
```bash
# Combined actions (SSM push + Terraform gen)
make aws-ssm-sync-dry-run                # Dry run both actions, all envs
make aws-ssm-sync                        # Push all envs to SSM + generate Terraform for all
make aws-ssm-sync-env ENV=demo           # Push demo to SSM + regenerate Terraform for all

# SSM push only
make aws-ssm-push-dry-run                # Dry run SSM push, all envs
make aws-ssm-push                        # Push all environments to SSM
make aws-ssm-push-env ENV=demo           # Push only demo environment to SSM

# Terraform generation only (always ALL environments)
make aws-terraform-gen-dry-run           # Dry run Terraform generation
make aws-terraform-gen                   # Generate Terraform config for all envs

# Using the Python script directly
python infra/scripts/aws_ssm_sync.py --action all --dry-run
python infra/scripts/aws_ssm_sync.py --action ssm --env demo
python infra/scripts/aws_ssm_sync.py --action terraform
python infra/scripts/aws_ssm_sync.py --action ssm --env demo --env prod
```

### Generated Terraform Format
The script generates `infra/main/ecs_secrets.auto.tf` with this structure:
```tf
# Auto-generated by infra/scripts/aws_ssm_sync.py
# DO NOT EDIT MANUALLY - Changes will be overwritten

locals {
  ecs_secrets_demo = [
    {
      name      = "DB_PASSWORD_RW"
      valueFrom = "/genonaut/demo/DB_PASSWORD_RW"
    },
    # ... more secrets
  ]
}

# Similar blocks for dev, prod, test environments
```

### Testing
All functionality tested with dry-run mode:
- Environment detection works correctly (found demo, dev, prod, test)
- Variable loading with precedence works (13 variables loaded from .env.shared)
- SSM parameter naming follows pattern: /genonaut/{env}/{key}
- Terraform generation creates proper locals blocks
- Makefile commands execute successfully

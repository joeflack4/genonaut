# Deployment configs
## Intro
I want to change the way that deployments are configured. Right now, everything is set up in `env/.env`. It has multiple 
variables for running 3 variations of the backend: demo, dev, and test, all locally. But I want to make some major 
changes.

1. Set up configuration for cloud environments.
2. Change so that primary configuration for most variables lies inside 1 or more config.json, which can be overriden by 
1 or more .env files.

We also currently have a config.json at the root of the repo, which has several key vals. We will still need those, but 
those have nothing to do with deployment configurations. 

In other words, the goal is to separate **application configuration** from **deployment secrets**, simplify local 
overrides. JSON is for committed, non-sensitive values. `.env` holds sensitive or private overrides. FYI: we are also 
preparing for future Terraform + AWS integration, and splitting up config and env like this will help with that.

## Multi-environment setup
I want to support the following environments (format: LOCATION-TYPE).

Local
- `local-dev`
- `local-test`
- `local-demo`

Cloud
- `cloud-dev`
- `cloud-test`
- `cloud-demo`
- `cloud-prod`

Each of the above will have a corresponding config file and can optionally reference a dedicated .env file for overrides.

Context: Regarding "cloud", I haven't settled yet on my cloud architecture. I think I'll go with AWS, but I'm not sure yet what
the specific setup will look like. I don't think I'll know the URLs of everything until I have that set up. What's more,
I'll likely store things on S3 instead of the local file system, which will mean updates to the configuration, but also 
to the app. I think I'll do this later, and see if I can rely on the AWS web servers' file systems for storage for now.


## Configuration refactor
```
config/
  base.json
  local-dev.json
  local-test.json
  local-demo.json
  cloud-dev.json
  cloud-test.json
  cloud-demo.json
  cloud-prod.json
```

You can initialize `config/base.json` by creating it and using all of the key/vals inside `/config.json`. Then, all 
references in the repo to use this new path.

## env/ refactor
```
env/
  .env.shared
  .env.local-dev
  .env.local-test
  .env.local-demo
  .env.cloud-dev
  .env.cloud-test
  .env.cloud-demo
  .env.cloud-prod
  env.shared.example
  env.location-type.example
```

### Migrating variables: .env vs config: Which vars go where?
Refer to `notes/config-env-refactor-env-vars-migrate.csv file`. It has a `move_to_config` column. If True, then that variable 
should be present in a config file and not in an .env file. Otherwise, keep in the .env file.

### Where to put var? shared/base vs LOCATION-TYPE
You'll need to use your discretion, but it should be easy to tell. e.g. if the variable like ends in _DEV, _DEMO, or 
_TEST, you'll know where to put it.

I noticed that the current .env lacks a _DEV distinction for the following variables, but I want you to know that these 
variables are actually the ones that are currently being used for the "dev" instance, so they should be treated as such:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=genonaut
DATABASE_URL=postgresql://${DB_USER_ADMIN}:${DB_PASSWORD_ADMIN}@${DB_HOST}:${DB_PORT}/${DB_NAME}
```

Note that our current .env doesn't have anything that distinguishes from "local" vs "cloud". In practice right now, 
these are all "local". We have no cloud deployment yet. But I think probably the best thing to do is to still initialize
the cloud env and config files using the respective "local" ones as placeholders. E.g. for `CELERY_RESULT_BACKEND_DEMO`,
you can use that in both the local and cloud "demo" configs.

When you move such vars, like `CELERY_RESULT_BACKEND_DEMO`, you can remove the `_DEMO` from the end. It'll be in the 
"demo" config now, so there is no need to keep such suffixes on the vars. Basically, the variable names should be 
exactly the same across all o the LOCATION-TYPE files.  

### Maintaining comments
The `.env` file has useful comments. Please try to retain these comments above the appropriate variables in the new 
file(s).

It's possible that there may not actually be very many vars in the .env files, so a lot of comments will end up getting 
dropped simply in virtue of the variable no longer existing in the .env. If that's the case, that's ok. Only show 
comments for variables that still continue to exist in the .env files after this refactor. 

### example files
We currently have an `env.example`. I wanna keep it, but given that we have this new pattern, we should have 2 of them: 
```
env.shared.example
env.location-type.example
```

So please create those two files, and remove env.example after. Maintain comments here, tool. Update the docs to 
reference these two files.

## Load Order (lowest → highest precedence)
1. `config/base.json`
2. `config/{ENV_TARGET}.json` (more on `ENV_TARGET` will be discussed in the makefile section / elsewhere)
3. `env/.env.shared`
4. `env/.env.{ENV_TARGET}`
5. process env (CI, shell)
6. local `env/.env` (developer overrides, optional)

## Makefile Setup
Here’s a Makefile pattern that supports commands for each environment, e.g. `make backend-local-dev`.
- The `__run-using-env-file` rule sources both `.env.shared` and `.env.<ENV_TARGET>` automatically.
- Each environment gets its own Makefile target.
- `--config-path` is derived from `ENV_TARGET` as `config/<ENV_TARGET>.json`.
- Set workers e.g. via `make backend-local-dev workers=4`.

We have several `api*` makefile commands like `api-dev` and `api-production-sim`. Repurpose them to use this new setup.


```make
ENV_DIR := env
SHARED_ENV := $(ENV_DIR)/.env.shared

# Generic runner: sources env vars and runs the given Python command.
# (renamed to _run-api, always loads SHARED_ENV, accepts ENV_TARGET, optional WORKERS)
_run-api:
	@echo ">> ENV_TARGET=$(ENV_TARGET)"
	@set -a; \	[ -f $(SHARED_ENV) ] && . $(SHARED_ENV); \	set +a; \	ENV_FILE="$(ENV_DIR)/..env.$(ENV_TARGET)"; \	CONFIG_PATH="config/$(ENV_TARGET).json"; \	CMD="uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --reload --env-path $$ENV_FILE --config-path $$CONFIG_PATH"; \	if [ -n "$(workers)" ]; then CMD="$$CMD --workers $(workers)"; fi; \	echo ">> Running: $$CMD"; \	ENV_TARGET=$(ENV_TARGET) $$CMD

# Example per-environment targets
api-local-dev:
	@$(MAKE) _run-api ENV_TARGET=local-dev

api-local-test:
	@$(MAKE) _run-api ENV_TARGET=local-test

api-cloud-prod:
	@$(MAKE) _run-api ENV_TARGET=cloud-prod

# Example with explicit workers:
api-local-dev-4w:
	@$(MAKE) _run-api ENV_TARGET=local-dev workers=4
```

## Python setup

dotenv Loading with fallback. This example shows how to load env files dynamically inside Python using `python-dotenv`.

Take these snippets as inspiration. Adapt the existing Python code to use patterns in these snippets as you see necessary to 
fulfill our goals.

```python
# app/config_loader.py
import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

def load_env_for_runtime(env_file: str | None) -> None:
    """
    Load order (lowest → highest precedence):
      1. env/.env.shared               # always attempt to load if present
      2. --env-file (passed path)      # the per-environment env file
      3. env/.env                      # developer local overrides (optional)
      4. process environment           # highest precedence (already present)
    """
    shared = os.path.join("env", ".env.shared")
    local_default = os.path.join("env", ".env")

    # 1) shared (base, do NOT override anything already set)
    if os.path.exists(shared):
        load_dotenv(shared, override=False)

    # 2) explicit env file (override values from shared)
    if env_file and os.path.exists(env_file):
        load_dotenv(env_file, override=True)

    # 3) developer .env (allow opt-in overrides)
    if os.path.exists(local_default):
        load_dotenv(local_default, override=True)

def load_config_path(path: str) -> Dict[str, Any]:
    """
    Read the JSON config located at 'path' and return a Python dictionary.
    This function does not perform env interpolation; values are read as-is.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
```

Example entrypoint using argparse:

```python
# app/main.py
import argparse
from app.config_loader import load_env_for_runtime, load_config_path

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", dest="env_file", help="Path to the per-environment .env file", default=None)
    parser.add_argument("--config-path", dest="config_path", help="Path to the JSON config for this environment", required=True)
    return parser.parse_args()

def main():
    args = parse_args()
    load_env_for_runtime(args.env_file)
    cfg = load_config_path(args.config_path)
    print(f"Loaded config from {args.config_path}: keys={list(cfg.keys())}")
    # TODO: initialize app with cfg and environment

if __name__ == "__main__":
    main()
```

Ensure that the Python checks to see if the .env files loaded override anything in the config files. E.g. if the config 
file has a var like `db-name` and the env file has a var like `DB_NAME`, that would be considered a match.


## Docs
When all is finished, update the docs. Should go over all of this, the configs and envs, how one overrides the other, 
which things are env only, and how to create configs for multiple enviroments..

Some things to explain:
- Config load precedence
- Which vars belong in `.env`
- How `ENV_TARGET`
- How to extend configs for new environments

## High level instructions
Follow these high level steps:
1. Fully read this file (notes/config-env-refactor.md)
2. Create a mulit-phased list of tasks with markdown checkboxes: notes/config-env-refactor-tasks.md.
3. If anything is unclear, create: notes/config-env-refactor-questions-unanswered.md, and prompt me to answer them before 
continuing. If later on you ever encounter another stopping point and have a question, also append them to this file and
stop and ask me to answer.
4. Read: .claude/commands/interation.md, and follow those instructions on how to iterate and complete the tasks.
5. Finally, get started on the tasks! Work as independently as you can, completing as many phases as you can (all of 
them ideally) before prompting me, unless you hit a sticking point.

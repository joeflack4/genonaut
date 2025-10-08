# Configuration Refactor - Questions for User - Answered
## Question 1: Uvicorn CLI Arguments

**Context:** The spec document (notes/config-env-refactor.md) shows Makefile examples using:
```bash
uvicorn genonaut.api.main:app --env-path $$ENV_FILE --config-path $$CONFIG_PATH
```

**Issue:** Uvicorn does not have `--env-path` or `--config-path` flags built-in.

**Proposed Solutions:**
1. **Option A**: Pass these as environment variables (e.g., `ENV_FILE_PATH`, `CONFIG_FILE_PATH`) and read them in the app startup
2. **Option B**: Create a wrapper Python script that parses these args and calls uvicorn programmatically
3. **Option C**: Modify the approach to set `ENV_TARGET` as an environment variable, and the app derives the paths from that

**Question:** Which approach would you prefer? I'm leaning toward Option A or C as they're simpler.

### Answer
Short answer: go with Option B (wrapper CLI), but let it also accept ENV_TARGET (so you also get C’s ergonomics). That
gives you a clean --env-path/--config-path UX, keeps Makefiles simple, and avoids overloading uvicorn flags.

Here's an example for the cli.py. You might be able to use this exactly as-is, or you might need to repurpose:
```py
# genonaut/cli.py
import os
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
import uvicorn

app = typer.Typer(add_completion=False)

def _load_envs(explicit_env: Optional[str]):
    # Always try shared + default if present
    for p in ["env/.env.shared", "env/.env"]:
        if Path(p).is_file():
            load_dotenv(p, override=False)
    # Then load explicit file last so it wins
    if explicit_env:
        if not Path(explicit_env).is_file():
            raise FileNotFoundError(f"--env-path not found: {explicit_env}")
        load_dotenv(explicit_env, override=True)

def _derive_paths_from_target(env_target: Optional[str], env_path: Optional[str], config_path: Optional[str]):
    # Only fill in missing values
    if env_target and not env_path:
        candidate = f"env/.env.{env_target}"
        if Path(candidate).is_file():
            env_path = candidate
    if env_target and not config_path:
        # adjust if your config layout differs
        candidate = f"config/{env_target}.yaml"
        if Path(candidate).is_file():
            config_path = candidate
    return env_path, config_path

@app.command()
def run_api(
    host: str = "0.0.0.0",
    port: int = 8001,
    reload: bool = True,
    workers: Optional[int] = None,
    env_path: Optional[str] = typer.Option(None, help="Path to .env file to load"),
    config_path: Optional[str] = typer.Option(None, help="Path to app config file"),
    env_target: Optional[str] = typer.Option(None, help="Shortcut like 'dev/test/demo' to derive paths"),
):
    # Derive defaults from ENV_TARGET, then load envs
    env_path, config_path = _derive_paths_from_target(env_target, env_path, config_path)
    _load_envs(env_path)

    # Export config path for your app to read on startup
    if config_path:
        os.environ["APP_CONFIG_PATH"] = str(config_path)

    # Tip: your FastAPI app can read APP_CONFIG_PATH on startup
    uvicorn_kwargs = dict(host=host, port=port, reload=reload)
    if workers:
        uvicorn_kwargs["workers"] = workers

    uvicorn.run("genonaut.api.main:app", **uvicorn_kwargs)

if __name__ == "__main__":
    app()
```

The makefile function could then be updated: to run like this: 
```makefile
	python -m genonaut.cli run-api \
		--env-target $(ENV_TARGET) \
		--env-path $(ENV_PATH) \
		--config-path $(CONFIG_PATH) \
		--workers $(WORKERS)
```

## Question 2: JSON Config Merging Strategy

**Context:** We have `config/base.json` and environment-specific configs like `config/local-dev.json`.

**Question:** How should we merge these files?

**Options:**
a. **Shallow merge**: Just overwrite top-level keys from base with env-specific values
b. **Deep merge**: Recursively merge nested objects (e.g., if base has `{"db": {"host": "x"}}` and env-specific has `{"db": {"port": 5432}}`, result is `{"db": {"host": "x", "port": 5432}}`)

**Recommendation:** I suggest deep merge for maximum flexibility, but it's more complex to implement.

### Answer
Agreed We might as well do (b) now.

## Question 3: Config Key Naming Convention

**Context:** Config files will use JSON format, .env files use uppercase with underscores.

**Question:** What naming convention should we use for keys in JSON config files?

**Options:**
a. **snake_case**: `db_host`, `db_port` (matches Python naming)
b. **kebab-case**: `db-host`, `db-port` (common in JSON configs)
c. **camelCase**: `dbHost`, `dbPort` (JavaScript style)

**Recommendation:** I suggest `snake_case` to match Python conventions and make env var overrides more intuitive (DB_HOST overrides db_host).

### Answer
b. **kebab-case**

## Question 4: Env Var Override Matching

**Context:** The spec says .env vars should be able to override config vars (e.g., `DB_NAME` in .env overrides `db_name` in config).

**Question:** How should we match env var names to config keys?

**Current thinking:**
- Env var `DB_NAME` matches config key `db_name`
- Conversion: uppercase to lowercase, keep underscores
- Case-insensitive matching

**Is this correct, or do you want a different mapping strategy?**

### Answer
It actually says "(e.g., `DB_NAME` in .env overrides `db-name` in config)".

Let's use this strategy instead:
- Case insensitive matching
- Replace underscores with dashes

## Question 5: Cloud Config Initialization

**Context:** The spec says to initialize cloud configs using local configs as placeholders.

**Question:** Should all cloud configs (cloud-dev.json, cloud-test.json, cloud-demo.json, cloud-prod.json) be exact copies of their local counterparts initially?

For example:
- `config/cloud-dev.json` = copy of `config/local-dev.json`
- `config/cloud-test.json` = copy of `config/local-test.json`
- etc.

**Or should they have some placeholders/TODOs for values that will definitely change (like database URLs)?**

### Answer
Let's make them be exact copies for now.

## Question 6: DATABASE_URL Variable

**Context:** Currently, `DATABASE_URL` is constructed in .env like:
```
DATABASE_URL=postgresql://${DB_USER_ADMIN}:${DB_PASSWORD_ADMIN}@${DB_HOST}:${DB_PORT}/${DB_NAME}
```

This uses variable interpolation within the .env file.

**Question:** Should we:
- **Option A**: Keep this in .env files (but then it references vars that might be in config files)
- **Option B**: Construct DATABASE_URL programmatically in Python from individual components
- **Option C**: Put the template in config and only the password in .env

**Recommendation:** Option B seems cleanest - construct it in Python from the individual components.

### Answer
I agree with Option (b).

We also need to address 1 makefile command as well:
```makefile
init-test:
	@echo "Initializing test database..."
	@TEST_URL=$${DATABASE_URL_TEST:-$${DATABASE_URL}}; \
	GENONAUT_DB_ENVIRONMENT=test TEST=1 DATABASE_URL=$$TEST_URL DATABASE_URL_TEST=$$TEST_URL python -m genonaut.db.init
```

I think we'll need to update `genonaut.db.init` so that it follows a similar pattern: To get the env vars and config 
files from explicitly passed params, and resolve them. This will result in duplciative code, where we have a very 
similar CLI for 'init' as for the API... but this may be the best solution for now. 


## Question 7: Handling Current ENV Variables

**Context:** The current .env has variables like:
- `DB_HOST`, `DB_PORT`, `DB_NAME` (currently used for "dev" but not suffixed with _DEV)
- According to the spec, these are actually the dev instance variables

**Question:** In the new structure, should these go into:
a.`config/local-dev.json` (since they're non-sensitive and dev-specific)
b.OR keep them in `env/.env.shared` (since they could be shared defaults)

**My understanding from the spec:** They should go into `config/local-dev.json`. Is this correct?

### Answer
That's correct. Go with 'a'.

## Question 8: APP_ENV vs ENV_TARGET

**Context:**
- Current system uses `APP_ENV` environment variable (values: dev, demo, test)
- Spec introduces `ENV_TARGET` (values: local-dev, local-test, local-demo, cloud-dev, etc.)

**Question:** Should we:
- **Option A**: Replace `APP_ENV` entirely with `ENV_TARGET`
- **Option B**: Keep both (ENV_TARGET for file selection, APP_ENV derived from it)
- **Option C**: Keep APP_ENV as the main variable and derive file paths from it plus a separate DEPLOYMENT_LOCATION variable

**Recommendation:** Option A for simplicity, but this is a breaking change.

### Answer
This is difficult. I can see the advantages of (b). Let's go with (a) and hope it ends up working out. It's possible 
that we'll need to determine whether something is e.g. 'demo' by extracting it from the string 'local-demo' or 
'cloud-demo', but I think this can be done within Python code if that's the case.

Go with (a), but take care and resolve / fix any references of "APP_ENV" (lowercase or uppercase) in the entire 
codebase, including in Python files, documentation, etc.

## Question 9: Backward Compatibility

**Question:** Do you need backward compatibility with the old configuration system during a transition period, or can we do a complete cutover?

**Impact:**
- If we need compatibility, we'll need fallback logic to check old locations
- If not, we can do a clean implementation

### Answer
No backwards compatibility.

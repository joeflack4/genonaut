# AGENTS.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Genonaut is a project to implement recommender systems for generative AI that can perpetually produce content (text, 
image, video, audio) based on user preferences.

## How to familiarize yourself with the project
- Read the `README.md` file in the root of the repository. Follow any links in that file, or any other files it links 
to, e.g. [full dev docs](docs/developer.md)), and read those files as well.

## Code / architecture style
- Whenever possible, functions / methods should be pure functions.
- Use types often, especially for all function / method parameters.

## Standard Operating Procedures
### Common steps to do whenever creating/updating any task / feature
1. Add end-to-end and/or integration tests, where applicable.
2. Add unit tests for any functions/methods.
3. Add documentation: Module level docstrings, class level docstrings, function level docstrings, and method / function
level docstrings. Function / method docstrings should include information about parameters and returns, and a 
description. 
4. Periodic code commenting. For example, for a function that has several distinct steps, where each step involves a 
block of code (e.g. a `for` loop with several operations), put at least 1 comment above eaach block, explaining what it 
does.
5. If any new Python requirements / packages are added to the project, include them (unversioned) in the 
`requirements-unlocked.txt` file.
6. If the new feature has a CLI, document it in a "Features" section in the `README.md`. Include a table showing the 
args, their description, defaults, data types, etc.
7. Consider otherwise any other documentation that might need to be added or updated in `README.md` after adding a 
feature, and either do those updates or ask for input.
8. Ensure that the whole test suite passes before completion of a feature or major task.
9. If there is a command involved that needs to work, but for which it does not make sense to have a test (like if you 
are asked to fix a one-off script or command), then make sure to run the command to ensure that it works, unless asked 
not to or otherwise if you think it is inadvisable to do so.

### When changing DB schema
Caution!: DO NOT edit existing files Alembic version files!: `genonaut/db/migrations/versions/`. Treat them as immutable
history. Always generate a new revision with `alembic revision -m "..."` and put upgrade/downgrade code there. If you 
need to change the schema, add it in a new migration file rather than modifying or deleting old ones.

Read this too: [DB migrations docs](./docs/db_migrations.md), particularly the "SOP: Changing database schema" section.

### Service Management
If at any point you need a service to be running (e.g. database, backend web API, frontend, or other services), you should:

1. **Start required services**: Go ahead and try to start the process as a background process using appropriate commands (e.g., `make start-db`, `npm run dev`, `python -m uvicorn app:app`, etc.).

2. **Restart existing services**: If you need to restart a service that is already running, try to stop and start the process again. Use commands like:
   - `pkill -f <process_name>` or `killall <service>` to stop
   - Then start the service again with the appropriate command
   
3. **Check service status**: Before starting, you can check if a service is already running using commands like:
   - `ps aux | grep <service_name>`
   - `lsof -i :<port_number>` for services running on specific ports
   
4. **Use project-specific commands**: Look for Makefile targets, npm scripts, or other project-specific commands for service management (e.g., `make start-services`, `docker-compose up -d`, etc.).

Always prioritize using project-specific service management commands when available, as they are likely configured with the correct parameters and dependencies.

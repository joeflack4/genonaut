# Tests

## Worktree-Specific Testing

**IMPORTANT**: If you are working in a worktree other than the main development worktree (`/Users/joeflack4/projects/genonaut`), you must use the worktree-specific infrastructure to avoid port conflicts.

See [docs/testing-test-worktree.md](../docs/testing-test-worktree.md) for complete instructions.

Quick reference for worktree 2:
- Starting services: `make api-test-wt2` and `make celery-test-wt2` (and also `make frontend-dev-wt2` if needed)
- Stopping/restarting services: `make api-test-wt2-stop` / `make api-test-wt2-restart` (NOT generic pkill)
- Running tests: `make test-wt2`, `make test-api-wt2`, `make frontend-test-e2e-wt2`

**IMPORTANT**: When restarting API servers, always use environment-specific commands like `make api-test-wt2-restart` instead of `pkill -f "run-api"` to avoid killing servers in other worktrees. See [docs/testing.md](../docs/testing.md#api-server-management-for-testing) for details.

---

When working on tests, you need to read the following documents as a prerequisite:
- `docs/testing.md`
- `docs/testing-test-worktree.md` (if in worktree 2)

# Do and test
Do the work you have been given, but if you have a task document, make sure the following tasks are listed towards the
end of that document. These should be part of acceptance criteria / final phase / testing phase.

**For main worktree:**
- [ ] 1. Ensure tests pass: `make test`
- [ ] 2. Ensure tests pass: `make frontend-test-unit`
- [ ] 3. Ensure tests pass: `make frontend-test-e2e`
- [ ] 4. Ensure tests pass: `make test-long-running`

**For worktree 2 (`/genonaut-wt2`):**
- [ ] 1. Ensure tests pass: `make test-wt2`
- [ ] 2. Ensure tests pass: `make frontend-test-unit-wt2`
- [ ] 3. Ensure tests pass: `make frontend-test-e2e-wt2`
- [ ] 4. Ensure tests pass: `make test-long-running-wt2`

## Additional info about alternative worktrees and tests
**IMPORTANT**: If you are working in a worktree other than the main development worktree (`/Users/joeflack4/projects/genonaut`), you must use the worktree-specific infrastructure to avoid port conflicts.

See [docs/testing-test-worktree.md](../../docs/testing-test-worktree.md) for complete instructions.

Quick reference for worktree 2:
- Starting services: `make api-test-wt2` and `make celery-test-wt2` (and also `make frontend-dev-wt2` if needed)
- Running tests: `make test-wt2`, `make test-api-wt2`, `make frontend-test-e2e-wt2`

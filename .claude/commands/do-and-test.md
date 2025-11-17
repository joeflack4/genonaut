---
description: Add test tasks to document, and execute work. [Args - OPTIONAL_DOCS ]
---

# Do and test
Do the work you have been given, but if you have a task document, make sure the following tasks are listed towards the
end of that document. These should be part of acceptance criteria / final phase / testing phase.

Task documents: $1

Note: if the above just shows () and doesn't show any documents, then please consult the document(s) containing markdown 
checkbox task(s) that we have been working or that have been called to your attention on in this session / conversation.

## 1. Add the following text to the task document
```md
## Run full test suites
**If you are on the main worktree:**
- [ ] 1. Ensure tests pass: `make test`
- [ ] 2. Ensure tests pass: `make frontend-test-unit`
- [ ] 3. Ensure tests pass: `make frontend-test-e2e`
- [ ] 4. Ensure tests pass: `make test-long-running`
- [ ] 5. Ensure tests pass: `make test-performance`

**If on worktree 2 (`/genonaut-wt2`):**
- [ ] 1. Ensure tests pass: `make test-wt2`
- [ ] 2. Ensure tests pass: `make frontend-test-unit-wt2`
- [ ] 3. Ensure tests pass: `make frontend-test-e2e-wt2`
- [ ] 4. Ensure tests pass: `make test-long-running-wt2`
- [ ] 5. Ensure tests pass: `make test-performance`
```

## Additional info 
### About alternative worktrees and tests
**IMPORTANT**: If you are working in a worktree other than the main development worktree (
`/Users/joeflack4/projects/genonaut`), you must use the worktree-specific infrastructure to avoid port conflicts.

See [docs/testing-test-worktree.md](../../docs/testing-test-worktree.md) for complete instructions.

Quick reference for worktree 2:
- Starting services: `make api-test-wt2` and `make celery-test-wt2` (and also `make frontend-dev-wt2` if needed)
- Running tests: `make test-wt2`, `make test-api-wt2`, `make frontend-test-e2e-wt2`

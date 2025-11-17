---
description: Think up and create new playwright tests at the start of a new session. [Args - None ]
---

# New playwright tests
I'd like to ensure that we have good frontend test coverage. Perhaps we do, but I don't know if we've covered all the 
bases.

- [ ] Create new doc: C`notes/new-tests-YYYY-MM-DD.md`, where `YYYY-MM-DD` is today's 
date. The major sections of this should be "Very high priority", "High priority", "Medium priority", and "Low priority".
- [ ] Iterate through each page of the frontend
  - [ ] For each page, consider all of the UI elements that, when engaged with by the user (e.g. click), result in some
  state change. For all such element interactions, ensure that there is a playwright test that covers the interaction
  and tests for the expected outcome(s). If there is a test that already exists that covers this--great, no need to add
  a new one. But if not, then create a new test.
- [ ] If you have any questions, write them in a new section of this document for the user to respond to later. Don't
  wait for a response. Just keep working until tasks are complete.
- [ ] If you end up needing a complex solution to cover one or more tests, you can mak ea new section here with its own
  set of checkboxes.
- [ ] Ensure all tests pass successfully before marking this task complete.
- [ ] Check off any checkboxes after the task has been completed. Your work will be considered complete when all
  checkboxes in the document are marked off. Keep working until then.


## Task Completion Summary
```
### Frontend Pages Analyzed:
TODO: Put one bullet for each page here

### New Test Files Created:
TODO: 1 bullet for each test file created (test name & a description)

### Additional notes
TODO: Any additional notes, if applicable
```

## Additional info
### Worktree-Specific Testing

**IMPORTANT**: If you are working in a worktree other than the main development worktree (
`/Users/joeflack4/projects/genonaut`), you must use the worktree-specific infrastructure to avoid port conflicts.

See [docs/testing-test-worktree.md](../../docs/testing-test-worktree.md) for complete instructions.

Quick reference for worktree 2:
- Starting services: `make api-test-wt2` and `make celery-test-wt2` (and also `make frontend-dev-wt2` if needed)
- Running tests: `make test-wt2`, `make test-api-wt2`, `make frontend-test-e2e-wt2`

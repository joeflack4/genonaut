---
description: Think up and create new tests at the start of a new session. [Args - None ]
---

# Create new batch of tests
## Overview
I want to make sure we have good test coverage. Please do an analysis. Iterate through every frontend page, and on each 
page, look at each widget, and think about some workflows that are good to perhaps test that involve manipulating 
several different widgets in order, and checking that the results are what you would expect. Similarly, look through all
the API endpoints, and make sure that the various query options they provide are tested. Think about which kinds of 
tests you could add for these: unit, end-to-end, integration, performance, etc. Be sure to look at the existing tests 
for the respective page / endpoint to make sure that there is not already a test that already exists; don't want to 
write the same test twice.

Start by ideating like this, and creating a document called `notes/new-tests-YYYY-MM-DD.md`, where `YYYY-MM-DD` is today's 
date. The major sections of this should be "Very high priority", "High priority", "Medium priority", and "Low priority".
Then, in each of those sections, add subsections "Backend" and "Frontend". then, in each of those, add further 
subsections, one for each kind of test, "Unit", "E2E", etc.

Then in each of those sections, add checkboxes lines, 1 for each test; a markdown checkbox, followed by the name of the
test to make, and a description of the test. Feel free to add as much detail as you want.

Then, once that is all finished, you'll probably want to /compact your memory. And then you can get started. Start with 
the high priority tests, and then move on, subsection by subsection, to the high, then medium. You can do all of this in
one shot without coming to ask me anything. Don't touch the "low" ones yet. Just create the tasks and I'll decide if I 
want you to do those or not.

When you finish a subsection of tests, be sure to check them off.

Go ahead, get started! Thanks in advance.

## Additional info
### Worktree-Specific Testing

**IMPORTANT**: If you are working in a worktree other than the main development worktree (
`/Users/joeflack4/projects/genonaut`), you must use the worktree-specific infrastructure to avoid port conflicts.

See [docs/testing-test-worktree.md](../../docs/testing-test-worktree.md) for complete instructions.

Quick reference for worktree 2:
- Starting services: `make api-test-wt2` and `make celery-test-wt2` (and also `make frontend-dev-wt2` if needed)
- Running tests: `make test-wt2`, `make test-api-wt2`, `make frontend-test-e2e-wt2`

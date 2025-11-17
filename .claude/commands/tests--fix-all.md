# Tests - Fix all
## Overview
It is assumed that there are currently broken tests in the repo. We have been doing development quickly without ensuring
that tests are passing with every commit. So now, we want to see what's broken and fix in batch.

## Test suites
Below is a list of different makefile commands that we use to run different test suites. They are sorted by the order in
which we want you to work on them:

1. `test`: These are backend tests; mostly unit and integration.
2. `test-frontend-unit`
3. `test-long-running`: These are backend tests that take longer than normal to run.
4. `test-frontend-e2e`
5. `test-performance`: These are backend tests that test performance.


-------------

## What to do for each test suite
Iteratively, for each of the "test suites", in the order shown above, do the following:
- 1. Run the tests suite.
- 2. Create a `notes/test-fails-N-NAME.md`, where `NAME` is the makefile command name, and `N` is the order in which it 
  appears in the ordered list in the "## Test suites" section above.  
  - 2.1. In it, create a section header for the current test suite.
  - 2.2. Within the test suite section, create subsections, one per category of failures. What we mean by "category" is 
    that you will likely find that you will get clusters of tests that are failing for the same kind of reason(s). The 
    section header for the category should contain the category name, and the estimated level of difficulty to fix those 
    tests, e.g. `### My failing test category (high)`. Estimted levels of difficulty should be one of: (low), (
    medium low), (medium), (medium high), (high), and (very high).
  - 2.3. Within each category, list all of the relevant failing tests. Each test should appear on a separate line, 
    having its own markdown checkbox and displaying the test name, e.g. `- [ ] my_failing_test`. By the end of this 
    process, 100% of the failing tests should appear somewhere in the document.
- 3. Iterate over categories, in the order that you feel is best.
  - 3.1. See if you can fix all the tests in the category. When you are done working on a batch, check off (`- [x]`) all
    fixed tests. The fix process should involve applying the fixes, and then re-running those specific tests to ensure 
    that they are now passing.
  - 3.2. For any that you think should not be fixed and should instead be skipped for good reason, add an annotation at
    the end of the line for the given test, e.g. (@recommend-skip: REASON).
  - 3.3. If you think a test should be deleted, e.g. if it is obsolete, add an annotation (@recommend-delete: REASON).
  - 3.4. If you can't fix it because you need our feedback, add (@need-feedback: EXPLANATION).
- 4. When you have finished all category sections for the test suite (all have been fixed, skipped, or deleted per 
  protocol), re-run the test suite and ensure everything is passing. If not, continue with the relevant parts of steps 
  (2) and (3).
- 5. Periodically, you will need to prompt the user. Do this as infrequently as possible; you should work as 
  independently as possible. However, when you prompt the user with your report and/or questions, you should also 
  remind them of their role: (i) they should examine `notes/test-fails-N-NAME.md` to see what you have completed, and to
  see your '@recommend*' or '@need-feedback*' annotations. Remidn the user that if we choose to skip any tests, we 
  should follow the SOP outlined in `.claude/commands/tests--skip-and-file.md`.

By the end of this process, after fixing tests and working with the user to decide any tests to explicitly skip or 
delete, all of the test suites should have a 100% pass rate.

## Additional info
### Worktree-Specific Testing

**IMPORTANT**: If you are working in a worktree other than the main development worktree (
`/Users/joeflack4/projects/genonaut`), you must use the worktree-specific infrastructure to avoid port conflicts.

See [docs/testing-test-worktree.md](../../docs/testing-test-worktree.md) for complete instructions.

Quick reference for worktree 2:
- Starting services: `make api-test-wt2` and `make celery-test-wt2` (and also `make frontend-dev-wt2` if needed)
- Running tests: `make test-wt2`, `make frontend-test-unit-wt2`, `make test-long-running-wt2`, 
`make frontend-test-e2e-wt2`, `make test-performance-wt2`

## Your high level tasks: How to proceed
1. Read and understand this SOP.
2. Read: `docs/testing.md`
3. Work through the "What to do for each test suite" section, following its iterative process.

---
description:  [Args - REQUIRED_PROMPT, OPTIONAL_DOC_NAMES ]
---

# Tests - skip and file
Sometimes, we have persistent test failures and they end up being more trouble than they are worth. When this happens, 
you'll be asked to execute this procedure.

## Background information
### User prompt
$1

### Documents
The test tasks being referred to exist in the following document(s): ($2)

Note: if the above just shows () and doesn't show any documents, then please consult the document(s) containing markdown 
checkbox task(s) that we have been working on in this session / conversation.

## Tasks
1. Skip the test(s) - Apply the appropriate method to skip them.
2. Code commenting - Thoroughly apply code commenting in the docstring for the test, explaining why the test was 
skipped. This should also include information about what was tried, difficulties encountered, and possible future routes
of inquiry, troubleshooting, and possible solutions, if you are aware of any.
3. Referencing - Add entries for the skipped tests in: `notes/issues/groupings/tests/tests.md`. There is a "paused 
tests" section. You can basically add all the same information here that you added in the "code commenting" step above.
4. Offer alternative solutions, if possible - If these tests were skipped because they were persistently difficult to 
resolve, think and see if you can identify any alternative ways to test what the test is trying to test. Then, if there 
isn't such a test that already exists, propose to the user these potential alternative(s). Also, see if any of the 
following issues documenting alternative test patterns would be helpful for any of these skipped tests, and if so, raise
them to attention: (i) `notes/issues/by_priority/low/msw-for-e2e-tests.md`


## Things not to do unless asked
1. Do not add an entry for the skipped test in `notes/issues/groupings/tests/tests-skipped-troublesome-patterns.md` 
unless the user asks you.
2. Do not create individual markdown issue task documents for each of the failures, or a group of related failures, in 
`notes/issues/by_priority`, `notes/issues/groupings/tests/paused`, or anywhere else.

## Contingencies
### If the user asks to mark the test / pattern as a 'skipped because troublesome pattern'
You may be asked something that sounds like this. If you're not sure, ask to clarify. 

**Background info**
The idea here is that there are 2 kinds of tests that we deliberately pause and skip: (1) the kind that we think are 
more worth tackling in the future, and (2) the kind that (have probably come up before and) have proven persistently 
difficult to solve, and that have shown us patterns that appear to be difficult to test and have been a huge time sink, 
more than worthwhile, to try and resolve.

**What to do**
We want to try to avoid being sucked into such time sinks in the future, so what we do in these cases is we add 
that test or set of tests that have this pattern to `notes/issues/groupings/tests/tests-skipped-troublesome-patterns.md`.
Then, we add a section to the "E2E Test Patterns to Avoid" section of `docs/testing.md` (assuming these are indeed 
frontend E2E tests), explaining what the pattern is, and if possible, why it might have been difficult to resolve. 

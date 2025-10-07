## Redis and Celery
I recently installed Redis. It is up and running on port 6379. Now we need to add celery to the app. The primary focus 
will be to set it up and hook it up to the Image Generation routes / page.   

Start by reading the spec for the new work in: `notes/celery.md`.

Then, read what's been completed, and what remains to be done in: `notes/celery-tasks.md`.

If you come up with questions for me to answer, add them to the "unanswered" section of `notes/celery-questions.md`. However, try not to let these 
hold up your progress. Keep working to do as much as possible, and when reporting to me, prompt me to answer the 
questions in that document.

Read this as well:
- iteration.md: Tells you about how to go about making changes in phases.

Then, proceed with the actual work. Do these tasks, and get back to me.
- 1. Phase 5: ComfyUI client: It's ready. ComfyUI us running on port 8188. So we should be able to fully implement this now. If you run into difficulties, add questions to notes/celery-questions.md and prompt me to answer.
- 2. Finish section: "3.2 Define Celery Tasks": Some of them are not done yet because "(placeholder - see Phase 5)". So once Phase 5 is done, do these.
- 3. Phase 8: Testing: Do these tests. We'll want unit and e2e / integration tests for both the frontend and backend. Come back to me when the tests are passing. If there are tests that are erroring or failing and you feel like we shouldn't complete these now, set them to being skipped. Then create notes/celery-tasks-tests.md, and add checkbox lists. But them into different subsections based on which common category these failures fall into. And then let me know which of the tests can be unskipped and completed once particular phases of notes/celery-tasks.md are completed, and which ones are being skipped because of some blocker that I need to fix, versus tests that are being skipped for some future work not yet covered in celery-tasks.md. Special Note: test database. I thought that the postgres database was ephemeral, created and destroyed during tests. Maybe that's only so for the sqlite db. But I couldn't migrate the test db. I got an error. See if you can migrate the test DB. if you have too much trouble, we should delete that DB and make a new one.

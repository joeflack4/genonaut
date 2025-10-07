## Redis and Celery
I recently installed Redis. It is up and running on port 6379. Now we need to add celery to the app. The primary focus 
will be to set it up and hook it up to the Image Generation routes / page.   

Start by reading the spec for the new work in `notes/celery.md`.

Think about the app, and if the spec is sufficient enouhg to describe what needs to be done. If you think it is lacking 
details, you should feel free to update it.  

Based on that, create a long, multi-phased list of tasks in: `notes/celery-tasks.md.`

If you come up with questions for me to answer, add them to `notes/celery-questions.md`. However, try not to let these 
hold up your progress. Keep working to do as much as possible, and when reporting to me, prompt me to answer the 
questions in that document.

After you have created the tasks, then read these documents to get up-to-spee don the workflows you should follow:
- iteration.md: Tells you about how to go about
- mirations.md

Then, go ahead and get started! Complete as much as possible before reporting back to me.

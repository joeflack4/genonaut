# Iterating through sectioned checklists of tasks 
When working on a large set of tasks, it may sometimes be difficult to complete everything in one pass. It may be that 
there are some things which take a lot of time and effort, and might be better being skipped until later. And in some 
cases, it may be that the agent AI is blocked by something that only the user dev must do, such as set up some 
infrastructure.

When doing your work using a document to guide your tasks in steps and phases, go through sections 1-by-1, continuously.
And there are a very special set of tasks that you must follow every time you complete a minor section ("minor" meaning 
.1 in e.g. 5.1 Project Board Integration):

1. Ensure all tests are passing or skipped. Emphasis should be on passing. But if they are failing and you can't get 
them passing now because you need me to do something, or because of a complex setup, and you feel they are not truly 
necessary now, then skip them, and add as much information as you can about them in a document 
`notes/DOC_NAME-skipped-tests.md`, where `DOC_NAME` is the name of the document containing the checklist of tasks that 
you are currently working on. 
2. For the checkboxes in this minor section, check off all the ones completed. If there are any that you can't complete
now, put an annotation at the end of the sentence on the checkbox, like: `@skipped-until-TAG`, where `TAG` is an alias 
for a broader description of what is being held up.
3. Explain tags: There is or should be a "Tags" section somewhere in the document. If there are any `@skipped-until-TAG`
annotations, explain what the tags mean, in `- TAG: DESCRIPTION` format.
4. If you ran into anything unclear and need questions asked, you should update some markdown with these questions and 
prompt me to answer them when giving me my report after you are done with your batch of work. You can (a) add a 
"Questions" section somewhere in the document that lists the tasks that you are working on, or (b) you can use a 
document specifically for questions for me. E.g. let's say you have a setup where the spec document describing the work 
to be done is called `db-updates.md`, then usually it will come with a tasks document called `db-updates-tasks.md`, and 
you could put your questions in `db-updates-questions.md`.  When writing a question, make note of which specific tasks 
and subsections are  relevant to the question. You can refer to them like "task 3 in subsection (5.1)".
5. If anything needs my attention--if I am the hold up--put `@dev` on the checkbox or other spot in the markdown to call
my attention to it. 
6. Ensure that the associated `README.md` is updated with anything relevant based on these updates, if applicable.

So, once all the work in a minor section is completed or skipped for good cause, follow these 6 steps to close that 
minor subsection off, and then you can move on to the next section.

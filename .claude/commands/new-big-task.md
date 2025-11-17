---
description: Create a spec doc, do work, then test. [Args - OPTIONAL_SPEC_DOC_NAME, OPTIONAL_FILES_TO_READ, OPTIONAL_PROMPT ] [ Prereqs - If no OPTIONAL_SPEC_DOC_NAME already exists, first prommpt Claude to describe the task before using this command, or provide "OPTIONAL_PROMPT", in quotations, after providing the first 2 args. ]  
---

# SOP - New big task
$3

## What this SOP is
Describes how to proceed with carrying out a large task.

## When to follow this SOP
Please follow this SOP (standard operating procedure) when asked to, or when you determine that you have a big task (
something that has many steps, will take a while to complete, or is high effort).

## Steps
### 1. You are prompted
This will have already happened. The user has assigned you a new big task and asked you to read and follow this document.

### 2. Reading
### Spec document
Document name: ($1)

If the above shows an actual document name and not just empty parens (), read this as part of your prerequisite reading.
You will be updating this document. But instead if this is empty parens (), you will be creating a new spec document, 
and you can name it whatever you like. 

When to do this reading:
- Read this first after you finish reading this current "SOP - New big task" docuemnt, before you do any other reading.

#### Static SOPs
Files to read: `notes/routines/iteration.md`

When to do this reading:
- If possible, read this after creating or updating the spec document, and just before you start your work, so it is 
fresh in your mind.

#### More prerequisite reading
Files to read: ($2)

When to do this reading:
- Read this / these before creating or updating your spec document, after reading that spec document if it already 
exists.

Note: If the above just shows empty parens (), ignore; there is no optional prerequisite reading.

### 3. Planning
Create or update spec `.md` document in `notes/`, and in it, write:
1. A detailed description of the task(s) at hand.
2. A multi-phase list of checkbox tasks. Most large multi-step tasks will likely merit adding one or more of various 
types of tests: (frontend | backend) x (unit | integration / e2e). Large tasks will often include documentation updates 
(maybe a small bit in the `README.md`, but usually just in `docs/`). You should lean towards good documentation and test 
coverage for big tasks.
3. Steps in the final phases for manual QC: Do this if you did any frontend work. Use the playwright MCP to load a 
browser and test the features that you added in the various phases. Make sure that each feature works as you would 
expect.
4. Final testing: Steps in the final phases for final round of testing. See: `.claude/commands/do-and-test.md`
5. Questions for user: If you ran into anything unclear and need questions asked, you should update some markdown with 
these questions and prompt me to answer them when giving me my report after you are done with your batch of work. You 
can (a) add a "Questions" section somewhere in the document.

### 4. Execution
When you're ready to start working on the tasks, follow the SOP outlined in: `notes/routines/iteration.md`

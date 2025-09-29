# Markdown Manager
I want you to make a new Python-based program in libs/md_manager. This will later become its own separate product with 
its own life cycle, and will likely be pip installed here, and/or used as a git submodule.

The goal of the program will be to do complex management and analysis of sets of related markdown files. For example, a 
use case will be to work with all of our files in the notes/ dir.

The code for this will be written in libs/md_manager/md_manager. The tests will be in libs/md_manager/test/. Use TDD 
while developing.

The program should have its own set of files in the root libs/md_manager/, such as a README.md with documentation, a 
.gitignore, an AGENTS.md, a requriements-unlocked.txt for unversioned python files, and a requirements.txt for 
versioned ones. It should have its own virtual environment in an env/ dir. You'll want to use `click` as the CLI lib.

## How to's
### Marking tasks completed
If a section has checkboxes, then mark it checked when done. If a full subsection of "Open tasks" has been completed, 
then move it to the corresopnding `*-tasks-done.md`.

In this case, that is md-manager-tasks-done.md.

## Completed tasks
If needed, see [./md-manager-tasks-done.md](md-manager-tasks-done.md)

## Finally @dev
When agent is done with this document, compmile all @skipped-until-TAG and the associated TAG definitions, and put them 
somewhere, either in a checklist in this issue, or in a new issue.

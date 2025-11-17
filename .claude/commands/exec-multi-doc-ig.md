---
description: Check off completed work in documents, and show remaining work. [Args - IMPLEMENTATION_GUIDE_DIR ]
---

You will be executing on a large amount of work described in several files. These files together comprise an 
implementation guide. The directory contaning them is: $1

Tasks are represented by markdown checkboxes `- [ ]` and `- [x]`.

You'll start by reading `1-main.md`. This document contains the high level, outer loop of the work. Tasks here 
are a higher level summary representation of more granular tasks defined in the "phase documents" that follow. Each 
phase document is  numbered in order, like `2-TASK-NAME.md`, etc. After reading the `1-main.md`, you'll start on the 
second document and complete that in full before moving onto the third document, and so on.

Within the document are sections, which may or may not have subsections, e.g.:

```md
## 2. SECTION

### 2.1 SUBSECTION
- [ ] Create FILE_NAME
  - [ ] SUBTASK
...
```

Complete evecrything in order.

When you complete a subsection or section, check off all of the tasks that you completed. If you didn't complete any due
to some difficulty, or feedback needed, you must prompt the user. 

When you complete these tasks, make sure not to mark off a higher level task unless all of its lower level tasks have 
first been completed and checked off.

Wrong:
```md
- [x] Implement `make install-chat`:
    - [ ] Install required packages (fastapi, uvicorn, httpx, pydantic-settings, pinecone-client, etc.)
```

Correct:
```md
- [x] Implement `make install-chat`:
    - [x] Install required packages (fastapi, uvicorn, httpx, pydantic-settings, pinecone-client, etc.)
```

One you complete one of the phase documents, go back to `1-main.md`, and check off the apporpriate summary tasks as 
applicable, if the document you completed fully takes care of the task. If it looks like there is still more work to do 
for the given phase document, let the user know.

Work continuously on a given phase document, and only stop if you truly need help or feedback, or are running out of 
context. Otherwise, just prompt the user when a phase is complete. There's no need otherwise to prompt the user between 
sections in a phase document.  

That's it!

Your high level tasks now:
- [ ] 1. Read `1-main.md`
- [ ] 2. Begin impleemntation by reading the 2nd phase document and executing its tasks. 

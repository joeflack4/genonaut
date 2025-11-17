---
description: Defer subtasks (e.g. tests, security, etc), checking off and creating linked issue documents for later. [Args - REQUIRED_SUBTASK_TYPE OPTIONAL_DOC_NAME ]
---

You have been working on a feature: ($2) 

Note: If the above doc name is just empty parens (), refer instead to the document that you have been working on during
this session / conversation.

We have decided to defer one or more $1 updates for later. Examine the document that you have been working on to 
implement the feature / update. Does it have any unchecked boxes representing $1 updates to create?

Then, also think if there are any other $1 updates which would be very useful to have for this feature / update, but are 
not otherwise covered by the $1 updates that have been completed thus far (as shown by checked-off boxes in this 
document), nor explicitly planned yet (as shown by unchecked boxes in this document)

Then, for this set of unfinished $1 updates ((i) unchecked boxes, (ii) new ones you just came up with), add a new file 
`FEATURE-NAME.md` to `notes/issues/groupings/$1/`, where you add markdown checkboxes for all these $1 updates to one day 
be added, as well as as much detail as you think is useful about these $1 updates. Finally, add a link to this file in 
`notes/issues/groupings/tests/$1.md`.

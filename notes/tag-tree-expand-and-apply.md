ok great. however, when I click the little arrow thing next to each node in the tree to expand or collapse, I can see it
visually starting to expand, but then very quickly, it brings me to the "Content Browser" page. And then when I return 
back to the "Tag Hierarchy" page, it does not have the expanded state either; everything is fully collapsed again / 
still. Maybe that's because even though I saw it start to visually change, maybe it didn't complete the animation and 
that is the problem. I'm not sure. 

1. But start with fixing the issue where it is bringing me to that page when I expand. 

2. Let's change it so that clicking on items on the tree does not bring you to the "Content Browser" page. Instead, let's 
change it so that if the state of the tree becomes "dirty" (the user changes its state it from when it was last saved / 
applied, by clicking on a tag, toggling it from being selected or de-selected), a button that is otherwise hidden will 
appear, with the label "Apply & query content". And it will only apply the filter to the content browsing and jump you 
to the content browser only after the user clicks that. Then, when the query successfully completes, that button will 
become hidden again.

Let me know if you have any questions.

Think. Create a list of checkbox tasks here for you to complete, including new tests (mainly playwright) for these 
changes. Then, execute on that checklist.
å
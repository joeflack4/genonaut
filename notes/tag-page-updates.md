# Tag page updates
Some tasks for you on the 'tags' page (e.g.  http://localhost:5173/tags/TAG)

## 1. Title
change from "TAG_NAME" to: "Tag: TAG_NAME"

## 2. Button at the bottom
Change to take up only the width required to render the text, and keep it centered.

## 3. Your rating (-1)
Initially on page load, it correctly says "No rating" if the user has not rated the tag. If you hover over / focus on 
the stars, it will display the correct number for where the mouse cursor is located. However, if you then move your 
mouse away from the stars (out of focus), it will display "-1.0", which is not valid. It should go back to saying "No 
rating" if you have not rated it.
## 4. Tag cardinality
Show how many gens are associated with the tag somewhere on the page. This info is in the tag_cardinality_stats table. 
It should show "Auto-generated gens" ('auto' in content_source) and "Manually-generated gens" ('regular').
## 5. Selected tag persistence
If the user currently has tags that are selected in the gallery, but then they go to the tag page, then if they hit the 
back button, it will bring them to /gallery, but it will remove the query params! That shouldn't happen. Do like what 
the content "view" pages are doing (e.g. http://localhost:5173/view/88136). The back button for that page will bring you
back to the gallery, but it will preserve query params.

## 6. Gallery page update
Sorry that this is not part of the tag page! But it is related. I want to add a popOver that will instantly appear 
whenever a user's mouse hovers over a tag that is in the "Selected tags" area. It should say ""Click to open tag page".

## 7. Tag ratings
We have a table for this (tag_ratings), but it looks like this feature has not yet been fully implemented. If a user 
clicks the stars widget for "Your rating", it does not appear that any query actually gets executed in the backend. 
Correspondingly, nothing gets persisted into the tag_ratings table. And the users selection does not persist. 
They click it, and then move mouse away, and then it resets back to no stars being selected. Do this task last. This 
will require the most work. Do it carefully. You'll probably want to add backend and frontend tests for this. Unit 
tests, if you create new functions / methods for this. And I definitely want a frontend-e2e test for it, at least. For 
this particular task, create a document: notes/tag-ratings.md, and in it, describe what needs to be done, and make lists
of checkbox tasks for what you need to do on the frontend and backend, including any testing.

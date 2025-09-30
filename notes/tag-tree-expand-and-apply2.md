# Upates to Tag Hierarchy page
Ensure that there are playwright tests for all of these, and unit tests as well if applicable.

It is possible that for the query phase, some work will need to be done on the API, but I'm not sure. It may actually be
currently ready to execute such tag related queries.

## General task list
- [x] 1: Remember state of tree when navigating away from page and back to it (the expansion state of the tree & which 
  tags are selected)
- [x] 2: 2 buttons instead of 1: Apply, and Apply & Query Content
  - Apply will just keep the page the way it is. It won't jump to the other page or execute a query. Right now, there 
  will be no change So if you want, this button can just do nothing right now. 
- [x] 3: n Tags selected: Don't display this on the button; display it somewhere else on the screen
- [x] 4: When "Apply & Query Content" button is clicked, it should not only navigate to the Content Browser, but also 
  execute a query that filters content coming back from the API such that the data returned is only for the items with 
  those tags. Note that the query will have to also take into consideration all of the other query parameters when 
  filtering content (your gens, your auto-gens, community gens, community auto-gens), along with proper sorting.

## Details

# Bookmarks feature - frontend
## Spec

### Page: Bookmarks
This is a page where we will show all bookmark categories, and also bookmark thumbnails themselves, etc.

This page will be set up basically the same way as the dashboard page. The dashboard page has multiple sections, and 
each section has a title and shows its 5 most recent items (as a grid layout by default). 

I basically want to re-use this overall page layout component, if that's possible, so that we can keep the code DRY.

But I want the dashboard page and the bookmarks page to have some different defaults / values.

So, if you feel there are too many differences and that they should just be entirely different components, do that. But 
if you feel they should share the same component and just had different initialization/settings, do that.

#### Defaults / value differences - dashboard vs bookmarks page
N items
- Dashboard page: Shows 5 most recent items
- Bookmarks page: Should show 15 most recent items (recent in terms of when the user bookmarked the item)

Pagination
- Dashboard page: Has no pagination. Just shows 5 most recent items.
- Bookmarks page: Has pagination.

Thumbnail res
- Dashboard page: Grid layout: default thumbnail / grid cell resolution: ? (I don't remember what it is)
- Bookmarks page: Grid layout: default thumbnail / grid cell resolution: Set it to - 184x272

Icons
- Dashboard page: Doesn't have this yet. This is a new addition to the component. More on that below.
- Bookmarks page: Several icons. See more below: "Section component - new addition: icons with features"

#### Section component - new addition: icons with features
The dashbaord page has sections, and each section has a title and a grid. But it doesn't have any icons. That's fine for 
the dashboard. But for the bookmarks page, I want there to be icons at the top right, on the same row as the title.

**Public/Private**
Location: Farthest to the right.

popOver text: "Is currently: STATUS", where STATUS is either "Public" or "Private"

Either PublicIcon (`import PublicIcon from '@mui/icons-material/Public';`) if section is set to 
public, else PublicOffIcon (`import PublicOffIcon from '@mui/icons-material/PublicOff';`) if section is private.

When you click the icon, it toggles it; switching from public to private, or private to public. The icon change should 
be visible immediately, but there should be a delay so that you can't toggle more than once every 500ms.

**Edit**
Location: 2nd from right.

popOver text: "Edit category"

The icon for this should be a pencil icon. When the user clicks this, a modal will appear. It should be the very same 
form as the one described below in the "Add new category" section. The only difference is that the form header should 
read "Edit category" instead of "Add new category".

#### Bookmark category db fields we're not using
- icon: This is to assign a unique icon to categories.. We won't yet use this yet.
- color_hex
- cover_content_id
- cover_content_source_type
- parent_id: We will let users assign this when they create or update a category, but we won't do anything with it yet.
- sort_index: This is for manual sorting of category order on this page. We will do this soon; just not yet.
- share_token

#### Add new category
At the bottom of the bookmarks page, after all of the bookmark category sections, there should be a UI to 
"Add new category". If you click that / a button, then a 
form will appear, with all of the fields that you can fill out:
- name
- description
- is_public
- parent category: a dropdown, where all of the names of the existing categories are list options. Note that we will 
allow users to set this, but we will not yet add any functionality around it.

There should be a "save" button at the bottom. Once you click that, the form should disappear, and the category should 
appear as a new section (empty at first; 0 items).

#### Link to open "Category page"
There will also be a separate page that we're adding, where we can see a single category in isolation. It's described 
below in the "Page: Bookmarks category" section.

How do we get to pages representing a single bookmark category?
- By clicking the category title where it appears in the "Bookmarks" page.
- By clicking a "thumbnail" / "grid cell" displaying the text "More...". This should appear as the final item in the 
thumbnail grid for the category section. I mentioned earlier that the default number of items per page would be "15". 
So what I really mean by that is that there will be 15 grid cells, each with a thumbnail, where, if you click it, it 
will open the page for that specific image. But, there would be a 16th cell, and that cell would simply contain the text
"More...", centered vertically and horizontally. Be careful not to allow this cell to interfere with pagination. The 
number of items per page should reflect the thumbnail grid cells, and should not consider this "More..." grid cell.

#### UI options at top of the page
##### Sorting of category sections
This should control which bookmark category sections appear in which order.
 
Options:
- Datetime last updated
- Datetime created
- Alphabetical

Default: Datetime last updated (descending; most recently updated should be first)

There should be a way to make the sort option ascending or descending.

##### Sorting of category items
This should control which items within a bookmark category appear in which order.

Options:
- User's rating > Datetime added as bookmark
- User's rating
- Overall rating
- Datetime added as a bookmark
- Datetime created
- Alphabetical

Default: - User's rating > Datetime added as bookmark 

popOver texts:
- User's rating > Datetime added as bookmark: "Show all the ones that the user has rated first, but then for the ones 
that the user hasn't rated, sort by 'Datetime added as bookmark'."
- Alphabetical: "Alphabetical (Title)"

There should be a way to make the sort option ascending or descending.

##### Items/page: N
There should be a button that says "Items/page: N", where N is the number of items shown per page, 15 by default. If the
user clicks this, they should be able to change the number of items per page.

### Sidebar
We're going to have a setup similer to the "Settings" area. Use the same UI / pattern. There will be a caret, where you 
can toggle whether children are expanded/collapsed. The parent of this group should be the "Gallery" page. Then, the 
"Bookmarks" page should be its only child. It should have the following icon: `CollectionsBookmarkIcon` (`import 
CollectionsBookmarkIcon from '@mui/icons-material/CollectionsBookmark';`).

While you're at it, please change the Gallery icon to the following: `BurstModeIcon` (`import BurstModeIcon from 
'@mui/icons-material/BurstMode';`)

### Page: Bookmarks category
This page will be to browse a single bookmark category in isolation. This page should have a similar UI to the 
"Bookmarks" page. You should be able toggle public/private, edit the category, see the category header, see the grid 
items, and navigate pages. But the default number of items per page should be set to "50".

### Future work
Notice that we have all this work to display bookmarks, but nothing about how to add bookmarks. That is intentional. We 
will implement that very soon. For now, just implement these UI updates (bookmarks page, bookmarks category page, and 
sidebar updates).

## How to proceed with this work
Follow `notes/routines/iteration.md`. Include these tasks as part of the existing `bookmarks-tasks.md`. Add new sections
there. Manage your tasks there. But make reports on status updates (as applicable / if necessassary) here.

## Reports

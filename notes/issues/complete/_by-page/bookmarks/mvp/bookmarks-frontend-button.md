# Bookmarks - "Add/update bookmark" icon button
We've added pages for 'bookmarks' and 'bookmark category'. But we haven't yet added a way to add/remove/update 
individual bookmarks. We're going to do that now.

## bookmark_categories.updated_at
We're going to implement functionality to (i) add, (ii) remove, or (iii) move bookmarks to different categories.

When either (i) or (iii) happens, we should update the `updated_at` field in the `bookmark_categories` table for the 
records where the bookmark will now appear. Set the value to to the current datetime.

I know that we will need to implement some new code to do this in the frontend, but I'm not sure if we will need to 
update the backend as well in order to ensure that bookmark_categories.updated_at is updated correctly at these times; 
my guess is that updates are needed.

## The Icon
When an image is not bookmarked by the user, the icon will be `BookmarkBorder` (`import BookmarkBorderIcon from 
'@mui/icons-material/BookmarkBorder';`). Otherwise if it is a bookmark, use `BookmarkIcon` (`import BookmarkIcon from 
'@mui/icons-material/Bookmark';`).

## Button location 1: Image view page
The icon button should appear on "image view" pages (`view/CONTENT_ID`), directly to the left of the 'trashbin' icon.

## Button location 2+: Grid cells
For all image grids, this icon should appear within the grid cell. Icons in grid cells should always appear at the top 
right of the area beneath the thumbnail, on the same row as the title.

I think currently there is only 1 image grid component and it is shared between pages. If that's the case, add this 
there. However, if that's not the case and there are multiple grid components, add to all of them. In the end, I want 
the following pages to have this button in their image grid cells:
- Image generation > history tab
- Gallery page

Although, I have just decided I want to customize this a bit and have the grid be configured to optionally not display 
this icon button. I've decided I dont' want to see it on the "Dashboard" page. So you should set up the dashboard grid 
in that way, to not display it.

## Behavior: Add bookmark
If the image is currently not bookmarked, then when the user clicks it, the following should happen:
- Add the bookmark to the default category, which should be set to 'Uncategorized'.
- Update the 
- Set the bookmark to 'private' by default.
- The icon should change from `BookmarkBorder` to `BookmarkIcon`

## Behavior: Update bookmark
If the image is currently a bookmark, then if the user clicks the bookmark icon, it will open up a modal, which will 
have the following options.

1. Public/Private toggle.
This should also have text that says: 'Public bookmarks have not yet been implemented. As of now, even if you set it to 
public, all bookmarks will be private.'

2. Multi-assign: categories
Have a dropdown multi-select widget, where there is one selection option for each bookmark category.

There should also be a dropdown next to it or above it, where the user can adjust the sorting order in which items 
appear in this categories dropdown. The sorting dropdown should have the options: "Recent activity" (default), and 
"Alphabetical". "Recent activity" will corresopnd to the bookmark_categories.updated_at datetime values. Also have the
option for the user to toggle between ascending and descending. 

Note that when the user saves their selection, we shouldn't send multiple requests to the backend. Handle all of the 
changes in this form with a single web request. I imagine that you will need to update an existing route, more likely, 
create a new one. For each categoriey that the user has selected, an entry should appear in the 
bookmark_category_members table. It may be that the selections sent may include some entries that are already in that 
table. If so, we don't need to update those entries nor do we need to add a new record. We just need to add new records 
for newly added categories. But we also need to remove any records that the user has deselected. So liekly most / all of
the time, the backend will need to query the db to see the categories that the bookmark has already been assigned to, 
and then the current selections state sent by the frontend after the user clicks "Save", and then update what the 
database has based on this information, adding categories that do not appear, and removing ones that should no longer 
appear in the db. Note that you can leave the `position` field untouched. This is for manual sorting within the 
category, which we are not doing.

If you have more efficient, stable ways to do this other than what I just said, go with whatever works.

Also, an important thing. What if the user clicks 'save', but leaves all of the categories unchecked (0 categories 
selected)? In that case, we will add/retain the bookmark in the "Uncategorized" category (even if the user did not 
select it from the list).

3. Buttons at bottom

- Remove bookmark
- Cancel
- Save

Make the 'remove bookmark' button red, and appear at the bottom left. 'Save' and 'Cancel' should be on the right, with
'Save' being the furthest to the right.

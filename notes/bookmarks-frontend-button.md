# Bookmarks - "Add/update bookmark" icon button
We've added pages for 'bookmarks' and 'bookmark category'. But we haven't yet added a way to add/remove/update 
individual bookmarks. We're going to do that now.

## The Icon
When an image is not bookmarked by the user, the icon will be `BookmarkBorder` (`import BookmarkBorderIcon from 
'@mui/icons-material/BookmarkBorder';). Otherwise if it is a bookmark, use `BookmarkIcon` (`import BookmarkIcon from 
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
- Set the bookmark to 'private' by default.

## Behavior: Update bookmark

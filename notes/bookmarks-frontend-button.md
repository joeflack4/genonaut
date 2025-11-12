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

## Behavior: Add bookmark

## Behavior: Update bookmark

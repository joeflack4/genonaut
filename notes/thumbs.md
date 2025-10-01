# Thumbnails
I'd like to update the "Dashboard" and "Gallery" pages. The content_items are going to all be images. Right now we're 
only showing in list view. We're not displaying any actual images, thumbnails for images, nor placeholders for images.

I want to change that. I want to display thumbnails of images. Right now, the full path of images in the content_items 
and content_items_auto tables resides in the content_data column. I you to add a new field to the model for these tables 
(schema.py): it should be called "path_thumb". This will be the path on disk to the thumbnail. In the future, we will 
have multiple such fields for different resolutions, but for now, just 1 field. After you add this to the model, run the 
`migrate-prep` command to do an auto-migration. Then you can update the demo database with `migrate-demo`. You can try 
the `migrate-dev` too but if it gives you an error that's ok, we're not using that DB right now.

Once that's in place, you should be good to update the API to provide thumbnail data as well.

Then, most of the work is going to be on the frontend. I want to have 2 new icons at the top right of the "Dashboard" 
and "Gallery" pages. The Gallery page already has an icon up there for 'settings' / 'options'. You can put these icons 
to the left of those. One of these icons will be for "list view" (which is what is currently implemented). The other 
will be for "grid view" (AKA "thumbnail view") (what you are going to implement now). Whichever view is active should change the icon color 
so that it appears active.

As a later phase for this, I also want diferent sizes for thumbnails. So you might want a little down arrow next to the 
/ attached to the "thumbnail view" icon, where it pops out a dropdown for the user to select a resolution.

Here are the resolution options:

576 x 768
520 × 698 (≈91% of ref)
480 × 644 (≈84%)
440 × 590 (≈77%)
400 × 537 (≈70%)
360 × 484 (≈63%)
320 × 430 (≈56%)
300 × 403 (≈53%)

Please make "480 × 644" the default resolution for "thumbnail view" when it is selected.

Navigating away and back to these pages should retain state / memory of the current view that is active on that page.

For rendering of images, if the thumbnail is not present, but the full image is present, then render the full image as a
fallback. However, you should shrink its appearance such that it fits into the grid cell. So if the resolution of each 
grid cell is 480 × 644, but the image is 576 x 768, it should dynamically shrink down the image to fit into the cell.

If the user clicks the image, then there should be a new temporary page that opens up, that displays the image in its 
full size, with image metadata beneath it. Hitting back on the navigation should return the user to the Gallery page, 
but there should also be a "back" arrow icon for the user to select to do that navigation too.

The path for the full size imags are in the content_data columns.

Placeholders:
Note that right now, we actually have no images on disk. So we will use placeholders. In these cases if there is no 
thumbnail and no fallback image, then 
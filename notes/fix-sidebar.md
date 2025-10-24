# Fix sidebar issues
## Intro
We recently added a feature change to the sidebar. There are now nested options under the Settings / Account Settings 
option. However, it's not done entirely as I want it and some new bugs have been introduced.

## High-level task list
- [x] 1. Collapsed by default
- [x] 2. Behavior when (sidebar) buttons are not being displayed
- [x] 3. Viewport bug when no sidebar
- [x] 4. Add chevron when no button labels
- [x] 5. Clicking parent vs clicking chevron

## Task detials
### 1. Collapsed by default
Any sidebar options that are children of other options should only appear when that option (or one of its children) is 
currently selected (i.e. that page is currently active). The only case we have of this right now is the account 
settings. It has 2 children right now: search history, and analytics. So, if a page other than account settings, search 
history, or analytics is currently selected / active, then only the root page (account settings) should be displayed.

Then, when a user clicks account settings, or somehow otherwise gets navigated to it or one of its child pages (perhaps they navigated directly via 
entering URL to these pages), then those descendants should become visible. This of course also applies to the chevron 
/ arrow which allows a user to expand/collapse the child options under that sidebar option.

### 2. Behavior when (sidebar) buttons are not being displayed
When the option to hide button labels is currently active in the account settings and these labels are not being 
displayed, there are two problems:

1. There is no chevron visible next to the account settings page icon
2. Child pages are not indented. They should be, slightly.

### 3. Viewport bug when no sidebar
When the user clicks the hamburger icon to remove the sidebar from display, the page contents are shifted to the left.
This shouldn't happen. Indeed, there is more space when the sidebar is not there, and the page should be given more
space to fill, but right now what happens is that there is a large margin or padding that is present on the right side.
And then on the left side of the page, the page contents actually get shifted outside of the visible viewport area, so
you cannot see the whole page.

### 5. Clicking parent vs clicking chevron
I want that when the "Account settings" icon or label is clicked, it opens up the settings page. I want the 
expand/collapse behavior to only occur when the chevron is clicked. So, separate that part of the UI into two parts. 
When the user hovers over the button icon and label, that section should be highlighted, and when the user hovers over 
the chevron, only that part should be highlighted. And then make each of those sections clickable and have their own 
independent actions: navigation for the button (icon and label), and expand/collpase for the chevron.

Note that for when label doesn't show, this requires implementation of (4) showing chevron when no button labels. 

## Implementation Summaries
### Tasks 1-3
All issues have been fixed in frontend/src/components/layout/AppLayout.tsx:

1. Collapsed by default: Changed loadExpandedItems to return empty object instead of { settings: true }. Updated
   auto-expand/collapse logic to only expand parent items when the current route matches the parent or one of its
   children.

2. Behavior when buttons not displayed: Removed the showButtonLabels condition from chevron rendering so it shows even
   when labels are hidden. Increased child item left padding from 2 to 3 when labels are hidden for better visual
   indentation.

3. Viewport bug: Removed the negative margin logic (ml: { md: sidebarOpen ? 0 : -drawerWidth }) from the main content
   box, which was causing content to shift outside the viewport when the sidebar was hidden.

All unit tests updated and passing (21/21).

### Tasks 4-5
Task 4 was already completed as part of task 2 - the chevron is visible even when button labels are hidden.

Task 5 implementation - Separated Settings navigation into two independent clickable areas:

1. Restructured the parent navigation item UI: Instead of a single ListItemButton handling both navigation and expansion,
   created a Box wrapper containing two separate interactive elements:
   - ListItemButton (flex: 1) for the icon and label - handles navigation to /settings
   - IconButton for the chevron - handles expand/collapse toggle

2. Created separate event handlers:
   - handleNavClick: Navigates to the item's route (removed expansion logic)
   - handleChevronClick: Toggles expansion state (with stopPropagation to prevent navigation)

3. Independent hover states:
   - ListItemButton has default Material-UI hover behavior
   - IconButton has custom hover state (bgcolor: 'action.hover')
   - Each element highlights independently when hovered

4. Added data-testid for the chevron button to enable testing

All unit tests updated and passing (21/21). 


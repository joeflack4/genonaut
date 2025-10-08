# Gallery page thumbnails, etc - e2e playwirght testing
Create e2e playwright tests to check many things on the gallery page.

If you think that some of these are out of the scope for playwright tests, skip them with @skipped-TAG. And add a list 
and explanation of such tags in a section in this markdown document. 

## 1. Gallery Page - View Toggle & Grid Layout

### Basic View Switching
- [ ] Navigate to `/gallery`
- [ ] Verify list view is shown by default (unless localStorage has different setting)
- [ ] Click grid view icon
  - [ ] Grid view appears
  - [ ] Grid icon is highlighted (primary color)
  - [ ] List icon is default color
  - [ ] Resolution dropdown appears next to grid icon
- [ ] Click list view icon
  - [ ] List view appears
  - [ ] List icon is highlighted
  - [ ] Grid icon is default color
  - [ ] Resolution dropdown disappears
- [ ] Refresh page
  - [ ] View mode persists (stays on last selected view)

### Grid Layout Responsiveness
- [ ] Switch to grid view
- [ ] Test different viewport sizes:
  - [ ] **Mobile (< 600px)**: Should show 1-2 columns
  - [ ] **Tablet (600-900px)**: Should show 2-3 columns
  - [ ] **Desktop (900-1200px)**: Should show 3-4 columns
  - [ ] **Large Desktop (> 1200px)**: Should show 4-5 columns
- [ ] Grid adjusts smoothly during window resize
- [ ] No horizontal scrolling
- [ ] Grid cells maintain aspect ratio

### Image Rendering in Grid
- [ ] For items WITH `pathThumb`:
  - [ ] Thumbnail image loads correctly
  - [ ] Image fits within grid cell (no overflow)
  - [ ] Image maintains aspect ratio (not stretched/squashed)
  - [ ] Loading states show before image appears
- [ ] For items WITHOUT `pathThumb` but with `contentData`:
  - [ ] Full image is used as fallback
  - [ ] Image is scaled down to fit grid cell
  - [ ] No performance issues with large images
- [ ] For items WITHOUT any image:
  - [ ] Placeholder icon (ImageNotSupportedIcon) appears
  - [ ] Icon is centered in grid cell
  - [ ] Icon color is muted/disabled color
  - [ ] Cell has proper background color

### Grid Cell Interactions
- [ ] Hover over grid cell
  - [ ] Cell elevates slightly (translateY)
  - [ ] Box shadow increases
  - [ ] Transition is smooth
- [ ] Click on grid cell
  - [ ] Navigates to detail page (`/gallery/:id`)
  - [ ] Detail page shows correct item
- [ ] Keyboard navigation
  - [ ] Tab through grid cells
  - [ ] Enter key activates cell (navigates to detail)
  - [ ] Focus indicator visible

### Grid Cell Metadata Display
- [ ] Each grid cell shows:
  - [ ] Title (truncated with ellipsis if too long)
  - [ ] Full title visible on hover (tooltip)
  - [ ] Created date (formatted as locale string)
  - [ ] Text is readable (sufficient contrast)

---

## 2. Resolution Dropdown

### Dropdown Interaction
- [ ] Switch to grid view (dropdown should appear)
- [ ] Click resolution dropdown icon (down arrow)
  - [ ] Menu opens with all 8 resolution options
  - [ ] Current resolution is highlighted/selected
  - [ ] Menu is properly positioned (doesn't overflow screen)
- [ ] Click on a different resolution option
  - [ ] Menu closes
  - [ ] Grid re-renders with new resolution
  - [ ] Grid cells resize to match new aspect ratio
  - [ ] Selection persists in localStorage
- [ ] Refresh page
  - [ ] Selected resolution is remembered
  - [ ] Grid renders with correct resolution immediately

### Resolution-Specific Thumbnails
**Note**: This requires content items with `pathThumbsAltRes` populated in database

- [ ] View item that has resolution-specific thumbnails
  - [ ] At 480x644: Uses `pathThumbsAltRes['480x644']` if available
  - [ ] At 320x430: Uses `pathThumbsAltRes['320x430']` if available
  - [ ] Falls back to `pathThumb` if resolution not in alt res
  - [ ] Falls back to `contentData` if no thumbnails exist
- [ ] Verify correct image path is loaded (check Network tab)
- [ ] Switching resolutions loads different image files

### Tooltip and Accessibility
- [ ] Hover over resolution dropdown icon
  - [ ] Tooltip shows: "Grid resolution: [current resolution label]"
  - [ ] Tooltip appears after brief delay
- [ ] Keyboard navigation
  - [ ] Tab to resolution dropdown
  - [ ] Enter/Space opens menu
  - [ ] Arrow keys navigate options
  - [ ] Enter selects option
  - [ ] Escape closes menu

---

## 3. Dashboard Page - Same Tests as Gallery

### Basic View Switching
- [ ] Navigate to `/` (or `/dashboard`)
- [ ] Verify list view is shown by default
- [ ] Click grid view icon → grid appears with resolution dropdown
- [ ] Click list view icon → list appears, dropdown disappears
- [ ] Refresh page → view mode persists

### Grid Layout (same as Gallery)
- [ ] Test responsive breakpoints
- [ ] Verify grid cell sizing and aspect ratios
- [ ] Check image rendering (thumb → full → placeholder)
- [ ] Test hover effects and interactions

### Resolution Dropdown (same as Gallery)
- [ ] Open dropdown, select different resolution
- [ ] Verify grid re-renders correctly
- [ ] Verify persistence after refresh
- [ ] Test keyboard navigation

### Dashboard-Specific Checks
- [ ] Grid view works in "Your recent gens" section
- [ ] Grid view works in "Auto-gen gallery" section (if present)
- [ ] View mode is independent from Gallery page
  - [ ] Set Gallery to grid, Dashboard to list → both persist independently

---

## 4. Image Detail Pages

### Navigation from Grid View
- [ ] From Gallery grid view, click a grid cell
  - [ ] Navigate to `/gallery/:id`
  - [ ] Correct item details displayed
  - [ ] Full-size image shown (from `contentData`)
  - [ ] All metadata visible (title, date, creator, tags, quality, **prompt**)
- [ ] Click back button (browser or in-page arrow)
  - [ ] Returns to `/gallery`
  - [ ] Grid view is still active (not reset to list)
  - [ ] Scroll position preserved (if possible)

### Repeat for Dashboard
- [ ] From Dashboard grid view, click a grid cell
  - [ ] Navigate to `/dashboard/:id`
  - [ ] Correct item details displayed
- [ ] Click back button
  - [ ] Returns to `/dashboard`
  - [ ] Grid view still active

---

## 5. Cross-Browser and Responsive Testing

### Desktop Browsers
- [ ] **Chrome/Edge**: All features work
- [ ] **Firefox**: All features work
- [ ] **Safari**: All features work

### Mobile Devices (or responsive mode)
- [ ] **iOS Safari**: Touch interactions work, grid renders properly
- [ ] **Android Chrome**: Touch interactions work, grid renders properly
- [ ] Grid view is usable on small screens
- [ ] Resolution dropdown is accessible on mobile

### Orientation Changes
- [ ] Portrait mode → landscape mode
  - [ ] Grid adjusts column count appropriately
  - [ ] No layout breaks

---

## 6. Performance and Edge Cases

### Performance
- [ ] Grid with 50+ items loads smoothly
- [ ] Switching between resolutions is fast (< 1 second)
- [ ] No janky scrolling in grid view
- [ ] Large images don't cause browser lag

### Edge Cases
- [ ] Empty gallery (no items)
  - [ ] Grid view shows appropriate empty state message
  - [ ] No errors in console
- [ ] Single item in gallery
  - [ ] Grid renders correctly (doesn't stretch item)
- [ ] Very long title text
  - [ ] Text truncates with ellipsis
  - [ ] Tooltip shows full text
- [ ] Missing image sources (404 errors)
  - [ ] Placeholder icon appears
  - [ ] No broken image icons
  - [ ] No console errors spam

### LocalStorage Edge Cases
- [ ] Clear localStorage
- [ ] Reload page → defaults to list view
- [ ] Switch to grid, select resolution → saves correctly
- [ ] Open in incognito/private window → defaults apply

---

## 7. Accessibility

### Screen Reader Testing (NVDA, JAWS, or VoiceOver)
- [ ] Grid view announces correctly
- [ ] Grid cells have descriptive labels (item title)
- [ ] Resolution dropdown announces current selection
- [ ] Menu options are announced clearly

### Keyboard Navigation
- [ ] Tab through all interactive elements in logical order
- [ ] Focus indicators are visible on all elements
- [ ] No keyboard traps
- [ ] Enter/Space activates buttons and menu items

### Color Contrast
- [ ] All text meets WCAG AA contrast requirements (4.5:1)
- [ ] Focus indicators are clearly visible
- [ ] Active/inactive states distinguishable without color alone

---

## 8. Console Checks

### No Errors
- [ ] No JavaScript errors in console
- [ ] No React warnings
- [ ] No 404 errors for missing images (unless expected)

### Network Tab
- [ ] Images load from correct paths
- [ ] No duplicate image requests when switching resolutions
- [ ] Proper caching (images don't reload unnecessarily)

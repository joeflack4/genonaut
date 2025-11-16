# MUI :focus-visible Browser Compatibility Warning

**Priority**: Low
**Status**: Open
**Created**: 2025-11-16
**Component**: BookmarkManagementModal (and potentially other MUI components)
**Browser**: Chrome (latest version as of Nov 2025)

## Issue Description

When interacting with the bookmark management dialog (clicking category dropdown, sort controls, etc.), a Material-UI browser compatibility warning intermittently appears in the console:

```
MUI: The `:focus-visible` pseudo class is not supported in this browser.
Some components rely on this feature to work properly.
```

## Trigger Conditions

The warning appears the **first time** MUI needs to check focus state on any component in a browser session. Common triggers include:
- Clicking into the category selection dropdown
- Selecting items from the dropdown
- Clicking the sort order toggle button (ascending/descending)
- Other interactive MUI components

## Technical Background

The `:focus-visible` CSS pseudo-class is used by Material-UI to show focus indicators (blue outlines) **only when navigating with keyboard**, not when clicking with a mouse. This improves:
- **Accessibility**: Keyboard users can see where focus is
- **UX**: Mouse users don't see unnecessary outlines

When the browser doesn't support `:focus-visible`, MUI falls back to standard `:focus` behavior, which means focus outlines appear more often than intended (e.g., when clicking buttons, not just when tabbing).

## Stack Trace

```
installHook.js:1 MUI: The `:focus-visible` pseudo class is not supported in this browser.
overrideMethod @ installHook.js:1
isFocusVisible @ @mui_material.js?v=86f941cd:3517
(anonymous) @ @mui_material.js?v=86f941cd:4113
(anonymous) @ @mui_material.js?v=86f941cd:4231
(anonymous) @ chunk-EBIJRPEM.js?v=86f941cd:9400
executeDispatch @ react-dom_client.js?v=86f941cd:11734
...
```

## Impact Assessment

**Functional Impact**: None - the dialog and all MUI components work correctly
**Visual Impact**: Minor - users may see focus outlines more frequently than intended
**User Experience**: Minimal - most users won't notice the difference
**Developer Experience**: Low - warning appears in console but doesn't indicate a bug

## Potential Solutions

### Option 1: Add focus-visible Polyfill (Recommended if fixing)
Add a polyfill to support `:focus-visible` in browsers that lack native support:

```bash
npm install focus-visible
```

Then import in `frontend/src/main.tsx`:
```typescript
import 'focus-visible'
```

### Option 2: Configure MUI to Suppress Warning
Update MUI theme configuration to disable the warning (not recommended - hides useful information)

### Option 3: Do Nothing (Current Approach)
Accept that some browsers will show the warning. Modern browsers are adding support for `:focus-visible`, so this will naturally resolve over time.

## Related Files

- `frontend/src/components/bookmarks/BookmarkManagementModal.tsx` - Where warning is frequently observed
- Any component using MUI interactive controls (Autocomplete, TextField, IconButton, etc.)

## References

- [MDN: :focus-visible](https://developer.mozilla.org/en-US/docs/Web/CSS/:focus-visible)
- [MUI GitHub Discussion on :focus-visible](https://github.com/mui/material-ui/issues?q=focus-visible)
- [focus-visible polyfill](https://github.com/WICG/focus-visible)

## Notes

- Warning appears even in latest Chrome (as of Nov 2025), suggesting the detection logic may be overly cautious or there's a specific browser configuration issue
- Warning is logged only once per browser session
- Does not affect any functionality or user workflows
- May be worth investigating if Chrome actually lacks `:focus-visible` support or if MUI's detection is producing false positives

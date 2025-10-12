I want to set unique `data-testid` on most elements of our react layouts.

the reason is because i want to tell my colleague specifically what element i'm referring to, but since it 
doesn't have an id, i have to say like "that div that's nested here on this page with this text". it's difficult.

example case:

before:
```
<Box sx={{ p: 3, maxWidth: '100%', overflow: 'hidden' }}>
      {/* Page Header */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
```

after:
```
<Box data-testid="page-root" sx={{ p: 3, maxWidth: '100%', overflow: 'hidden' }}>
  {/* Page Header */}
  <Box data-testid="page-header" sx={{ mb: 3 }}>
    <Box
      data-testid="page-header-toolbar"
      sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}
    >
      <Box data-testid="page-header-left" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        …
      </Box>
    </Box>
  </Box>
</Box>
```

more examples:

Lists? Make them unique:
```
{items.map((it) => (
  <Box key={it.id} data-testid={`image-card-${it.id}`} />
))}

```

Some MUI components render multiple elements; set testids via slot/input props:
```
<TextField
  label="Search"
  inputProps={{ 'data-testid': 'search-input' }}   // the <input>
  FormHelperTextProps={{ 'data-testid': 'search-help' }}
/>

<IconButton data-testid="more-actions" />

```

i want you to go through all of our pages in the frontend and update as many elements as possible in this way

## Task Checklist
- [x] Review frontend pages to define consistent `data-testid` naming
- [x] Add `data-testid` attributes to `DashboardPage`
- [x] Add `data-testid` attributes to `GalleryPage`
- [x] Add `data-testid` attributes to `GalleryPage`
- [x] Add `data-testid` attributes to `GenerationPage`
- [x] Add `data-testid` attributes to `RecommendationsPage`
- [x] Add `data-testid` attributes to `TagsPage`
- [x] Add `data-testid` attributes to `SettingsPage`
- [x] Add `data-testid` attributes to admin pages (e.g., `AdminFlaggedContentPage`)
- [x] Add `data-testid` attributes to auth pages (`LoginPage`, `SignupPage`)
- [x] Add `data-testid` attributes to shared layout/root components (`App.tsx`, layout wrappers)
- [x] Update/frontend unit tests for new selectors where needed
- [x] Update frontend e2e tests for new selectors where needed
- [x] Run frontend unit tests
- [x] Run frontend e2e tests

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
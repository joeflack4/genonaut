# Playwright Test Expansion Ideas

This document outlines additional Playwright E2E tests that can be implemented and should pass with the current application state, without requiring authentication, seed data, or ComfyUI model data.

## Current Test Status
- ✅ **Passing**: 1/9 tests (ComfyUI generation parameters controls)
- ⏸️ **Appropriately Skipped**: 8/9 tests (require auth, seed data, or model data)
- 🎯 **Opportunity**: Many more tests can be added that work with current functionality

## Categories of Tests We Can Add

### 1. Navigation & Routing Tests
These test basic navigation without requiring data or authentication:

- [x] **Basic Navigation Flow**
  - Navigate to all main pages (dashboard, gallery, recommendations, settings, generation)
  - Verify correct URLs and page titles
  - Test browser back/forward navigation
  - Test direct URL access to all routes

- [x] **Navigation Menu Tests**
  - Verify all navigation items are visible
  - Test navigation item clicks and URL changes
  - Verify active states on navigation items
  - Test navigation with keyboard (Tab, Enter)

- [ ] **Responsive Navigation**
  - Test navigation on mobile viewport
  - Verify hamburger menu functionality (if implemented)
  - Test navigation drawer open/close states

### 2. Theme & UI State Tests
These test the theme system and UI state management:

- [x] **Theme Toggle Tests**
  - Toggle between light and dark mode
  - Verify theme persistence across page refreshes
  - Verify theme persistence across navigation
  - Test theme toggle from different pages

- [x] **UI Settings Tests**
  - Toggle button labels on/off
  - Verify button label setting persistence
  - Test setting changes reflect immediately
  - Verify tooltips appear when labels are hidden

- [ ] **Layout & Responsive Tests**
  - Test page layouts on different viewport sizes
  - Verify sidebar collapse/expand behavior
  - Test responsive grid layouts on different pages
  - Verify mobile-friendly touch targets

### 3. Form Validation & UX Tests
These test form behaviors without requiring backend data:

- [x] **Generation Form UX Tests** (non-data dependent)
  - Test form field focus states
  - Test input validation (number ranges, required fields)
  - Test form reset functionality
  - Test accordion expand/collapse (Advanced Settings)
  - Test slider components (if any)
  - Test form submission prevention without required fields

- [ ] **Settings Form UX Tests** (without requiring pre-filled data)
  - Test input field focus and blur states
  - Test form field validation
  - Test form submission with valid/invalid data
  - Test form reset/cancel behavior

### 4. Component Interaction Tests
These test UI component behaviors without requiring API data:

- [ ] **Modal & Dialog Tests**
  - Test modal open/close functionality
  - Test modal backdrop click behavior
  - Test modal keyboard escape behavior
  - Test focus management in modals

- [ ] **Dropdown & Select Tests**
  - Test dropdown open/close behavior
  - Test dropdown keyboard navigation
  - Test multi-select functionality (if implemented)
  - Test search within dropdowns (if implemented)

- [ ] **Loading & Error State Tests**
  - Test loading spinner appearance during API calls
  - Test error message display on API failures
  - Test retry functionality on errors
  - Test empty state displays

### 5. Accessibility Tests
These test accessibility features without requiring specific data:

- [x] **Keyboard Navigation Tests**
  - Test Tab navigation through all interactive elements
  - Test Enter/Space activation of buttons
  - Test arrow key navigation in menus/lists
  - Test Escape key behavior in modals/dropdowns

- [ ] **ARIA & Screen Reader Tests**
  - Verify proper ARIA labels on interactive elements
  - Test heading hierarchy (h1, h2, h3...)
  - Verify alt text on images
  - Test skip links functionality

- [ ] **Focus Management Tests**
  - Test focus indicators are visible
  - Test focus trapping in modals
  - Test focus restoration after modal close
  - Test logical tab order

### 6. Performance & Technical Tests
These test technical functionality without requiring specific data:

- [ ] **Page Load Performance Tests**
  - Measure and verify page load times
  - Test that critical resources load quickly
  - Verify no console errors on page load
  - Test that pages render without layout shifts

- [ ] **Error Handling Tests**
  - Test behavior when API endpoints return errors
  - Test behavior when network is offline
  - Test handling of malformed API responses
  - Verify user-friendly error messages

### 7. Browser Compatibility Tests
These test cross-browser functionality:

- [ ] **Cross-Browser Functionality**
  - Test core functionality in Chrome, Firefox, Safari
  - Test touch interactions on mobile browsers
  - Verify CSS features work across browsers
  - Test JavaScript functionality compatibility

## High-Priority Test Candidates

Based on current functionality and ease of implementation, here are the top candidates:

### Immediate Implementation (Should Pass Now)
1. **Navigation Flow Test** - Test navigation between all pages
2. **Theme Toggle Test** - Test light/dark mode switching
3. **UI Settings Test** - Test button label toggle
4. **Form Field Focus Test** - Test form input focus states
5. **Loading States Test** - Test loading spinners during API calls
6. **Error Display Test** - Test error message displays
7. **Keyboard Navigation Test** - Test Tab navigation
8. **Responsive Layout Test** - Test layouts on different screen sizes

### Short-Term Implementation (After Minor Setup)
1. **Modal Behavior Tests** - If modals are implemented
2. **Dropdown Functionality Tests** - Test select components
3. **Form Validation Tests** - Test client-side validation
4. **Page Load Performance Tests** - Measure load times
5. **Console Error Tests** - Verify no console errors
6. **ARIA Label Tests** - Verify accessibility attributes

## Test Implementation Strategy

### Phase 1: Core Navigation & Theme Tests (5-8 tests)
Start with basic navigation, theme switching, and UI state tests since these are fundamental and should be very stable.

### Phase 2: Form UX & Component Tests (8-12 tests)
Add form interaction tests and component behavior tests that don't rely on API data.

### Phase 3: Accessibility & Performance Tests (5-8 tests)
Add accessibility testing and basic performance measurements.

### Phase 4: Advanced Interaction Tests (10-15 tests)
Add more sophisticated interaction tests, error handling, and edge cases.

## Benefits of These Tests

1. **Immediate Value**: These tests provide coverage of current functionality
2. **Regression Prevention**: Catch UI/UX regressions during development
3. **Foundation Building**: Create a solid test foundation before adding data-dependent tests
4. **User Experience Focus**: Ensure the app provides a good user experience
5. **Accessibility**: Ensure the app is accessible to all users
6. **Cross-Browser**: Ensure functionality works across different browsers

## Sample Test Ideas (Specific)

### Navigation Test Example
```typescript
test('should navigate between all main pages', async ({ page }) => {
  // Start at home
  await page.goto('/')
  await expect(page).toHaveURL('/')

  // Navigate to each main page
  await page.click('[href="/dashboard"]')
  await expect(page).toHaveURL('/dashboard')

  await page.click('[href="/gallery"]')
  await expect(page).toHaveURL('/gallery')

  await page.click('[href="/recommendations"]')
  await expect(page).toHaveURL('/recommendations')

  await page.click('[href="/settings"]')
  await expect(page).toHaveURL('/settings')

  await page.click('[href="/generate"]')
  await expect(page).toHaveURL('/generate')
})
```

### Theme Toggle Test Example
```typescript
test('should toggle theme and persist across pages', async ({ page }) => {
  await page.goto('/settings')

  // Toggle to dark mode
  await page.click('text=Toggle theme')

  // Verify dark mode is applied
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')

  // Navigate to another page
  await page.click('[href="/dashboard"]')

  // Verify theme persisted
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
})
```

This expansion would significantly increase our test coverage while focusing on functionality that should work reliably with the current codebase.
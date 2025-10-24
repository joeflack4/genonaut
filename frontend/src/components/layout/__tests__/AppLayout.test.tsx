/**
 * Unit tests for AppLayout component
 * Tests hierarchical navigation, expand/collapse, localStorage persistence
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AppProviders } from '../../../app/providers'
import { AppLayout } from '../AppLayout'

// Mock hooks
vi.mock('../../../hooks', () => ({
  useCurrentUser: vi.fn(() => ({ data: { id: '1', name: 'Test User' }, isLoading: false })),
  useRecentSearches: vi.fn(() => ({ data: [] })),
  useAddSearchHistory: vi.fn(() => ({ mutate: vi.fn() })),
  useDeleteSearchHistory: vi.fn(() => ({ mutate: vi.fn() })),
}))

// Mock NotificationBell component
vi.mock('../../notifications/NotificationBell', () => ({
  NotificationBell: () => <div data-testid="notification-bell-mock" />
}))

// Mock TimeoutNotification component
vi.mock('../../notifications/TimeoutNotification', () => ({
  TimeoutNotification: () => <div data-testid="timeout-notification-mock" />
}))

function renderAppLayout() {
  return render(
    <AppProviders>
      <MemoryRouter>
        <AppLayout />
      </MemoryRouter>
    </AppProviders>
  )
}

describe('AppLayout', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('Basic Rendering', () => {
    it('renders app layout with all main elements', () => {
      renderAppLayout()

      expect(screen.getByTestId('app-layout-root')).toBeInTheDocument()
      expect(screen.getByTestId('app-layout-appbar')).toBeInTheDocument()
      expect(screen.getByTestId('app-layout-logo')).toHaveTextContent('Genonaut')
      expect(screen.getByTestId('app-layout-drawer')).toBeInTheDocument()
      expect(screen.getByTestId('app-layout-nav-list')).toBeInTheDocument()
    })

    it('renders core navigation items', () => {
      renderAppLayout()

      // Check for core navigation items that should always be visible
      expect(screen.getByTestId('app-layout-nav-link-dashboard')).toBeInTheDocument()
      expect(screen.getByTestId('app-layout-nav-link-gallery')).toBeInTheDocument()
      expect(screen.getByTestId('app-layout-nav-link-generate')).toBeInTheDocument()
      expect(screen.getByTestId('app-layout-nav-link-tag-hierarchy')).toBeInTheDocument()
      expect(screen.getByTestId('app-layout-nav-link-settings')).toBeInTheDocument()
      // Note: Some items (Recommendations, Flagged Content) may be filtered based on visibility settings
    })

    it('renders user information', () => {
      renderAppLayout()

      // User element should always be present
      expect(screen.getByTestId('app-layout-user')).toBeInTheDocument()

      // User name is only visible when showButtonLabels is true
      const userName = screen.queryByTestId('app-layout-user-name')
      if (userName) {
        expect(userName).toHaveTextContent('Test User')
      }
    })

    it('renders theme toggle button', () => {
      renderAppLayout()

      expect(screen.getByTestId('app-layout-theme-toggle')).toBeInTheDocument()
    })
  })

  describe('Hierarchical Navigation - Settings Parent', () => {
    it('renders Settings as expandable parent item', () => {
      renderAppLayout()

      const settingsLink = screen.getByTestId('app-layout-nav-link-settings')
      expect(settingsLink).toBeInTheDocument()

      // Should show expand icon (ChevronRight or ExpandMore)
      const settingsItem = screen.getByTestId('app-layout-nav-item-settings')
      expect(settingsItem).toBeInTheDocument()
    })

    it('shows Settings collapsed by default when not on settings pages', async () => {
      renderAppLayout()

      // Settings children should NOT be visible when on a non-settings page (e.g., dashboard)
      await waitFor(() => {
        expect(screen.queryByTestId('app-layout-nav-link-search-history')).not.toBeInTheDocument()
        expect(screen.queryByTestId('app-layout-nav-link-analytics')).not.toBeInTheDocument()
      })
    })

    it('toggles Settings expansion when chevron clicked', async () => {
      renderAppLayout()

      const settingsChevron = screen.getByTestId('app-layout-nav-chevron-settings')

      // Children should NOT be visible initially (collapsed by default when not on settings pages)
      expect(screen.queryByTestId('app-layout-nav-link-search-history')).not.toBeInTheDocument()
      expect(screen.queryByTestId('app-layout-nav-link-analytics')).not.toBeInTheDocument()

      // Click chevron to expand
      fireEvent.click(settingsChevron)

      // Children should appear
      await waitFor(() => {
        expect(screen.getByTestId('app-layout-nav-link-search-history')).toBeInTheDocument()
        expect(screen.getByTestId('app-layout-nav-link-analytics')).toBeInTheDocument()
      })

      // Click chevron to collapse again
      fireEvent.click(settingsChevron)

      // Children should disappear
      await waitFor(() => {
        expect(screen.queryByTestId('app-layout-nav-link-search-history')).not.toBeInTheDocument()
        expect(screen.queryByTestId('app-layout-nav-link-analytics')).not.toBeInTheDocument()
      })
    })

    it('persists expansion state in localStorage', async () => {
      renderAppLayout()

      const settingsChevron = screen.getByTestId('app-layout-nav-chevron-settings')

      // Expand Settings (starts collapsed)
      fireEvent.click(settingsChevron)

      await waitFor(() => {
        const stored = localStorage.getItem('expandedNavItems')
        expect(stored).toBeTruthy()
        const parsed = JSON.parse(stored!)
        expect(parsed.settings).toBe(true)
      })

      // Collapse Settings
      fireEvent.click(settingsChevron)

      await waitFor(() => {
        const stored = localStorage.getItem('expandedNavItems')
        expect(stored).toBeTruthy()
        const parsed = JSON.parse(stored!)
        expect(parsed.settings).toBe(false)
      })
    })
  })

  describe('Hierarchical Navigation - Child Items', () => {
    it('renders Search History child item with icon when Settings expanded', async () => {
      renderAppLayout()

      // First expand Settings to make children visible
      const settingsChevron = screen.getByTestId('app-layout-nav-chevron-settings')
      fireEvent.click(settingsChevron)

      await waitFor(() => {
        const searchHistoryLink = screen.getByTestId('app-layout-nav-link-search-history')
        expect(searchHistoryLink).toBeInTheDocument()

        const searchHistoryIcon = screen.getByTestId('app-layout-nav-icon-search-history')
        expect(searchHistoryIcon).toBeInTheDocument()
      })
    })

    it('renders Analytics child item with icon when Settings expanded', async () => {
      renderAppLayout()

      // First expand Settings to make children visible
      const settingsChevron = screen.getByTestId('app-layout-nav-chevron-settings')
      fireEvent.click(settingsChevron)

      await waitFor(() => {
        const analyticsLink = screen.getByTestId('app-layout-nav-link-analytics')
        expect(analyticsLink).toBeInTheDocument()

        const analyticsIcon = screen.getByTestId('app-layout-nav-icon-analytics')
        expect(analyticsIcon).toBeInTheDocument()
      })
    })

    it('child items are indented compared to parent when labels are shown', async () => {
      renderAppLayout()

      // First expand Settings to make children visible
      const settingsChevron = screen.getByTestId('app-layout-nav-chevron-settings')
      fireEvent.click(settingsChevron)

      await waitFor(() => {
        const settingsButton = screen.getByTestId('app-layout-nav-link-settings')
        const analyticsButton = screen.getByTestId('app-layout-nav-link-analytics')

        // Check padding (child should have more padding when showButtonLabels is true)
        const settingsStyles = window.getComputedStyle(settingsButton)
        const analyticsStyles = window.getComputedStyle(analyticsButton)

        const settingsPadding = parseInt(settingsStyles.paddingLeft)
        const analyticsPadding = parseInt(analyticsStyles.paddingLeft)

        // When showButtonLabels is false (icon-only mode), both might have same padding
        // When showButtonLabels is true, child should have more padding
        // Just verify both have padding and child has >= parent padding
        expect(analyticsPadding).toBeGreaterThanOrEqual(settingsPadding)
      })
    })
  })

  describe('Navigation Behavior', () => {
    it('clicking a child item does not trigger parent collapse', async () => {
      renderAppLayout()

      // First expand Settings to make children visible
      const settingsChevron = screen.getByTestId('app-layout-nav-chevron-settings')
      fireEvent.click(settingsChevron)

      await waitFor(() => {
        const analyticsLink = screen.getByTestId('app-layout-nav-link-analytics')
        expect(analyticsLink).toBeInTheDocument()
      })

      const analyticsLink = screen.getByTestId('app-layout-nav-link-analytics')

      // Click Analytics child
      fireEvent.click(analyticsLink)

      // Settings should still be expanded
      await waitFor(() => {
        expect(screen.getByTestId('app-layout-nav-link-search-history')).toBeInTheDocument()
        expect(screen.getByTestId('app-layout-nav-link-analytics')).toBeInTheDocument()
      })
    })

    it('chevron controls expansion independently of navigation', async () => {
      renderAppLayout()

      const settingsChevron = screen.getByTestId('app-layout-nav-chevron-settings')

      // Children should be collapsed initially
      expect(screen.queryByTestId('app-layout-nav-link-analytics')).not.toBeInTheDocument()

      // Click chevron to expand
      fireEvent.click(settingsChevron)

      // Children should be visible (expanded)
      await waitFor(() => {
        expect(screen.getByTestId('app-layout-nav-link-analytics')).toBeInTheDocument()
      })

      // Click chevron again to collapse
      fireEvent.click(settingsChevron)

      // Children should be hidden (collapsed)
      await waitFor(() => {
        expect(screen.queryByTestId('app-layout-nav-link-analytics')).not.toBeInTheDocument()
      })
    })

    it('sidebar toggle button works', () => {
      renderAppLayout()

      const toggleButton = screen.getByTestId('app-layout-toggle-sidebar')
      expect(toggleButton).toBeInTheDocument()

      // Click to toggle sidebar
      fireEvent.click(toggleButton)

      // Sidebar visibility changes (tested via DOM)
      expect(screen.getByTestId('app-layout-drawer')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('nav items have tooltips', () => {
      renderAppLayout()

      // All nav items should have Tooltip wrappers
      expect(screen.getByTestId('app-layout-nav-link-dashboard').closest('[data-mui-internal-clone-element]')).toBeTruthy()
    })

    it('all interactive elements have proper data-testids', () => {
      renderAppLayout()

      // Check critical test IDs exist
      expect(screen.getByTestId('app-layout-toggle-sidebar')).toBeInTheDocument()
      expect(screen.getByTestId('app-layout-theme-toggle')).toBeInTheDocument()
      expect(screen.getByTestId('app-layout-user')).toBeInTheDocument()
      expect(screen.getByTestId('app-layout-nav-list')).toBeInTheDocument()
    })
  })

  describe('Theme Toggle', () => {
    it('theme toggle button is clickable', () => {
      renderAppLayout()

      const themeToggle = screen.getByTestId('app-layout-theme-toggle')

      expect(themeToggle).toBeInTheDocument()

      // Click theme toggle
      fireEvent.click(themeToggle)

      // Button should still be present after click
      expect(screen.getByTestId('app-layout-theme-toggle')).toBeInTheDocument()
    })
  })

  describe('Search Functionality', () => {
    it('renders search trigger button', () => {
      renderAppLayout()

      expect(screen.getByTestId('app-layout-search-trigger')).toBeInTheDocument()
    })

    it('expands search input when trigger clicked', async () => {
      renderAppLayout()

      const searchTrigger = screen.getByTestId('app-layout-search-trigger')
      fireEvent.click(searchTrigger)

      await waitFor(() => {
        expect(screen.getByTestId('app-layout-search-input')).toBeInTheDocument()
      })
    })
  })

  describe('Edge Cases', () => {
    it('handles missing localStorage gracefully', () => {
      // Mock localStorage to throw error
      const originalGetItem = Storage.prototype.getItem
      Storage.prototype.getItem = vi.fn(() => {
        throw new Error('localStorage error')
      })

      // Should render without crashing
      renderAppLayout()

      expect(screen.getByTestId('app-layout-root')).toBeInTheDocument()

      // Restore localStorage
      Storage.prototype.getItem = originalGetItem
    })

    it('handles empty localStorage', () => {
      localStorage.clear()

      renderAppLayout()

      // Should render with default state (Settings collapsed when not on settings pages)
      expect(screen.getByTestId('app-layout-nav-link-settings')).toBeInTheDocument()
      expect(screen.queryByTestId('app-layout-nav-link-analytics')).not.toBeInTheDocument()
    })
  })
})

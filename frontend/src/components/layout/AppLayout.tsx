import { forwardRef, useState, useEffect } from 'react'
import type { NavLinkProps } from 'react-router-dom'
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  AppBar,
  Box,
  Button,
  Drawer,
  IconButton,
  InputBase,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Skeleton,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined'
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined'
import MenuIcon from '@mui/icons-material/Menu'
import PersonIcon from '@mui/icons-material/Person'
import SearchIcon from '@mui/icons-material/Search'
import DashboardIcon from '@mui/icons-material/Dashboard'
import ArticleIcon from '@mui/icons-material/Article'
import RecommendIcon from '@mui/icons-material/Recommend'
import SettingsIcon from '@mui/icons-material/Settings'
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh'
import AccountTreeIcon from '@mui/icons-material/AccountTree'
import FlagIcon from '@mui/icons-material/Flag'
import BarChartIcon from '@mui/icons-material/BarChart'
import HistoryIcon from '@mui/icons-material/History'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import BurstModeIcon from '@mui/icons-material/BurstMode'
import CollectionsBookmarkIcon from '@mui/icons-material/CollectionsBookmark'
import { Collapse } from '@mui/material'
import { useCurrentUser, useRecentSearches, useAddSearchHistory, useDeleteSearchHistory } from '../../hooks'
import { useThemeMode } from '../../app/providers/theme'
import { useUiSettings } from '../../app/providers/ui'
import { NotificationBell } from '../notifications/NotificationBell'
import { TimeoutNotification } from '../notifications/TimeoutNotification'
import { SearchHistoryDropdown } from '../search/SearchHistoryDropdown'
import { UI_CONFIG } from '../../config/ui'

/**
 * Navigation item structure supporting hierarchical navigation
 */
interface NavItem {
  label: string
  to: string
  icon: React.ComponentType
  key: string
  children?: NavItem[]
}

const navItems: NavItem[] = [
  { label: 'Dashboard', to: '/dashboard', icon: DashboardIcon, key: 'dashboard' },
  {
    label: 'Gallery',
    to: '/gallery',
    icon: BurstModeIcon,
    key: 'gallery',
    children: [
      { label: 'Bookmarks', to: '/bookmarks', icon: CollectionsBookmarkIcon, key: 'bookmarks' },
    ]
  },
  { label: 'Generate', to: '/generate', icon: AutoFixHighIcon, key: 'generate' },
  { label: 'Tag Hierarchy', to: '/tags', icon: AccountTreeIcon, key: 'tags' },
  { label: 'Recommendations', to: '/recommendations', icon: RecommendIcon, key: 'recommendations' },
  { label: 'Flagged Content', to: '/admin/flagged-content', icon: FlagIcon, key: 'flagged-content' },
  {
    label: 'Settings',
    to: '/settings',
    icon: SettingsIcon,
    key: 'settings',
    children: [
      { label: 'Search History', to: '/settings/search-history', icon: HistoryIcon, key: 'search-history' },
      { label: 'Analytics', to: '/settings/analytics', icon: BarChartIcon, key: 'analytics' },
    ]
  },
]

const NavLinkButton = forwardRef<HTMLAnchorElement, NavLinkProps>((props, ref) => (
  <NavLink ref={ref} {...props} />
))

NavLinkButton.displayName = 'NavLinkButton'

const LAST_GALLERY_URL_KEY = 'lastGalleryUrl'
const EXPANDED_NAV_ITEMS_KEY = 'expandedNavItems'

/**
 * Load expanded nav items from localStorage
 */
function loadExpandedItems(): Record<string, boolean> {
  try {
    const stored = localStorage.getItem(EXPANDED_NAV_ITEMS_KEY)
    return stored ? JSON.parse(stored) : {} // Default: All collapsed
  } catch {
    return {}
  }
}

/**
 * Save expanded nav items to localStorage
 */
function saveExpandedItems(expanded: Record<string, boolean>): void {
  try {
    localStorage.setItem(EXPANDED_NAV_ITEMS_KEY, JSON.stringify(expanded))
  } catch {
    // Silently fail if localStorage is unavailable
  }
}

export function AppLayout() {
  const { data: currentUser, isLoading: isUserLoading } = useCurrentUser()
  const { mode, toggleMode } = useThemeMode()
  const { showButtonLabels, visibleSidebarPages } = useUiSettings()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const navigate = useNavigate()
  const location = useLocation()

  // Filter nav items based on visibility settings
  const visibleNavItems = navItems.filter((item) => visibleSidebarPages[item.key] ?? true)

  // Dynamic drawer width based on whether labels are shown
  const drawerWidth = showButtonLabels ? 220 : 72

  // State for sidebar open/closed
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // State for hierarchical nav expansion (persisted in localStorage)
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>(loadExpandedItems)

  // State for search functionality
  const [searchExpanded, setSearchExpanded] = useState(false)
  const [searchValue, setSearchValue] = useState('')
  const [showSearchHistory, setShowSearchHistory] = useState(false)

  // Search history hooks
  const userId = currentUser?.id || ''
  // Fetch limited number of recent searches for dropdown display
  const { data: recentSearches } = useRecentSearches(userId, UI_CONFIG.SEARCH_HISTORY_DROPDOWN_LIMIT)
  const addSearchHistory = useAddSearchHistory(userId)
  const deleteSearchHistory = useDeleteSearchHistory(userId)

  // Set default sidebar state based on screen size
  useEffect(() => {
    setSidebarOpen(!isMobile)
  }, [isMobile])

  // Auto-expand/collapse parent items based on current route
  // Parent items should only be expanded when the parent or one of its children is active
  useEffect(() => {
    const path = location.pathname
    const newExpandedItems: Record<string, boolean> = {}

    navItems.forEach((item) => {
      if (item.children) {
        // Check if parent or any child is active
        const isParentActive = path === item.to || path.startsWith(item.to + '/')
        const hasActiveChild = item.children.some((child) => path.startsWith(child.to))

        // Expand only if parent or child is active
        newExpandedItems[item.key] = isParentActive || hasActiveChild
      }
    })

    // Only update if something changed
    const hasChanges = Object.keys(newExpandedItems).some(
      (key) => newExpandedItems[key] !== expandedItems[key]
    )

    if (hasChanges) {
      setExpandedItems(newExpandedItems)
      saveExpandedItems(newExpandedItems)
    }
  }, [location.pathname]) // Removed expandedItems dependency to avoid infinite loop

  // Save gallery URL with query params whenever we're on the gallery page
  useEffect(() => {
    if (location.pathname === '/gallery') {
      const fullGalleryUrl = location.pathname + location.search
      sessionStorage.setItem(LAST_GALLERY_URL_KEY, fullGalleryUrl)
    }
  }, [location])

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen)
  }

  const handleToggleExpand = (itemKey: string) => {
    setExpandedItems((prev) => {
      const next = { ...prev, [itemKey]: !prev[itemKey] }
      saveExpandedItems(next)
      return next
    })
  }

  const handleUserClick = () => {
    navigate('/settings')
  }

  const handleSearchClick = () => {
    setSearchExpanded(true)
  }

  const handleSearchSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    const trimmedSearch = searchValue.trim()

    // Save to history if non-empty
    if (trimmedSearch) {
      addSearchHistory.mutate(trimmedSearch)
    }

    // Navigate to gallery with search param
    const searchParam = trimmedSearch ? `?search=${encodeURIComponent(trimmedSearch)}` : ''
    navigate(`/gallery${searchParam}`)

    setSearchExpanded(false)
    setSearchValue('')
    setShowSearchHistory(false)
  }

  const handleSearchBlur = () => {
    // Delay to allow clicks on dropdown
    setTimeout(() => {
      if (!searchValue.trim()) {
        setSearchExpanded(false)
      }
      setShowSearchHistory(false)
    }, 200)
  }

  const handleHistoryItemClick = (searchQuery: string) => {
    setSearchValue(searchQuery)
    navigate(`/gallery?search=${encodeURIComponent(searchQuery)}`)
    setSearchExpanded(false)
    setShowSearchHistory(false)
  }

  const handleHistoryItemDelete = (searchQuery: string) => {
    deleteSearchHistory.mutate(searchQuery)
  }

  return (
    <>
      <Box
      sx={{ minHeight: '100vh', bgcolor: 'background.default', color: 'text.primary' }}
      data-testid="app-layout-root"
    >
      <AppBar position="static" component="header" elevation={0} color="primary" data-testid="app-layout-appbar">
        <Toolbar sx={{ justifyContent: 'space-between', gap: 2 }} data-testid="app-layout-toolbar">
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} data-testid="app-layout-brand">
            <Tooltip title="Toggle sidebar" enterDelay={1500} arrow>
              <IconButton
                color="inherit"
                aria-label="toggle sidebar"
                edge="start"
                onClick={handleSidebarToggle}
                sx={{ mr: 1 }}
                data-testid="app-layout-toggle-sidebar"
              >
                <MenuIcon />
              </IconButton>
            </Tooltip>
            <Typography variant="h6" component="div" sx={{ fontWeight: 600 }} data-testid="app-layout-logo">
              Genonaut
            </Typography>
          </Box>
          <Box
            sx={{ display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1, justifyContent: 'flex-end' }}
            data-testid="app-layout-header-controls"
          >
            <Box sx={{ position: 'relative' }}>
              <Box
                component="form"
                onSubmit={handleSearchSubmit}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  bgcolor: searchExpanded ? 'rgba(255, 255, 255, 0.15)' : 'transparent',
                  borderRadius: 1,
                  transition: (theme) => theme.transitions.create(['background-color', 'width'], {
                    duration: theme.transitions.duration.short,
                  }),
                  width: searchExpanded ? 250 : 'auto',
                  mr: 1,
                }}
                data-testid="app-layout-search-form"
              >
                {!searchExpanded ? (
                  <Tooltip title="Search" enterDelay={1500} arrow>
                    <IconButton
                      color="inherit"
                      onClick={handleSearchClick}
                      sx={{ p: 1 }}
                      data-testid="app-layout-search-trigger"
                    >
                      <SearchIcon />
                    </IconButton>
                  </Tooltip>
                ) : (
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', px: 1 }} data-testid="app-layout-search-active">
                    <SearchIcon sx={{ color: 'inherit', mr: 1 }} />
                    <InputBase
                      placeholder="Search..."
                      value={searchValue}
                      onChange={(e) => setSearchValue(e.target.value)}
                      onFocus={() => setShowSearchHistory(true)}
                      onBlur={handleSearchBlur}
                      autoFocus
                      sx={{
                        color: 'inherit',
                        flex: 1,
                        '& .MuiInputBase-input': {
                          padding: '8px 0',
                          '&::placeholder': {
                            color: 'inherit',
                            opacity: 0.7,
                          },
                        },
                      }}
                      inputProps={{ 'data-testid': 'app-layout-search-input' }}
                    />
                  </Box>
                )}
              </Box>
              {searchExpanded && (
                <SearchHistoryDropdown
                  items={recentSearches || []}
                  onItemClick={handleHistoryItemClick}
                  onItemDelete={handleHistoryItemDelete}
                  show={showSearchHistory && (recentSearches?.length || 0) > 0}
                />
              )}
            </Box>
            <Tooltip title={mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} enterDelay={1500} arrow>
              <Button
                variant={showButtonLabels ? "outlined" : "text"}
                color="inherit"
                onClick={toggleMode}
                startIcon={
                  mode === 'dark' ? <LightModeOutlinedIcon fontSize="small" /> : <DarkModeOutlinedIcon fontSize="small" />
                }
                sx={{ textTransform: 'none' }}
                data-testid="app-layout-theme-toggle"
              >
                {showButtonLabels && (mode === 'dark' ? 'Light mode' : 'Dark mode')}
              </Button>
            </Tooltip>
            <NotificationBell />
            {isUserLoading ? (
              <Skeleton variant="text" width={120} data-testid="app-layout-user-loading" />
            ) : (
              <Tooltip title="Go to account settings" enterDelay={1500} arrow>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    cursor: 'pointer',
                    borderRadius: 1,
                    px: 1,
                    py: 0.5,
                    '&:hover': {
                      bgcolor: 'action.hover'
                    }
                  }}
                  onClick={handleUserClick}
                  data-testid="app-layout-user"
                >
                  <PersonIcon fontSize="small" />
                  {showButtonLabels && (
                    <Typography variant="subtitle1" component="div" data-testid="app-layout-user-name">
                      {currentUser?.name ?? 'Admin'}
                    </Typography>
                  )}
                </Box>
              </Tooltip>
            )}
          </Box>
        </Toolbar>
      </AppBar>
      <Box sx={{ display: 'flex', minHeight: 'calc(100vh - 64px)' }} data-testid="app-layout-body">
        <Box component="nav" sx={{ width: { md: sidebarOpen ? drawerWidth : 0 }, flexShrink: { md: 0 } }} data-testid="app-layout-nav">
          <Drawer
            variant={isMobile ? 'temporary' : 'persistent'}
            open={sidebarOpen}
            onClose={handleSidebarToggle}
            ModalProps={{
              keepMounted: true, // Better mobile performance
            }}
            sx={{
              '& .MuiDrawer-paper': {
                width: drawerWidth,
                boxSizing: 'border-box',
                borderRight: 1,
                borderColor: 'divider',
                position: { xs: 'fixed', md: 'relative' },
                height: { md: '100%' },
                top: { xs: 64, md: 0 }, // Account for AppBar height on mobile
              },
            }}
            data-testid="app-layout-drawer"
          >
            <List data-testid="app-layout-nav-list">
              {visibleNavItems.map((item) => {
                const IconComponent = item.icon
                const isGallery = item.key === 'gallery'
                const hasChildren = item.children && item.children.length > 0
                const isExpanded = expandedItems[item.key] || false

                const handleNavClick = (e: React.MouseEvent) => {
                  // For items with children, this handles navigation to parent route
                  // Expansion is handled separately by chevron click
                  if (isGallery) {
                    e.preventDefault()
                    const lastGalleryUrl = sessionStorage.getItem(LAST_GALLERY_URL_KEY)
                    navigate(lastGalleryUrl || '/gallery')
                  } else {
                    // Navigate to the item's route
                    navigate(item.to)
                  }

                  if (isMobile) {
                    handleSidebarToggle()
                  }
                }

                const handleChevronClick = (e: React.MouseEvent) => {
                  e.preventDefault()
                  e.stopPropagation()
                  handleToggleExpand(item.key)
                }

                // Check if this parent item or any of its children are active
                const isParentActive = location.pathname === item.to ||
                  (hasChildren && item.children!.some((child) => location.pathname.startsWith(child.to)))

                return (
                  <Box key={item.to}>
                    <ListItem disablePadding data-testid={`app-layout-nav-item-${item.label.toLowerCase().replace(/\s+/g, '-')}`}>
                      <Box
                        sx={{
                          display: 'flex',
                          width: '100%',
                          alignItems: 'center',
                          ...(isParentActive && !hasChildren ? {
                            bgcolor: 'action.selected',
                          } : {}),
                          ...(isGallery && location.pathname === '/gallery' ? {
                            bgcolor: 'action.selected',
                          } : {}),
                          ...(hasChildren && location.pathname === item.to ? {
                            bgcolor: 'action.selected',
                          } : {}),
                          '&:hover': {
                            bgcolor: 'action.hover',
                          },
                        }}
                      >
                        {/* Main navigation button (icon and label) */}
                        <Tooltip title={item.label} enterDelay={1500} arrow placement="right">
                          <ListItemButton
                            onClick={handleNavClick}
                            sx={{
                              flex: 1,
                              bgcolor: 'transparent',
                              cursor: 'pointer',
                              pr: hasChildren ? 0 : undefined,
                              '&:hover': {
                                bgcolor: 'transparent',
                              },
                            }}
                            data-testid={`app-layout-nav-link-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                          >
                            <ListItemIcon data-testid={`app-layout-nav-icon-${item.label.toLowerCase().replace(/\s+/g, '-')}`}>
                              <IconComponent />
                            </ListItemIcon>
                            {showButtonLabels && <ListItemText primary={item.label} />}
                          </ListItemButton>
                        </Tooltip>

                        {/* Separate chevron button for expand/collapse */}
                        {hasChildren && (
                          <Tooltip title={isExpanded ? "Collapse" : "Expand"} enterDelay={1500} arrow placement="right">
                            <IconButton
                              onClick={handleChevronClick}
                              size="small"
                              sx={{
                                mr: 1,
                                ml: showButtonLabels ? 0 : 'auto',
                                bgcolor: 'transparent',
                                '&:hover': {
                                  bgcolor: 'transparent',
                                },
                              }}
                              data-testid={`app-layout-nav-chevron-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                            >
                              {isExpanded ? <ExpandMoreIcon fontSize="small" /> : <ChevronRightIcon fontSize="small" />}
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </ListItem>

                    {/* Render child items */}
                    {hasChildren && (
                      <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                        <List component="div" disablePadding>
                          {item.children!.map((child) => {
                            const ChildIconComponent = child.icon
                            const isChildActive = location.pathname.startsWith(child.to)

                            const handleChildClick = () => {
                              navigate(child.to)
                              if (isMobile) {
                                handleSidebarToggle()
                              }
                            }

                            return (
                              <ListItem
                                key={child.to}
                                disablePadding
                                data-testid={`app-layout-nav-item-${child.label.toLowerCase().replace(/\s+/g, '-')}`}
                              >
                                <Tooltip title={child.label} enterDelay={1500} arrow placement="right">
                                  <ListItemButton
                                    onClick={handleChildClick}
                                    sx={{
                                      pl: showButtonLabels ? 4 : 3,
                                      ...(isChildActive ? {
                                        bgcolor: 'action.selected',
                                      } : {}),
                                    }}
                                    data-testid={`app-layout-nav-link-${child.label.toLowerCase().replace(/\s+/g, '-')}`}
                                  >
                                    <ListItemIcon
                                      sx={{ minWidth: showButtonLabels ? 40 : 56 }}
                                      data-testid={`app-layout-nav-icon-${child.label.toLowerCase().replace(/\s+/g, '-')}`}
                                    >
                                      <ChildIconComponent fontSize="small" />
                                    </ListItemIcon>
                                    {showButtonLabels && <ListItemText primary={child.label} />}
                                  </ListItemButton>
                                </Tooltip>
                              </ListItem>
                            )
                          })}
                        </List>
                      </Collapse>
                    )}
                  </Box>
                )
              })}
            </List>
          </Drawer>
        </Box>
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            py: 2,
            px: { xs: 1, lg: 2 },
            width: '100%',
            maxWidth: '100%',
            minWidth: 0,
          }}
          data-testid="app-layout-content"
        >
          <Outlet />
        </Box>
      </Box>
    </Box>
    <TimeoutNotification />
  </>
  )
}

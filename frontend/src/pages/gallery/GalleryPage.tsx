import { useMemo, useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import type { SelectChangeEvent } from '@mui/material/Select'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Drawer,
  FormControl,
  FormControlLabel,
  IconButton,
  InputAdornment,
  InputLabel,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  MenuItem,
  Pagination,
  Paper,
  Popper,
  Select,
  Skeleton,
  Snackbar,
  Stack,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import SearchIcon from '@mui/icons-material/Search'
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import ViewListIcon from '@mui/icons-material/ViewList'
import GridViewIcon from '@mui/icons-material/GridView'
import { useUnifiedGallery, useCurrentUser, useRecentSearches, useAddSearchHistory, useDeleteSearchHistory, useTags, useBookmarkStatusBatch, usePaginationCursorCache } from '../../hooks'
import { ADMIN_USER_ID } from '../../constants/config'
import type { GalleryItem, ThumbnailResolutionId, ViewMode } from '../../types/domain'
import {
  DEFAULT_GRID_VIEW_MODE,
  DEFAULT_THUMBNAIL_RESOLUTION,
  DEFAULT_THUMBNAIL_RESOLUTION_ID,
  DEFAULT_VIEW_MODE,
  GALLERY_VIEW_MODE_STORAGE_KEY,
  THUMBNAIL_RESOLUTION_OPTIONS,
} from '../../constants/gallery'
import { loadViewMode, persistViewMode } from '../../utils/viewModeStorage'
import { GridView as GalleryGridView, ResolutionDropdown, GoToPageButton } from '../../components/gallery'
import { TagFilter } from '../../components/gallery/TagFilter'
import { SearchHistoryDropdown } from '../../components/search/SearchHistoryDropdown'
import { VirtualScrollList } from '../../components/common/VirtualScrollList'
import { ImageGridCell } from '../../components/gallery/ImageGridCell'
import { UI_CONFIG } from '../../config/ui'

const PAGE_SIZE = 25
const VIRTUAL_SCROLL_PAGE_SIZE = 100
const PANEL_WIDTH = 360
const DEFAULT_USER_ID = ADMIN_USER_ID
const GALLERY_OPTIONS_OPEN_KEY = 'gallery-options-open'
const GALLERY_VIRTUAL_SCROLL_KEY = 'gallery-virtual-scroll'
const EARLY_FEATURES_STORAGE_KEY = 'early-features'

type SortOption = 'recent' | 'top-rated'

interface FiltersState {
  search: string
  sort: SortOption
  page: number
}

interface ContentToggles {
  yourGens: boolean
  yourAutoGens: boolean
  communityGens: boolean
  communityAutoGens: boolean
}

const sortOptions: Array<{ value: SortOption; label: string }> = [
  { value: 'recent', label: 'Most Recent' },
  { value: 'top-rated', label: 'Top Rated' },
]

function arraysEqualIgnoreOrder(a: string[], b: string[]): boolean {
  if (a.length !== b.length) {
    return false
  }
  const sortedA = [...a].sort()
  const sortedB = [...b].sort()
  return sortedA.every((value, index) => value === sortedB[index])
}

export function GalleryPage() {
  const [searchParams, setSearchParams] = useSearchParams()

  // Cursor cache for hybrid pagination (page numbers in URL, cursors under the hood)
  const { getCursor, setCursor, updateFilters: updateCursorFilters } = usePaginationCursorCache()

  // Initialize search input from URL parameter
  const [searchInput, setSearchInput] = useState(() => searchParams.get('search') || '')
  const [showSearchHistory, setShowSearchHistory] = useState(false)
  const [searchFocused, setSearchFocused] = useState(false)

  // Initialize filters from URL parameters
  const [filters, setFilters] = useState<FiltersState>(() => {
    const searchFromUrl = searchParams.get('search') || ''
    const pageFromUrl = searchParams.get('p')
    const pageNumber = pageFromUrl ? Math.max(1, parseInt(pageFromUrl, 10)) : 1
    return {
      search: searchFromUrl,
      sort: 'recent' as SortOption,
      page: pageNumber - 1, // Convert to 0-based for internal use
    }
  })

  // Initialize selected tags from URL (tags parameter contains comma-delimited tag names)
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [tagNameToIdMap, setTagNameToIdMap] = useState<Map<string, string>>(new Map())
  const [tagIdToNameMap, setTagIdToNameMap] = useState<Map<string, string>>(new Map())
  const [tagsInitialized, setTagsInitialized] = useState(false) // Track if tags from URL have been loaded

  // Tag filter page state (synced with URL)
  const [tagFilterPage, setTagFilterPage] = useState(() => {
    const tagPageParam = searchParams.get('tagPage')
    return tagPageParam ? parseInt(tagPageParam, 10) : 1
  })

  // Invalid tag notification state
  const [invalidTagNames, setInvalidTagNames] = useState<string[]>([])
  const [showInvalidTagError, setShowInvalidTagError] = useState(false)
  const invalidTagsShownRef = useRef(false) // Track if we've shown the error for this URL

  // Initialize optionsOpen state from localStorage
  const [optionsOpen, setOptionsOpen] = useState(() => {
    try {
      const stored = localStorage.getItem(GALLERY_OPTIONS_OPEN_KEY)
      return stored !== null ? JSON.parse(stored) : true
    } catch {
      return true
    }
  })

  // Initialize virtual scrolling state from localStorage
  const [useVirtualScrolling, setUseVirtualScrolling] = useState(() => {
    try {
      const stored = localStorage.getItem(GALLERY_VIRTUAL_SCROLL_KEY)
      return stored !== null ? JSON.parse(stored) : false
    } catch {
      return false
    }
  })

  // Check if early features are enabled
  const [virtualScrollingFeatureEnabled, setVirtualScrollingFeatureEnabled] = useState(() => {
    try {
      const stored = localStorage.getItem(EARLY_FEATURES_STORAGE_KEY)
      const features = stored ? JSON.parse(stored) : { galleryVirtualScrolling: false }
      return features.galleryVirtualScrolling === true
    } catch {
      return false
    }
  })

  // Listen for storage changes to update feature flag
  useEffect(() => {
    const handleStorageChange = () => {
      try {
        const stored = localStorage.getItem(EARLY_FEATURES_STORAGE_KEY)
        const features = stored ? JSON.parse(stored) : { galleryVirtualScrolling: false }
        setVirtualScrollingFeatureEnabled(features.galleryVirtualScrolling === true)
      } catch {
        setVirtualScrollingFeatureEnabled(false)
      }
    }

    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [])

  // Calculate items per row for virtual scrolling
  const [itemsPerRow, setItemsPerRow] = useState(4)

  // Popover state for stats
  const [statsAnchorEl, setStatsAnchorEl] = useState<HTMLElement | null>(null)
  const [genSourceInfoAnchorEl, setGenSourceInfoAnchorEl] = useState<HTMLElement | null>(null)
  const [shouldLoadStats, setShouldLoadStats] = useState(false)

  // Initialize contentToggles from URL params
  const [contentToggles, setContentToggles] = useState<ContentToggles>(() => {
    const notGenSource = searchParams.get('notGenSource')
    const disabledSources = notGenSource ? notGenSource.split(',') : []

    return {
      yourGens: !disabledSources.includes('your-g'),
      yourAutoGens: !disabledSources.includes('your-ag'),
      communityGens: !disabledSources.includes('comm-g'),
      communityAutoGens: !disabledSources.includes('comm-ag'),
    }
  })

  const [viewMode, setViewMode] = useState<ViewMode>(() =>
    loadViewMode(GALLERY_VIEW_MODE_STORAGE_KEY, DEFAULT_VIEW_MODE)
  )

  // Ref to track if we should skip URL sync (to prevent race conditions during initialization)
  const isInitializedRef = useRef(false)
  // Ref to track number of pending URL updates for adaptive debouncing
  const pendingUrlUpdatesRef = useRef(0)
  // Ref to store debounce timer for URL updates
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)
  // Ref to track when we're programmatically updating URL (to prevent "Sync FROM URL" from interfering)
  const isProgrammaticUrlUpdateRef = useRef(false)

  const navigate = useNavigate()

  const isGridView = viewMode.startsWith('grid-')

  const currentGridResolutionId = useMemo<ThumbnailResolutionId>(() => {
    if (isGridView) {
      const resolutionId = viewMode.slice(5) as ThumbnailResolutionId
      const exists = THUMBNAIL_RESOLUTION_OPTIONS.some((option) => option.id === resolutionId)
      if (exists) {
        return resolutionId
      }
    }
    return DEFAULT_THUMBNAIL_RESOLUTION_ID
  }, [isGridView, viewMode])

  const currentResolution = useMemo(
    () =>
      THUMBNAIL_RESOLUTION_OPTIONS.find((option) => option.id === currentGridResolutionId)
      ?? DEFAULT_THUMBNAIL_RESOLUTION,
    [currentGridResolutionId]
  )

  // Calculate items per row for virtual scrolling based on resolution
  useEffect(() => {
    const updateItemsPerRow = () => {
      const containerWidth = window.innerWidth - (optionsOpen ? PANEL_WIDTH + 64 : 64) // Account for sidebar and padding
      const itemWidth = currentResolution.width + 16 // Card width + gap
      const calculatedItemsPerRow = Math.max(1, Math.floor(containerWidth / itemWidth))
      setItemsPerRow(calculatedItemsPerRow)
    }

    updateItemsPerRow()
    window.addEventListener('resize', updateItemsPerRow)
    return () => window.removeEventListener('resize', updateItemsPerRow)
  }, [currentResolution.width, optionsOpen])

  const updateViewMode = (mode: ViewMode) => {
    setViewMode(mode)
    persistViewMode(GALLERY_VIEW_MODE_STORAGE_KEY, mode)
  }

  const handleSelectListView = () => {
    updateViewMode('list')
  }

  const handleSelectGridView = () => {
    const nextMode = isGridView ? viewMode : DEFAULT_GRID_VIEW_MODE
    updateViewMode(nextMode)
  }

  const handleResolutionChange = (resolutionId: ThumbnailResolutionId) => {
    const nextMode: ViewMode = `grid-${resolutionId}`
    updateViewMode(nextMode)
  }

  const navigateToDetail = (item: GalleryItem) => {
    navigate(`/view/${item.id}`, {
      state: {
        sourceType: item.sourceType,
        from: 'gallery',
        fallbackPath: '/gallery',
      },
    })
  }

  const { data: currentUser } = useCurrentUser()
  const userId = currentUser?.id ?? DEFAULT_USER_ID

  // Search history hooks
  // Fetch limited number of recent searches for dropdown display
  const { data: recentSearches } = useRecentSearches(userId, UI_CONFIG.SEARCH_HISTORY_DROPDOWN_LIMIT)
  const addSearchHistory = useAddSearchHistory(userId)
  const deleteSearchHistory = useDeleteSearchHistory(userId)

  // Fetch all tags to build name/ID mappings (used for URL param conversion)
  // Note: API max page_size is 100
  const { data: allTagsData } = useTags({ page: 1, page_size: 100 })

  // Build tag name/ID mappings when tags are loaded
  useEffect(() => {
    if (allTagsData?.items) {
      const nameToId = new Map<string, string>()
      const idToName = new Map<string, string>()

      allTagsData.items.forEach((tag) => {
        nameToId.set(tag.name, tag.id)
        idToName.set(tag.id, tag.name)
      })

      setTagNameToIdMap(nameToId)
      setTagIdToNameMap(idToName)

      // Note: selectedTags initialization from URL is handled by the sync effect below (lines 243-259)
      // to avoid duplicate API calls
    }
  }, [allTagsData])

  // Sync search input and page from URL
  useEffect(() => {
    const searchFromUrl = searchParams.get('search') || ''
    const pageFromUrl = searchParams.get('p')
    const pageNumber = pageFromUrl ? Math.max(1, parseInt(pageFromUrl, 10)) : 1

    if (searchFromUrl !== filters.search || (pageNumber - 1) !== filters.page) {
      setFilters((prev) => ({
        ...prev,
        search: searchFromUrl,
        page: pageNumber - 1  // Convert to 0-based
      }))
      setSearchInput(searchFromUrl)
    }
  }, [searchParams])

  // Sync Selected tags with URL parameters (supports navigation/back links)
  useEffect(() => {
    if (tagNameToIdMap.size === 0) return // Wait for tags to load

    const tagsParam = searchParams.get('tags')
    const tagNamesFromUrl = tagsParam
      ? tagsParam.split(',').map(name => name.trim()).filter(name => name)
      : []

    // Track which tags are invalid (not in database)
    const invalidTags: string[] = []
    const tagIdsFromUrl: string[] = []

    tagNamesFromUrl.forEach(name => {
      const id = tagNameToIdMap.get(name)
      if (id !== undefined) {
        tagIdsFromUrl.push(id)
      } else if (name) {
        // Tag name in URL but not in database
        invalidTags.push(name)
      }
    })

    // Show error for invalid tags (only once per URL change)
    if (invalidTags.length > 0 && !invalidTagsShownRef.current) {
      setInvalidTagNames(invalidTags)
      setShowInvalidTagError(true)
      invalidTagsShownRef.current = true
    }

    if (!arraysEqualIgnoreOrder(tagIdsFromUrl, selectedTags)) {
      setSelectedTags(tagIdsFromUrl)
      setFilters((prev) => ({ ...prev, page: 0 }))
    }

    // Mark tags as initialized once we've processed the URL params
    setTagsInitialized(true)
  }, [searchParams, selectedTags, tagNameToIdMap])

  // Reset invalid tags shown flag when URL tags param changes
  useEffect(() => {
    invalidTagsShownRef.current = false
  }, [searchParams.get('tags')])

  // Sync tag filter page with URL parameter
  useEffect(() => {
    const tagPageParam = searchParams.get('tagPage')
    const pageFromUrl = tagPageParam ? parseInt(tagPageParam, 10) : 1
    if (pageFromUrl !== tagFilterPage && pageFromUrl >= 1) {
      setTagFilterPage(pageFromUrl)
    }
  }, [searchParams])

  // Sync contentToggles FROM URL (for browser back/forward navigation)
  useEffect(() => {
    // Skip on first render (state already initialized from URL in useState)
    if (!isInitializedRef.current) {
      isInitializedRef.current = true  // Mark initialized at end
      return
    }

    // Skip if we're in the middle of a programmatic URL update to prevent race conditions
    if (isProgrammaticUrlUpdateRef.current) {
      return
    }

    const notGenSource = searchParams.get('notGenSource')
    const disabledSources = notGenSource ? notGenSource.split(',') : []

    const togglesFromParams: ContentToggles = {
      yourGens: !disabledSources.includes('your-g'),
      yourAutoGens: !disabledSources.includes('your-ag'),
      communityGens: !disabledSources.includes('comm-g'),
      communityAutoGens: !disabledSources.includes('comm-ag'),
    }

    // Only update if different to avoid infinite loop with "sync to URL" useEffect
    setContentToggles((prevToggles) => {
      if (
        togglesFromParams.yourGens !== prevToggles.yourGens ||
        togglesFromParams.yourAutoGens !== prevToggles.yourAutoGens ||
        togglesFromParams.communityGens !== prevToggles.communityGens ||
        togglesFromParams.communityAutoGens !== prevToggles.communityAutoGens
      ) {
        setFilters((prev) => ({ ...prev, page: 0 }))
        return togglesFromParams
      }
      return prevToggles
    })
  }, [searchParams])

  // Sync contentToggles TO URL (when state changes from user interaction)
  // Uses adaptive debouncing: immediate execution for single actions,
  // 150ms debounce for rapid successive actions to prevent race conditions
  useEffect(() => {
    // Skip on first render
    if (!isInitializedRef.current) {
      return
    }

    // Determine if we should debounce based on pending updates
    const shouldDebounce = pendingUrlUpdatesRef.current > 0

    // Clear any existing debounce timer
    if (debounceTimerRef.current !== null) {
      clearTimeout(debounceTimerRef.current)
      debounceTimerRef.current = null
    }

    // Function to perform the actual URL update
    const performUrlUpdate = () => {
      const disabledSources: string[] = []
      if (!contentToggles.yourGens) disabledSources.push('your-g')
      if (!contentToggles.yourAutoGens) disabledSources.push('your-ag')
      if (!contentToggles.communityGens) disabledSources.push('comm-g')
      if (!contentToggles.communityAutoGens) disabledSources.push('comm-ag')

      // Set flag to prevent "Sync FROM URL" effect from running during programmatic update
      isProgrammaticUrlUpdateRef.current = true

      // Check if URL needs updating before calling setSearchParams
      const currentNotGenSource = searchParams.get('notGenSource')
      const currentDisabled = currentNotGenSource ? currentNotGenSource.split(',').sort().join(',') : ''
      const newDisabled = disabledSources.sort().join(',')

      if (currentDisabled !== newDisabled) {
        // URL needs updating
        setSearchParams((params) => {
          const newParams = new URLSearchParams(params)

          if (disabledSources.length > 0) {
            newParams.set('notGenSource', disabledSources.join(','))
          } else {
            newParams.delete('notGenSource')
          }

          // Reset to page 1 when content toggles change
          newParams.delete('p')

          return newParams
        })
      }

      // Clear the programmatic update flag and decrement pending counter after React processes the update
      setTimeout(() => {
        pendingUrlUpdatesRef.current = Math.max(0, pendingUrlUpdatesRef.current - 1)

        // Only clear flag when no more pending updates
        if (pendingUrlUpdatesRef.current === 0) {
          isProgrammaticUrlUpdateRef.current = false
        }
      }, 500)
    }

    // Increment counter BEFORE scheduling or executing (tracks both scheduled and in-progress updates)
    pendingUrlUpdatesRef.current += 1

    // Execute immediately if no pending updates, otherwise debounce
    if (shouldDebounce) {
      // Debounce by 150ms when there are rapid successive updates
      debounceTimerRef.current = setTimeout(performUrlUpdate, 150)
    } else {
      // Execute immediately for single actions (best UX)
      performUrlUpdate()
    }

    // Cleanup function to clear timeout on unmount
    return () => {
      if (debounceTimerRef.current !== null) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [contentToggles])

  // Save optionsOpen state to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(GALLERY_OPTIONS_OPEN_KEY, JSON.stringify(optionsOpen))
    } catch {
      // Ignore localStorage errors
    }
  }, [optionsOpen])

  // Save virtual scrolling state to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(GALLERY_VIRTUAL_SCROLL_KEY, JSON.stringify(useVirtualScrolling))
    } catch {
      // Ignore localStorage errors
    }
  }, [useVirtualScrolling])


  // NEW: Build content source types array directly from toggles
  const contentSourceTypes = useMemo(() => {
    const types: string[] = []
    if (contentToggles.yourGens) types.push('user-regular')
    if (contentToggles.yourAutoGens) types.push('user-auto')
    if (contentToggles.communityGens) types.push('community-regular')
    if (contentToggles.communityAutoGens) types.push('community-auto')
    return types
  }, [contentToggles])

  // Clear cursor cache when filters change
  useEffect(() => {
    const filtersKey = {
      search: filters.search,
      sort: filters.sort,
      contentSourceTypes,
      selectedTags,
    }
    updateCursorFilters(filtersKey)
  }, [filters.search, filters.sort, contentSourceTypes, selectedTags, updateCursorFilters])

  // Determine if we should wait for tags to load before making API calls
  // Wait if: (1) there are tag params in URL AND (2) tags haven't been initialized yet
  const hasTagsInUrl = searchParams.get('tags') !== null
  const shouldWaitForTags = hasTagsInUrl && !tagsInitialized
  const queryEnabled = !shouldWaitForTags

  // Use unified gallery API with new content source types
  const tagFilterParam = selectedTags.length === 0 ? undefined : selectedTags

  // Get cursor for current page from cache (if available)
  const currentPageCursor = getCursor(filters.page + 1)

  // Main query - WITHOUT stats for better performance
  const { data: unifiedData, isLoading } = useUnifiedGallery({
    page: currentPageCursor ? undefined : (filters.page + 1), // Use page-based only if no cursor
    pageSize: (useVirtualScrolling && virtualScrollingFeatureEnabled) ? VIRTUAL_SCROLL_PAGE_SIZE : PAGE_SIZE,
    cursor: currentPageCursor,
    contentSourceTypes,  // NEW: Use specific combinations instead of contentTypes + creatorFilter
    userId,
    searchTerm: filters.search || undefined,
    sortField: filters.sort === 'recent' ? 'created_at' : 'quality_score',
    sortOrder: 'desc',
    tag: tagFilterParam,
    includeStats: false,  // Explicitly request no stats for performance
  }, queryEnabled)

  // Lazy-loaded stats query - only runs when shouldLoadStats is true
  const { data: statsData } = useUnifiedGallery({
    page: currentPageCursor ? undefined : (filters.page + 1),
    pageSize: (useVirtualScrolling && virtualScrollingFeatureEnabled) ? VIRTUAL_SCROLL_PAGE_SIZE : PAGE_SIZE,
    cursor: currentPageCursor,
    contentSourceTypes,
    userId,
    searchTerm: filters.search || undefined,
    sortField: filters.sort === 'recent' ? 'created_at' : 'quality_score',
    sortOrder: 'desc',
    tag: tagFilterParam,
    includeStats: true,  // Request stats
  }, queryEnabled && shouldLoadStats)

  const data = unifiedData
  const items = data?.items ?? []
  const stats = statsData?.stats || unifiedData?.stats  // Use stats from lazy query if available, fallback to main query

  // Cache next and previous page cursors when data arrives
  useEffect(() => {
    if (data?.nextCursor) {
      setCursor(filters.page + 2, data.nextCursor) // Next page is current + 1 (1-based)
    }
    if (data?.prevCursor && filters.page > 0) {
      setCursor(filters.page, data.prevCursor) // Previous page (1-based)
    }
  }, [data?.nextCursor, data?.prevCursor, filters.page, setCursor])

  // Batch fetch bookmark statuses for all items (if user is logged in and items exist)
  const contentItemsForBatch = useMemo(() => {
    return items.map(item => ({
      contentId: item.id,
      contentSourceType: item.sourceType === 'auto' ? 'auto' : 'items'
    }))
  }, [items])

  const { getBookmarkStatus, isLoading: isLoadingBookmarks } = useBookmarkStatusBatch(
    currentUser?.id,
    contentItemsForBatch
  )

  // Track if critical data has loaded for E2E tests
  const isAppReady = !isLoading && data !== undefined

  const totalPages = useMemo(() => {
    if (!data?.total) {
      return 1
    }

    return Math.max(1, Math.ceil(data.total / ((useVirtualScrolling && virtualScrollingFeatureEnabled) ? VIRTUAL_SCROLL_PAGE_SIZE : PAGE_SIZE)))
  }, [data, useVirtualScrolling, virtualScrollingFeatureEnabled])

  // Group items into rows for virtual scrolling
  const itemRows = useMemo(() => {
    if (!isGridView || !useVirtualScrolling || !virtualScrollingFeatureEnabled) return []

    const rows: GalleryItem[][] = []
    for (let i = 0; i < items.length; i += itemsPerRow) {
      rows.push(items.slice(i, i + itemsPerRow))
    }
    return rows
  }, [items, itemsPerRow, isGridView, useVirtualScrolling, virtualScrollingFeatureEnabled])

  // Calculate row height for virtual scrolling
  const rowHeight = useMemo(() => {
    if (!currentResolution) return 300
    const aspectRatio = currentResolution.height / currentResolution.width
    const cardHeight = currentResolution.width * aspectRatio + 100 // Add space for metadata
    return cardHeight + 16 // Add gap
  }, [currentResolution])

  // Render a row of gallery items for virtual scrolling
  const renderItemRow = useCallback(
    (row: GalleryItem[]) => (
      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: `repeat(${itemsPerRow}, minmax(${currentResolution.width}px, 1fr))`,
          alignItems: 'flex-start',
          px: 1,
        }}
      >
        {row.map((item) => {
          // Get bookmark status from batch
          const contentSourceType = item.sourceType === 'auto' ? 'auto' : 'items'
          const bookmarkStatus = getBookmarkStatus(item.id, contentSourceType)

          return (
            <ImageGridCell
              key={item.id}
              item={item}
              resolution={currentResolution}
              onClick={navigateToDetail}
              dataTestId={`gallery-grid-item-${item.id}`}
              showBookmarkButton={!isLoadingBookmarks}
              userId={currentUser?.id}
              bookmarkStatus={bookmarkStatus}
            />
          )
        })}
      </Box>
    ),
    [itemsPerRow, currentResolution, navigateToDetail, getBookmarkStatus, currentUser?.id, isLoadingBookmarks]
  )

  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmedSearch = searchInput.trim()

    // Save to history if non-empty
    if (trimmedSearch) {
      addSearchHistory.mutate(trimmedSearch)
    }

    // Update URL params with search and reset to page 1
    setSearchParams((params) => {
      const newParams = new URLSearchParams(params)
      if (trimmedSearch) {
        newParams.set('search', trimmedSearch)
      } else {
        newParams.delete('search')
      }
      newParams.delete('p')  // Reset to page 1
      return newParams
    })

    setFilters((prev) => ({ ...prev, search: trimmedSearch, page: 0 }))
    setShowSearchHistory(false)
  }

  const handleSortChange = (event: SelectChangeEvent<SortOption>) => {
    setFilters((prev) => ({ ...prev, sort: event.target.value as SortOption, page: 0 }))
    // Reset to page 1 in URL
    setSearchParams((params) => {
      const newParams = new URLSearchParams(params)
      newParams.delete('p')
      return newParams
    })
  }

  const handlePageChange = (_event: React.ChangeEvent<unknown>, page: number) => {
    // Update URL with page number
    setSearchParams((params) => {
      const newParams = new URLSearchParams(params)
      if (page > 1) {
        newParams.set('p', page.toString())
      } else {
        newParams.delete('p')  // Don't show ?p=1
      }
      return newParams
    })

    // Update filters with 0-based page number
    setFilters((prev) => ({ ...prev, page: page - 1 }))
  }

  const handleToggleChange = (toggleKey: keyof ContentToggles) => (event: React.ChangeEvent<HTMLInputElement>) => {
    const checked = event.target.checked

    // Update toggles state (URL will be synced by useEffect)
    setContentToggles((prevToggles) => ({
      ...prevToggles,
      [toggleKey]: checked,
    }))

    // Reset to page 1 when toggling content types
    setFilters((prev) => ({ ...prev, page: 0 }))
    setSearchParams((params) => {
      const newParams = new URLSearchParams(params)
      newParams.delete('p')
      return newParams
    })
  }

  const handleTagFilterChange = (tags: string[]) => {
    setSelectedTags(tags)
    setFilters((prev) => ({ ...prev, page: 0 }))
    setSearchParams((params) => {
      const newParams = new URLSearchParams(params)

      // Convert tag IDs to tag names for URL
      const tagNames = tags
        .map(tagId => tagIdToNameMap.get(tagId))
        .filter((name): name is string => name !== undefined)

      if (tagNames.length > 0) {
        newParams.set('tags', tagNames.join(','))
      } else {
        newParams.delete('tags')
      }

      // Reset to page 1 when tags change
      newParams.delete('p')

      return newParams
    })
  }

  const handleTagClick = (tagId: string) => {
    const tagName = tagIdToNameMap.get(tagId)
    if (tagName) {
      navigate(`/tags/${tagName}`)
    } else {
      // Fallback: if tag name not found in map, navigate with ID
      console.warn(`Tag name not found for ID: ${tagId}. Navigating with ID.`)
      navigate(`/tags/${tagId}`)
    }
  }

  const handleNavigateToHierarchy = () => {
    navigate('/tags')
  }

  const handleTagPageChange = (page: number) => {
    setTagFilterPage(page)
    setSearchParams((params) => {
      const newParams = new URLSearchParams(params)
      if (page > 1) {
        newParams.set('tagPage', page.toString())
      } else {
        newParams.delete('tagPage')
      }
      return newParams
    })
  }

  const handleHistoryItemClick = (searchQuery: string) => {
    setSearchInput(searchQuery)
    setSearchParams((params) => {
      const newParams = new URLSearchParams(params)
      newParams.set('search', searchQuery)
      newParams.delete('p')  // Reset to page 1
      return newParams
    })
    setFilters((prev) => ({ ...prev, search: searchQuery, page: 0 }))
    setShowSearchHistory(false)
  }

  const handleHistoryItemDelete = (searchQuery: string) => {
    deleteSearchHistory.mutate(searchQuery)
  }

  const handleClearSearch = () => {
    // Clear the search input
    setSearchInput('')

    // Remove search param from URL (preserving other params like tags)
    setSearchParams((params) => {
      const newParams = new URLSearchParams(params)
      newParams.delete('search')
      newParams.delete('p')  // Reset to page 1
      return newParams
    })

    // Clear search from filters and reset to first page
    setFilters((prev) => ({ ...prev, search: '', page: 0 }))
    setShowSearchHistory(false)
  }

  const handleSearchButtonClick = () => {
    // Trigger the same logic as form submit
    const trimmedSearch = searchInput.trim()

    // Save to history if non-empty
    if (trimmedSearch) {
      addSearchHistory.mutate(trimmedSearch)
    }

    // Update URL params with search
    setSearchParams((params) => {
      const newParams = new URLSearchParams(params)
      if (trimmedSearch) {
        newParams.set('search', trimmedSearch)
      } else {
        newParams.delete('search')
      }
      newParams.delete('p')  // Reset to page 1
      return newParams
    })

    setFilters((prev) => ({ ...prev, search: trimmedSearch, page: 0 }))
    setShowSearchHistory(false)
  }

  return (
    <Box
      component="section"
      sx={{ position: 'relative', display: 'flex', flexDirection: 'column' }}
      data-testid="gallery-page-root"
      data-app-ready={isAppReady ? '1' : '0'}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
        }}
        data-testid="gallery-content-wrapper"
      >
        <Stack spacing={4} data-testid="gallery-content-stack">
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            justifyContent="space-between"
            alignItems={{ xs: 'flex-start', sm: 'center' }}
            spacing={2}
            data-testid="gallery-header"
          >
            <Box data-testid="gallery-header-title">
              <Typography
                component="h1"
                variant="h4"
                fontWeight={600}
                gutterBottom
                data-testid="gallery-title"
              >
                Gallery
              </Typography>
            </Box>
            <Stack direction="row" spacing={1} alignItems="center" data-testid="gallery-view-toggle-group">
              <Tooltip title="List view" enterDelay={300} arrow>
                <IconButton
                  aria-label="Switch to list view"
                  color={isGridView ? 'default' : 'primary'}
                  onClick={handleSelectListView}
                  data-testid="gallery-view-toggle-list"
                  aria-pressed={!isGridView}
                >
                  <ViewListIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Grid view" enterDelay={300} arrow>
                <IconButton
                  aria-label="Switch to grid view"
                  color={isGridView ? 'primary' : 'default'}
                  onClick={handleSelectGridView}
                  data-testid="gallery-view-toggle-grid"
                  aria-pressed={isGridView}
                >
                  <GridViewIcon />
                </IconButton>
              </Tooltip>
              {isGridView && (
                <ResolutionDropdown
                  currentResolution={currentGridResolutionId}
                  onResolutionChange={handleResolutionChange}
                  dataTestId="gallery-resolution-dropdown"
                />
              )}
              <Tooltip title={optionsOpen ? 'Hide options panel' : 'Show options panel'} enterDelay={300} arrow>
                <IconButton
                  aria-label={optionsOpen ? 'Hide options panel' : 'Show options panel'}
                  color={optionsOpen ? 'primary' : 'default'}
                  onClick={() => setOptionsOpen((prev) => !prev)}
                  data-testid="gallery-options-toggle-button"
                >
                  <SettingsOutlinedIcon />
                </IconButton>
              </Tooltip>
            </Stack>
          </Stack>
          <Card data-testid="gallery-results-card">
            <CardContent>
              {isGridView ? (
                (useVirtualScrolling && virtualScrollingFeatureEnabled) ? (
                  <Box data-testid="gallery-virtual-scroll-view">
                    {itemRows.length > 0 ? (
                      <VirtualScrollList
                        items={itemRows}
                        itemHeight={rowHeight}
                        containerHeight={window.innerHeight - 250} // Dynamic height based on viewport
                        renderItem={renderItemRow}
                        overscan={2}
                      />
                    ) : isLoading ? (
                      <Box
                        sx={{
                          display: 'grid',
                          gap: 2,
                          gridTemplateColumns: `repeat(auto-fill, minmax(${currentResolution.width}px, 1fr))`,
                          alignItems: 'flex-start',
                        }}
                      >
                        {Array.from({ length: 12 }).map((_, index) => (
                          <Box key={`gallery-grid-skeleton-${index}`}>
                            <Box
                              sx={{
                                position: 'relative',
                                width: '100%',
                                pt: `${(currentResolution.height / currentResolution.width) * 100}%`,
                                borderRadius: 2,
                                overflow: 'hidden',
                              }}
                            >
                              <Skeleton
                                variant="rectangular"
                                animation="wave"
                                sx={{
                                  position: 'absolute',
                                  inset: 0,
                                  width: '100%',
                                  height: '100%',
                                }}
                              />
                            </Box>
                            <Skeleton variant="text" width="80%" sx={{ mt: 1 }} />
                            <Skeleton variant="text" width="40%" />
                          </Box>
                        ))}
                      </Box>
                    ) : (
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ textAlign: 'center', py: 4 }}
                        data-testid="gallery-grid-empty"
                      >
                        No gallery items found. Try adjusting your filters.
                      </Typography>
                    )}
                  </Box>
                ) : (
                  <GalleryGridView
                    items={items}
                    resolution={currentResolution}
                    isLoading={isLoading}
                    onItemClick={navigateToDetail}
                    emptyMessage="No gallery items found. Try adjusting your filters."
                    dataTestId="gallery-grid-view"
                    showBookmarkButton={!isLoadingBookmarks}
                    userId={currentUser?.id}
                    getBookmarkStatus={getBookmarkStatus}
                  />
                )
              ) : isLoading ? (
                <Stack spacing={2} data-testid="gallery-results-loading">
                  {Array.from({ length: 5 }).map((_, index) => (
                    <Skeleton
                      key={index}
                      variant="rectangular"
                      height={72}
                      data-testid={`gallery-results-skeleton-${index}`}
                    />
                  ))}
                </Stack>
              ) : items.length > 0 ? (
                <List data-testid="gallery-results-list">
                  {items.map((item) => (
                    <ListItem
                      key={item.id}
                      disablePadding
                      alignItems="flex-start"
                      divider
                      data-testid={`gallery-result-item-${item.id}`}
                    >
                      <ListItemButton
                        onClick={() => navigateToDetail(item)}
                        data-testid={`gallery-result-item-${item.id}-button`}
                        alignItems="flex-start"
                      >
                        <ListItemText
                          primary={
                            <Stack
                              direction="row"
                              justifyContent="space-between"
                              alignItems="center"
                              spacing={2}
                              data-testid={`gallery-result-item-${item.id}-header`}
                            >
                              <Typography variant="h6" component="span" data-testid={`gallery-result-item-${item.id}-title`}>
                                {item.title}
                              </Typography>
                              {item.qualityScore !== null && item.qualityScore !== undefined && (
                                <Chip
                                  label={`Quality ${(item.qualityScore * 100).toFixed(0)}%`}
                                  color={item.qualityScore > 0.75 ? 'success' : 'default'}
                                  data-testid={`gallery-result-item-${item.id}-quality`}
                                />
                              )}
                            </Stack>
                          }
                          secondary={
                            <Box
                              sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, mt: 1 }}
                              data-testid={`gallery-result-item-${item.id}-meta`}
                            >
                              {item.description && (
                                <Typography
                                  variant="body2"
                                  color="text.secondary"
                                  component="span"
                                  data-testid={`gallery-result-item-${item.id}-description`}
                                >
                                  {item.description}
                                </Typography>
                              )}
                              <Typography
                                variant="caption"
                                color="text.secondary"
                                component="span"
                                data-testid={`gallery-result-item-${item.id}-created`}
                              >
                                Created {new Date(item.createdAt).toLocaleString()}
                              </Typography>
                            </Box>
                          }
                          primaryTypographyProps={{ component: 'span' }}
                          secondaryTypographyProps={{ component: 'span' }}
                        />
                      </ListItemButton>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary" data-testid="gallery-results-empty">
                  No gallery items found. Try adjusting your filters.
                </Typography>
              )}
            </CardContent>
          </Card>

          {!(useVirtualScrolling && virtualScrollingFeatureEnabled) && (
            <Box
              display="flex"
              justifyContent="space-between"
              alignItems="center"
              data-testid="gallery-pagination"
            >
              <Pagination
                count={totalPages}
                page={filters.page + 1}
                onChange={handlePageChange}
                color="primary"
                shape="rounded"
                data-testid="gallery-pagination-control"
              />
              <GoToPageButton
                totalPages={totalPages}
                currentPage={filters.page + 1}
                onPageChange={(page) => handlePageChange(null as any, page)}
              />
            </Box>
          )}
        </Stack>
      </Box>

      <Drawer
        anchor="right"
        variant="persistent"
        open={optionsOpen}
        sx={{
          '& .MuiDrawer-paper': {
            width: { xs: '100%', md: PANEL_WIDTH },
            boxSizing: 'border-box',
            p: 3,
            gap: 3,
            position: 'fixed',
            zIndex: (theme) => theme.zIndex.drawer,
          },
        }}
        data-testid="gallery-options-drawer"
        data-open={optionsOpen ? 'true' : 'false'}
      >
        <Stack spacing={3} sx={{ height: '100%', pb: 4 }} data-testid="gallery-options-stack">
          <Box
            sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            data-testid="gallery-options-header"
          >
            <Typography component="h2" variant="h6" fontWeight={600} data-testid="gallery-options-title">
              Options
            </Typography>
            <Tooltip title="Hide options" enterDelay={300} arrow>
              <IconButton
                aria-label="Close options"
                onClick={() => setOptionsOpen(false)}
                data-testid="gallery-options-close-button"
              >
                <CloseIcon />
              </IconButton>
            </Tooltip>
          </Box>
          <Box sx={{ textAlign: 'center' }} data-testid="gallery-options-summary">
            {!isLoading && (
              <>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ fontStyle: 'italic', display: 'inline' }}
                  data-testid="gallery-options-summary-text"
                >
                  {(data?.total ?? 0) === 0
                    ? '0 results matching filters.'
                    : `${totalPages.toLocaleString()} pages showing ${data?.total?.toLocaleString() || 0} results matching filters.`}
                </Typography>
                <IconButton
                  size="small"
                  sx={{
                    ml: 0.5,
                    p: 0.25,
                    color: 'text.secondary'
                  }}
                  onMouseEnter={(event) => {
                    setShouldLoadStats(true)  // Trigger stats loading
                    setStatsAnchorEl(event.currentTarget)
                  }}
                  onMouseLeave={() => setStatsAnchorEl(null)}
                  data-testid="gallery-options-stats-info-button"
                >
                  <InfoOutlinedIcon sx={{ fontSize: 14 }} />
                </IconButton>
              </>
            )}
          </Box>
          <Stack
            component="form"
            spacing={2}
            onSubmit={handleSearchSubmit}
            aria-label="gallery filters"
            data-testid="gallery-filter-form"
          >
            <Box sx={{ position: 'relative' }}>
              <TextField
                label="Search (by prompt & title)"
                variant="outlined"
                fullWidth
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    event.preventDefault()
                    const formElement = event.currentTarget.closest('form')
                    if (formElement) {
                      formElement.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }))
                    }
                  }
                }}
                onFocus={() => {
                  setShowSearchHistory(true)
                  setSearchFocused(true)
                }}
                onBlur={() => {
                  setTimeout(() => setShowSearchHistory(false), 200)
                  setSearchFocused(false)
                }}
                InputProps={{
                  endAdornment: (searchFocused || searchInput) && (
                    <InputAdornment position="end">
                      <Tooltip title="Execute search" enterDelay={500} arrow>
                        <IconButton
                          aria-label="execute search"
                          onClick={handleSearchButtonClick}
                          edge="end"
                          data-testid="gallery-search-button"
                        >
                          <SearchIcon />
                        </IconButton>
                      </Tooltip>
                    </InputAdornment>
                  )
                }}
                inputProps={{ 'data-testid': 'gallery-search-input' }}
              />
              <SearchHistoryDropdown
                items={recentSearches || []}
                onItemClick={handleHistoryItemClick}
                onItemDelete={handleHistoryItemDelete}
                show={showSearchHistory && (recentSearches?.length || 0) > 0}
              />
            </Box>

            <Stack direction="row" spacing={1} alignItems="center">
              <FormControl fullWidth>
                <InputLabel id="gallery-sort-label">Sort by</InputLabel>
                <Select
                  labelId="gallery-sort-label"
                  label="Sort by"
                  value={filters.sort}
                  onChange={handleSortChange}
                  data-testid="gallery-sort-select"
                >
                  {sortOptions.map((option) => (
                    <MenuItem
                      key={option.value}
                      value={option.value}
                      data-testid={`gallery-sort-option-${option.value}`}
                    >
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              {filters.search && (
                <Button
                  variant="outlined"
                  onClick={handleClearSearch}
                  sx={{ height: '56px', minWidth: '100px' }}
                  data-testid="gallery-search-clear-button"
                >
                  Clear search
                </Button>
              )}
            </Stack>
          </Stack>

          <Stack spacing={2} data-testid="gallery-content-toggles">
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Typography variant="h6" component="h2" data-testid="gallery-content-toggles-title">
                Filter by gen source
              </Typography>
              <IconButton
                size="small"
                sx={{
                  p: 0.25,
                  color: 'text.secondary'
                }}
                onMouseEnter={(event) => setGenSourceInfoAnchorEl(event.currentTarget)}
                onMouseLeave={() => setGenSourceInfoAnchorEl(null)}
                data-testid="gallery-content-toggles-info-button"
              >
                <InfoOutlinedIcon sx={{ fontSize: 14 }} />
              </IconButton>
            </Box>
            <Stack spacing={1} data-testid="gallery-content-toggles-switches">
              <FormControlLabel
                control={
                  <Switch
                    checked={contentToggles.yourGens}
                    onChange={handleToggleChange('yourGens')}
                    inputProps={{ 'data-testid': 'gallery-toggle-your-gens' }}
                  />
                }
                label="Your gens"
                data-testid="gallery-toggle-your-gens-label"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={contentToggles.yourAutoGens}
                    onChange={handleToggleChange('yourAutoGens')}
                    inputProps={{ 'data-testid': 'gallery-toggle-your-autogens' }}
                  />
                }
                label="Your auto-gens"
                data-testid="gallery-toggle-your-autogens-label"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={contentToggles.communityGens}
                    onChange={handleToggleChange('communityGens')}
                    inputProps={{ 'data-testid': 'gallery-toggle-community-gens' }}
                  />
                }
                label="Community gens"
                data-testid="gallery-toggle-community-gens-label"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={contentToggles.communityAutoGens}
                    onChange={handleToggleChange('communityAutoGens')}
                    inputProps={{ 'data-testid': 'gallery-toggle-community-autogens' }}
                  />
                }
                label="Community auto-gens"
                data-testid="gallery-toggle-community-autogens-label"
              />
            </Stack>
          </Stack>

          <Stack spacing={2} data-testid="gallery-tag-filter-section">
            <Typography variant="h6" component="h2" data-testid="gallery-tag-filter-title">
              Filter by tags
            </Typography>
            <TagFilter
              selectedTags={selectedTags}
              onTagsChange={handleTagFilterChange}
              onTagClick={handleTagClick}
              onNavigateToHierarchy={handleNavigateToHierarchy}
              tagPage={tagFilterPage}
              onTagPageChange={handleTagPageChange}
              tagIdToNameMap={tagIdToNameMap}
            />
          </Stack>

          {/* Virtual Scrolling Toggle - only show if feature is enabled */}
          {virtualScrollingFeatureEnabled && (
            <Box sx={{ mt: 'auto', pt: 2 }} data-testid="gallery-virtual-scrolling-section">
              <FormControlLabel
                control={
                  <Switch
                    checked={useVirtualScrolling}
                    onChange={(e) => setUseVirtualScrolling(e.target.checked)}
                    size="small"
                    inputProps={{ 'data-testid': 'gallery-virtual-scroll-toggle' }}
                  />
                }
                label="Virtual Scrolling"
                sx={{ ml: 1 }}
                data-testid="gallery-virtual-scroll-toggle-label"
              />
            </Box>
          )}
        </Stack>
      </Drawer>

      {/* Gen Source Info Popper */}
      <Popper
        open={Boolean(genSourceInfoAnchorEl)}
        anchorEl={genSourceInfoAnchorEl}
        placement="bottom"
        modifiers={[{ name: 'offset', options: { offset: [0, 8] } }]}
        sx={{
          pointerEvents: 'none',
          zIndex: (theme) => theme.zIndex.tooltip,
        }}
        data-testid="gallery-gen-source-info-popover"
      >
        <Paper
          elevation={3}
          onMouseEnter={() => setGenSourceInfoAnchorEl(genSourceInfoAnchorEl)}
          onMouseLeave={() => setGenSourceInfoAnchorEl(null)}
          sx={{
            p: 1.5,
            pointerEvents: 'auto',
            maxWidth: 300,
          }}
        >
          <Typography variant="body2" color="text.secondary">
            Choose which types of content to include in your gallery view.
          </Typography>
        </Paper>
      </Popper>

      {/* Stats Popper */}
      <Popper
        open={Boolean(statsAnchorEl)}
        anchorEl={statsAnchorEl}
        placement="bottom"
        modifiers={[{ name: 'offset', options: { offset: [0, 8] } }]}
        sx={{
          pointerEvents: 'none',
          zIndex: (theme) => theme.zIndex.tooltip,
        }}
        data-testid="gallery-stats-popover"
      >
        <Paper
          elevation={3}
          onMouseEnter={() => setStatsAnchorEl(statsAnchorEl)}
          onMouseLeave={() => setStatsAnchorEl(null)}
          sx={{
            p: 1.5,
            pointerEvents: 'auto',
          }}
        >
          {stats ? (
            <Stack spacing={1} data-testid="gallery-stats-list">
              <Typography variant="body2" color="text.secondary" data-testid="gallery-stats-user-regular">
                Your gens: {stats.userRegularCount.toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary" data-testid="gallery-stats-user-auto">
                Your auto-gens: {stats.userAutoCount.toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary" data-testid="gallery-stats-community-regular">
                Community gens: {stats.communityRegularCount.toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary" data-testid="gallery-stats-community-auto">
                Community auto-gens: {stats.communityAutoCount.toLocaleString()}
              </Typography>
            </Stack>
          ) : (
            <Typography variant="body2" color="text.secondary" data-testid="gallery-stats-loading">
              Loading stats...
            </Typography>
          )}
        </Paper>
      </Popper>

      {/* Invalid Tags Error Notification */}
      <Snackbar
        open={showInvalidTagError}
        autoHideDuration={8000}
        onClose={() => setShowInvalidTagError(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        data-testid="gallery-invalid-tags-snackbar"
      >
        <Alert
          elevation={6}
          variant="filled"
          severity="error"
          onClose={() => setShowInvalidTagError(false)}
          data-testid="gallery-invalid-tags-alert"
        >
          <Typography variant="subtitle2" component="div" sx={{ mb: 1 }}>
            Invalid tags in URL
          </Typography>
          <Typography variant="body2" component="div" sx={{ mb: 1 }}>
            The following {invalidTagNames.length === 1 ? 'tag does' : 'tags do'} not exist in the database and {invalidTagNames.length === 1 ? 'has' : 'have'} no effect:
          </Typography>
          <Box component="ul" sx={{ margin: 0, paddingLeft: 2 }}>
            {invalidTagNames.map((tagName) => (
              <li key={tagName}>
                <Typography variant="body2" component="span">
                  {tagName}
                </Typography>
              </li>
            ))}
          </Box>
        </Alert>
      </Snackbar>
    </Box>
  )
}

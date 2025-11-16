import { useState, useEffect, useMemo, useCallback } from 'react'
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom'
import {
  Box,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Stack,
  Skeleton,
  Alert,
  Breadcrumbs,
  Link,
  Pagination,
  type SelectChangeEvent,
} from '@mui/material'
import NavigateNextIcon from '@mui/icons-material/NavigateNext'
import PublicIcon from '@mui/icons-material/Public'
import PublicOffIcon from '@mui/icons-material/PublicOff'
import EditIcon from '@mui/icons-material/Edit'
import SwapVertIcon from '@mui/icons-material/SwapVert'
import {
  useCurrentUser,
  useBookmarkCategories,
  useCategoryBookmarks,
  useUpdateCategory,
  useDeleteCategory,
} from '../../hooks'
import { GridView, ResolutionDropdown, ImageGridCell } from '../../components/gallery'
import { CategoryEditDeleteDialog } from '../../components/bookmarks'
import { useDebounce } from '../../hooks'
import type {
  BookmarkCategory,
  BookmarkCategoryUpdateRequest,
  GalleryItem,
  ThumbnailResolution,
  ThumbnailResolutionId,
} from '../../types/domain'
import { THUMBNAIL_RESOLUTION_OPTIONS } from '../../constants/gallery'

// Storage keys
const CATEGORY_PAGE_ITEMS_SORT_KEY = 'bookmarks-category-page-items-sort'
const CATEGORY_PAGE_ITEMS_PER_PAGE_KEY = 'bookmarks-category-page-items-per-page'
const CATEGORY_PAGE_RESOLUTION_KEY = 'bookmarks-category-page-resolution'

// Sort options
type ItemsSortField = 'user_rating_datetime' | 'user_rating' | 'quality_score' | 'created_at' | 'title'
type SortOrder = 'asc' | 'desc'

interface ItemsSortOption {
  field: ItemsSortField
  order: SortOrder
}

const itemsSortOptions: Array<{ value: ItemsSortField; label: string }> = [
  { value: 'user_rating_datetime', label: "Your Rating > Date Added" },
  { value: 'user_rating', label: "Your Rating" },
  { value: 'quality_score', label: "Quality Score" },
  { value: 'created_at', label: "Date Created" },
  { value: 'title', label: "Title (A-Z)" },
]

const itemsPerPageOptions = [25, 50, 75, 100]

/**
 * BookmarksCategoryPage - Single category view with full bookmark list
 *
 * Displays all bookmarks in a specific category with pagination,
 * sorting options, and grid resolution controls.
 */
export function BookmarksCategoryPage() {
  const { categoryId } = useParams<{ categoryId: string }>()
  const navigate = useNavigate()
  const { data: currentUser } = useCurrentUser()
  const userId = currentUser?.id || ''

  // Navigate to detail view
  const navigateToDetail = (item: GalleryItem) => {
    navigate(`/view/${item.id}`, {
      state: {
        sourceType: item.sourceType,
        from: 'bookmarks-category',
        fallbackPath: `/bookmarks/${categoryId}`,
      },
    })
  }

  // Load preferences from localStorage
  const [itemsSort, setItemsSort] = useState<ItemsSortOption>(() => {
    try {
      const stored = localStorage.getItem(CATEGORY_PAGE_ITEMS_SORT_KEY)
      return stored ? JSON.parse(stored) : { field: 'user_rating_datetime', order: 'desc' }
    } catch {
      return { field: 'user_rating_datetime', order: 'desc' }
    }
  })

  const [itemsPerPage, setItemsPerPage] = useState<number>(() => {
    try {
      const stored = localStorage.getItem(CATEGORY_PAGE_ITEMS_PER_PAGE_KEY)
      return stored ? JSON.parse(stored) : 50
    } catch {
      return 50
    }
  })

  const [resolutionId, setResolutionId] = useState<ThumbnailResolutionId>(() => {
    try {
      const stored = localStorage.getItem(CATEGORY_PAGE_RESOLUTION_KEY)
      return stored ? JSON.parse(stored) : '184x272'
    } catch {
      return '184x272'
    }
  })

  const [page, setPage] = useState(0)
  const [modalOpen, setModalOpen] = useState(false)
  const [isPublicState, setIsPublicState] = useState(false)

  const resolution: ThumbnailResolution = useMemo(() => {
    return THUMBNAIL_RESOLUTION_OPTIONS.find((r) => r.id === resolutionId) || THUMBNAIL_RESOLUTION_OPTIONS[0]
  }, [resolutionId])

  // Fetch category details
  const { data: categoriesData } = useBookmarkCategories(userId, {})
  const category = categoriesData?.items.find((c) => c.id === categoryId)

  // Fetch bookmarks for this category
  const {
    data: bookmarksData,
    isLoading: bookmarksLoading,
    isError: bookmarksError,
  } = useCategoryBookmarks(categoryId || '', userId, {
    skip: page * itemsPerPage,
    limit: itemsPerPage,
    sortField: itemsSort.field,
    sortOrder: itemsSort.order,
  })

  const bookmarks = bookmarksData?.items || []
  const totalBookmarks = bookmarksData?.total || 0
  const totalPages = Math.ceil(totalBookmarks / itemsPerPage)

  // Mutations
  const updateCategoryMutation = useUpdateCategory()
  const deleteCategoryMutation = useDeleteCategory()

  // Update local public state when category loads
  useEffect(() => {
    if (category) {
      setIsPublicState(category.isPublic)
    }
  }, [category])

  // Persist preferences to localStorage
  useEffect(() => {
    localStorage.setItem(CATEGORY_PAGE_ITEMS_SORT_KEY, JSON.stringify(itemsSort))
  }, [itemsSort])

  useEffect(() => {
    localStorage.setItem(CATEGORY_PAGE_ITEMS_PER_PAGE_KEY, JSON.stringify(itemsPerPage))
  }, [itemsPerPage])

  useEffect(() => {
    localStorage.setItem(CATEGORY_PAGE_RESOLUTION_KEY, JSON.stringify(resolutionId))
  }, [resolutionId])

  // Debounced public toggle
  const debouncedPublicToggle = useDebounce((newValue: boolean) => {
    if (category && categoryId) {
      updateCategoryMutation.mutate({
        categoryId,
        userId,
        data: { isPublic: newValue },
      })
    }
  }, 500)

  // Handlers
  const handlePublicToggle = useCallback(() => {
    const newValue = !isPublicState
    setIsPublicState(newValue)
    debouncedPublicToggle(newValue)
  }, [isPublicState, debouncedPublicToggle])

  const handleEditCategory = () => {
    setModalOpen(true)
  }

  const handleModalClose = () => {
    setModalOpen(false)
  }

  const handleUpdate = (categoryId: string, data: BookmarkCategoryUpdateRequest) => {
    updateCategoryMutation.mutate(
      { categoryId, userId, data },
      {
        onSuccess: () => {
          setModalOpen(false)
        },
      }
    )
  }

  const handleDelete = (categoryId: string, targetCategoryId: string | null, deleteAll: boolean) => {
    deleteCategoryMutation.mutate(
      {
        categoryId,
        userId,
        targetCategoryId,
        deleteAll,
      },
      {
        onSuccess: () => {
          setModalOpen(false)
          // Navigation to /bookmarks is handled by CategoryEditDeleteDialog
        },
      }
    )
  }

  const handleItemsSortFieldChange = (event: SelectChangeEvent) => {
    setItemsSort((prev) => ({ ...prev, field: event.target.value as ItemsSortField }))
    setPage(0) // Reset to first page when sorting changes
  }

  const handleItemsSortOrderToggle = () => {
    setItemsSort((prev) => ({ ...prev, order: prev.order === 'asc' ? 'desc' : 'asc' }))
    setPage(0)
  }

  const handleItemsPerPageChange = (event: SelectChangeEvent) => {
    setItemsPerPage(Number(event.target.value))
    setPage(0) // Reset to first page when items per page changes
  }

  const handleResolutionChange = (newResolutionId: ThumbnailResolutionId) => {
    setResolutionId(newResolutionId)
  }

  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value - 1) // MUI Pagination is 1-indexed
  }

  // Handle category not found
  if (!categoryId) {
    return (
      <Box data-testid="bookmarks-category-page-root" sx={{ p: 3 }}>
        <Alert severity="error" data-testid="bookmarks-category-page-error">
          Category ID is missing.
        </Alert>
      </Box>
    )
  }

  // Loading state while fetching category
  if (!category && !categoriesData) {
    return (
      <Box data-testid="bookmarks-category-page-root" sx={{ p: 3 }}>
        <Skeleton variant="text" width={200} height={40} />
        <Skeleton variant="rectangular" width="100%" height={400} sx={{ mt: 2 }} />
      </Box>
    )
  }

  // Category not found (404)
  if (categoriesData && !category) {
    return (
      <Box data-testid="bookmarks-category-page-root" sx={{ p: 3 }}>
        <Breadcrumbs
          separator={<NavigateNextIcon fontSize="small" />}
          sx={{ mb: 3 }}
          data-testid="bookmarks-category-page-breadcrumbs"
        >
          <Link
            component={RouterLink}
            to="/bookmarks"
            underline="hover"
            color="inherit"
            data-testid="bookmarks-category-page-breadcrumb-bookmarks"
          >
            Bookmarks
          </Link>
          <Typography color="text.primary">Not Found</Typography>
        </Breadcrumbs>

        <Alert severity="error" data-testid="bookmarks-category-page-not-found">
          Category not found. It may have been deleted or you don't have access to it.
        </Alert>
      </Box>
    )
  }

  // Render main content (no separate error state - just show empty state if fetch fails)
  return (
    <Box data-testid="bookmarks-category-page-root" sx={{ p: 3 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs
        separator={<NavigateNextIcon fontSize="small" />}
        sx={{ mb: 3 }}
        data-testid="bookmarks-category-page-breadcrumbs"
      >
        <Link
          component={RouterLink}
          to="/bookmarks"
          underline="hover"
          color="inherit"
          data-testid="bookmarks-category-page-breadcrumb-bookmarks"
        >
          Bookmarks
        </Link>
        <Typography color="text.primary" data-testid="bookmarks-category-page-breadcrumb-category">
          {category?.name}
        </Typography>
      </Breadcrumbs>

      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }} data-testid="bookmarks-category-page-header">
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" component="h1" gutterBottom data-testid="bookmarks-category-page-title">
              {category?.name}
            </Typography>
            {category?.description && (
              <Typography variant="body2" color="text.secondary" data-testid="bookmarks-category-page-description">
                {category.description}
              </Typography>
            )}
          </Box>

          {/* Toolbar */}
          <Box sx={{ display: 'flex', gap: 0.5, ml: 2 }} data-testid="bookmarks-category-page-toolbar">
            {/* Public/Private Toggle */}
            <Tooltip
              title={isPublicState ? 'Currently: Public - Click to make private' : 'Currently: Private - Click to make public'}
              arrow
            >
              <IconButton
                onClick={handlePublicToggle}
                size="small"
                color={isPublicState ? 'primary' : 'default'}
                data-testid="bookmarks-category-page-public-toggle"
                aria-label={isPublicState ? 'Make category private' : 'Make category public'}
              >
                {isPublicState ? <PublicIcon /> : <PublicOffIcon />}
              </IconButton>
            </Tooltip>

            {/* Edit Button - Hidden for Uncategorized */}
            {category?.name !== 'Uncategorized' && (
              <Tooltip title="Edit category" arrow>
                <IconButton
                  onClick={handleEditCategory}
                  size="small"
                  data-testid="bookmarks-category-page-edit-button"
                  aria-label="Edit category"
                >
                  <EditIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>
      </Paper>

      {/* Controls */}
      <Paper sx={{ p: 2, mb: 3 }} data-testid="bookmarks-category-page-controls">
        <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap alignItems="center">
          {/* Items Sort */}
          <FormControl size="small" sx={{ minWidth: 220 }} data-testid="bookmarks-category-page-items-sort-control">
            <InputLabel id="items-sort-label">Sort By</InputLabel>
            <Select
              labelId="items-sort-label"
              value={itemsSort.field}
              label="Sort By"
              onChange={handleItemsSortFieldChange}
              data-testid="bookmarks-category-page-items-sort-select"
            >
              {itemsSortOptions.map((option) => (
                <MenuItem
                  key={option.value}
                  value={option.value}
                  data-testid={`bookmarks-category-page-items-sort-option-${option.value}`}
                >
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Tooltip title={itemsSort.order === 'asc' ? 'Ascending' : 'Descending'}>
            <IconButton
              onClick={handleItemsSortOrderToggle}
              size="small"
              color={itemsSort.order === 'asc' ? 'primary' : 'default'}
              data-testid="bookmarks-category-page-items-sort-order-toggle"
              aria-label={`Sort order: ${itemsSort.order === 'asc' ? 'ascending' : 'descending'}`}
            >
              <SwapVertIcon />
            </IconButton>
          </Tooltip>

          {/* Items Per Page */}
          <FormControl size="small" sx={{ minWidth: 140 }} data-testid="bookmarks-category-page-items-per-page-control">
            <InputLabel id="items-per-page-label">Items/Page</InputLabel>
            <Select
              labelId="items-per-page-label"
              value={String(itemsPerPage)}
              label="Items/Page"
              onChange={handleItemsPerPageChange}
              data-testid="bookmarks-category-page-items-per-page-select"
            >
              {itemsPerPageOptions.map((value) => (
                <MenuItem
                  key={value}
                  value={String(value)}
                  data-testid={`bookmarks-category-page-items-per-page-option-${value}`}
                >
                  {value}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Resolution Dropdown */}
          <ResolutionDropdown
            currentResolution={resolutionId}
            onResolutionChange={handleResolutionChange}
            dataTestId="bookmarks-category-page-resolution-dropdown"
          />
        </Stack>
      </Paper>

      {/* Grid View */}
      {bookmarksLoading ? (
        <GridView
          items={[]}
          resolution={resolution}
          isLoading={true}
          loadingPlaceholderCount={itemsPerPage}
          dataTestId="bookmarks-category-page-grid"
        />
      ) : bookmarks.length === 0 ? (
        <Paper sx={{ p: 6, textAlign: 'center' }} data-testid="bookmarks-category-page-empty">
          <Typography variant="h6" color="text.secondary" gutterBottom>
            0 bookmarks in category.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Bookmarks you add to "{category?.name}" will appear here
          </Typography>
        </Paper>
      ) : (
        <Box data-testid="bookmarks-category-page-grid-container">
          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: `repeat(auto-fill, minmax(${resolution.width}px, 1fr))`,
              alignItems: 'flex-start',
            }}
            data-testid="bookmarks-category-page-grid"
          >
            {bookmarks.map((bookmark) =>
              bookmark.content ? (
                <ImageGridCell
                  key={bookmark.id}
                  item={bookmark.content}
                  resolution={resolution}
                  onClick={navigateToDetail}
                  dataTestId={`bookmarks-category-page-item-${bookmark.content.id}`}
                />
              ) : null
            )}
          </Box>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box
              sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}
              data-testid="bookmarks-category-page-pagination"
            >
              <Pagination
                count={totalPages}
                page={page + 1}
                onChange={handlePageChange}
                color="primary"
                showFirstButton
                showLastButton
                data-testid="bookmarks-category-page-pagination-control"
              />
            </Box>
          )}
        </Box>
      )}

      {/* Category Edit/Delete Dialog */}
      {category && categoriesData && (
        <CategoryEditDeleteDialog
          open={modalOpen}
          onClose={handleModalClose}
          category={category}
          categories={categoriesData.items}
          userId={userId}
          onUpdate={handleUpdate}
          onDelete={handleDelete}
          isUpdating={updateCategoryMutation.isPending}
          isDeleting={deleteCategoryMutation.isPending}
          redirectAfterDelete={true}
          dataTestId="bookmarks-category-page-category-dialog"
        />
      )}
    </Box>
  )
}

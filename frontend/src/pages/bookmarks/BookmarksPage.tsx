import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Button,
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
  type SelectChangeEvent,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import SwapVertIcon from '@mui/icons-material/SwapVert'
import {
  useCurrentUser,
  useBookmarkCategories,
  useCategoryBookmarks,
  useCreateCategory,
  useUpdateCategory,
  useDeleteCategory,
} from '../../hooks'
import { CategorySection, CategoryFormModal, CategoryEditDeleteDialog } from '../../components/bookmarks'
import type {
  BookmarkCategory,
  BookmarkCategoryCreateRequest,
  BookmarkCategoryUpdateRequest,
  GalleryItem,
  ThumbnailResolution,
} from '../../types/domain'
import { THUMBNAIL_RESOLUTION_OPTIONS } from '../../constants/gallery'

// Storage keys
const BOOKMARKS_CATEGORY_SORT_KEY = 'bookmarks-category-sort'
const BOOKMARKS_ITEMS_SORT_KEY = 'bookmarks-items-sort'
const BOOKMARKS_ITEMS_PER_PAGE_KEY = 'bookmarks-items-per-page'

// Sort options
type CategorySortField = 'updated_at' | 'created_at' | 'name'
type ItemsSortField = 'user_rating_datetime' | 'user_rating' | 'quality_score' | 'created_at' | 'title'
type SortOrder = 'asc' | 'desc'

interface CategorySortOption {
  field: CategorySortField
  order: SortOrder
}

interface ItemsSortOption {
  field: ItemsSortField
  order: SortOrder
}

const categorySortOptions: Array<{ value: CategorySortField; label: string }> = [
  { value: 'updated_at', label: 'Last Updated' },
  { value: 'created_at', label: 'Date Created' },
  { value: 'name', label: 'Alphabetical' },
]

const itemsSortOptions: Array<{ value: ItemsSortField; label: string }> = [
  { value: 'user_rating_datetime', label: "Your Rating > Date Added" },
  { value: 'user_rating', label: "Your Rating" },
  { value: 'quality_score', label: "Quality Score" },
  { value: 'created_at', label: "Date Created" },
  { value: 'title', label: "Title (A-Z)" },
]

const itemsPerPageOptions = [10, 15, 20, 25, 30]

/**
 * BookmarksPage - Main bookmarks view showing all categories
 *
 * Displays all bookmark categories as sections with grid views.
 * Each section shows up to N bookmarks (configurable) with a "More..." cell for navigation.
 */
export function BookmarksPage() {
  const navigate = useNavigate()
  const { data: currentUser } = useCurrentUser()
  const userId = currentUser?.id || ''

  // Navigate to detail view
  const navigateToDetail = (item: GalleryItem) => {
    navigate(`/view/${item.id}`, {
      state: {
        sourceType: item.sourceType,
        from: 'bookmarks',
        fallbackPath: '/bookmarks',
      },
    })
  }

  // Load preferences from localStorage
  const [categorySort, setCategorySort] = useState<CategorySortOption>(() => {
    try {
      const stored = localStorage.getItem(BOOKMARKS_CATEGORY_SORT_KEY)
      return stored ? JSON.parse(stored) : { field: 'updated_at', order: 'desc' }
    } catch {
      return { field: 'updated_at', order: 'desc' }
    }
  })

  const [itemsSort, setItemsSort] = useState<ItemsSortOption>(() => {
    try {
      const stored = localStorage.getItem(BOOKMARKS_ITEMS_SORT_KEY)
      return stored ? JSON.parse(stored) : { field: 'user_rating_datetime', order: 'desc' }
    } catch {
      return { field: 'user_rating_datetime', order: 'desc' }
    }
  })

  const [itemsPerPage, setItemsPerPage] = useState<number>(() => {
    try {
      const stored = localStorage.getItem(BOOKMARKS_ITEMS_PER_PAGE_KEY)
      return stored ? JSON.parse(stored) : 15
    } catch {
      return 15
    }
  })

  // Modal state
  const [modalOpen, setModalOpen] = useState(false)
  const [editingCategory, setEditingCategory] = useState<BookmarkCategory | null>(null)

  // Default resolution for grid view (184x272 as specified in requirements)
  const defaultResolution: ThumbnailResolution = useMemo(() => {
    return THUMBNAIL_RESOLUTION_OPTIONS.find((r) => r.id === '184x272') || THUMBNAIL_RESOLUTION_OPTIONS[0]
  }, [])

  // Fetch categories
  const {
    data: categoriesData,
    isLoading: categoriesLoading,
    isError: categoriesError,
  } = useBookmarkCategories(userId, {
    sortField: categorySort.field,
    sortOrder: categorySort.order,
  })

  const categories = categoriesData?.items || []

  // Separate "Uncategorized" and always show it first
  const sortedCategories = useMemo(() => {
    const uncategorized = categories.find((cat) => cat.name === 'Uncategorized')
    const others = categories.filter((cat) => cat.name !== 'Uncategorized')

    // If Uncategorized exists, put it first, otherwise just return others
    return uncategorized ? [uncategorized, ...others] : others
  }, [categories])

  // Mutations
  const createCategoryMutation = useCreateCategory()
  const updateCategoryMutation = useUpdateCategory()
  const deleteCategoryMutation = useDeleteCategory()

  // Persist preferences to localStorage
  useEffect(() => {
    localStorage.setItem(BOOKMARKS_CATEGORY_SORT_KEY, JSON.stringify(categorySort))
  }, [categorySort])

  useEffect(() => {
    localStorage.setItem(BOOKMARKS_ITEMS_SORT_KEY, JSON.stringify(itemsSort))
  }, [itemsSort])

  useEffect(() => {
    localStorage.setItem(BOOKMARKS_ITEMS_PER_PAGE_KEY, JSON.stringify(itemsPerPage))
  }, [itemsPerPage])

  // Handlers
  const handleCategorySortFieldChange = (event: SelectChangeEvent) => {
    setCategorySort((prev) => ({ ...prev, field: event.target.value as CategorySortField }))
  }

  const handleCategorySortOrderToggle = () => {
    setCategorySort((prev) => ({ ...prev, order: prev.order === 'asc' ? 'desc' : 'asc' }))
  }

  const handleItemsSortFieldChange = (event: SelectChangeEvent) => {
    setItemsSort((prev) => ({ ...prev, field: event.target.value as ItemsSortField }))
  }

  const handleItemsSortOrderToggle = () => {
    setItemsSort((prev) => ({ ...prev, order: prev.order === 'asc' ? 'desc' : 'asc' }))
  }

  const handleItemsPerPageChange = (event: SelectChangeEvent) => {
    setItemsPerPage(Number(event.target.value))
  }

  const handleAddCategory = () => {
    setEditingCategory(null)
    setModalOpen(true)
  }

  const handleEditCategory = (category: BookmarkCategory) => {
    setEditingCategory(category)
    setModalOpen(true)
  }

  const handleModalClose = () => {
    setModalOpen(false)
    setEditingCategory(null)
  }

  const handleCreateSubmit = (data: BookmarkCategoryCreateRequest) => {
    createCategoryMutation.mutate(
      { userId, data },
      {
        onSuccess: () => {
          setModalOpen(false)
        },
      }
    )
  }

  const handleUpdate = (categoryId: string, data: BookmarkCategoryUpdateRequest) => {
    updateCategoryMutation.mutate(
      { categoryId, userId, data },
      {
        onSuccess: () => {
          setModalOpen(false)
          setEditingCategory(null)
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
          setEditingCategory(null)
        },
      }
    )
  }

  const handlePublicToggle = (categoryId: string, isPublic: boolean) => {
    updateCategoryMutation.mutate({
      categoryId,
      userId,
      data: { isPublic },
    })
  }

  // Render loading state
  if (categoriesLoading) {
    return (
      <Box data-testid="bookmarks-page-root" sx={{ p: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom data-testid="bookmarks-page-title">
          Bookmarks
        </Typography>
        <Stack spacing={2} sx={{ mt: 3 }} data-testid="bookmarks-page-loading">
          {[1, 2, 3].map((i) => (
            <Paper key={i} sx={{ p: 3 }}>
              <Skeleton variant="text" width={200} height={40} />
              <Skeleton variant="rectangular" width="100%" height={200} sx={{ mt: 2 }} />
            </Paper>
          ))}
        </Stack>
      </Box>
    )
  }

  // Render error state
  if (categoriesError) {
    return (
      <Box data-testid="bookmarks-page-root" sx={{ p: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom data-testid="bookmarks-page-title">
          Bookmarks
        </Typography>
        <Alert severity="error" data-testid="bookmarks-page-error" sx={{ mt: 2 }}>
          Failed to load bookmark categories. Please try again later.
        </Alert>
      </Box>
    )
  }

  // Render empty state
  if (sortedCategories.length === 0) {
    return (
      <Box data-testid="bookmarks-page-root" sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1" data-testid="bookmarks-page-title">
            Bookmarks
          </Typography>
        </Box>

        <Paper sx={{ p: 6, textAlign: 'center' }} data-testid="bookmarks-page-empty">
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No bookmark categories yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Create your first category to start organizing your bookmarks
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAddCategory}
            data-testid="bookmarks-page-add-category-empty"
          >
            Create Category
          </Button>
        </Paper>

        <CategoryFormModal
          open={modalOpen}
          onClose={handleModalClose}
          onSubmit={handleCreateSubmit}
          mode="create"
          isSubmitting={createCategoryMutation.isPending}
          dataTestId="bookmarks-page-category-modal"
        />
      </Box>
    )
  }

  // Render main content
  return (
    <Box data-testid="bookmarks-page-root" sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" data-testid="bookmarks-page-title">
          Bookmarks
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddCategory}
          data-testid="bookmarks-page-add-category-button"
        >
          Add Category
        </Button>
      </Box>

      {/* Controls */}
      <Paper sx={{ p: 2, mb: 3 }} data-testid="bookmarks-page-controls">
        <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
          {/* Category Sort */}
          <FormControl size="small" sx={{ minWidth: 180 }} data-testid="bookmarks-page-category-sort-control">
            <InputLabel id="category-sort-label">Category Sort</InputLabel>
            <Select
              labelId="category-sort-label"
              value={categorySort.field}
              label="Category Sort"
              onChange={handleCategorySortFieldChange}
              data-testid="bookmarks-page-category-sort-select"
            >
              {categorySortOptions.map((option) => (
                <MenuItem key={option.value} value={option.value} data-testid={`bookmarks-page-category-sort-option-${option.value}`}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Tooltip title={categorySort.order === 'asc' ? 'Ascending' : 'Descending'}>
            <IconButton
              onClick={handleCategorySortOrderToggle}
              size="small"
              color={categorySort.order === 'asc' ? 'primary' : 'default'}
              data-testid="bookmarks-page-category-sort-order-toggle"
              aria-label={`Sort order: ${categorySort.order === 'asc' ? 'ascending' : 'descending'}`}
            >
              <SwapVertIcon />
            </IconButton>
          </Tooltip>

          {/* Items Sort */}
          <FormControl size="small" sx={{ minWidth: 220 }} data-testid="bookmarks-page-items-sort-control">
            <InputLabel id="items-sort-label">Items Sort</InputLabel>
            <Select
              labelId="items-sort-label"
              value={itemsSort.field}
              label="Items Sort"
              onChange={handleItemsSortFieldChange}
              data-testid="bookmarks-page-items-sort-select"
            >
              {itemsSortOptions.map((option) => (
                <MenuItem key={option.value} value={option.value} data-testid={`bookmarks-page-items-sort-option-${option.value}`}>
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
              data-testid="bookmarks-page-items-sort-order-toggle"
              aria-label={`Sort order: ${itemsSort.order === 'asc' ? 'ascending' : 'descending'}`}
            >
              <SwapVertIcon />
            </IconButton>
          </Tooltip>

          {/* Items Per Page */}
          <FormControl size="small" sx={{ minWidth: 140 }} data-testid="bookmarks-page-items-per-page-control">
            <InputLabel id="items-per-page-label">Items/Page</InputLabel>
            <Select
              labelId="items-per-page-label"
              value={String(itemsPerPage)}
              label="Items/Page"
              onChange={handleItemsPerPageChange}
              data-testid="bookmarks-page-items-per-page-select"
            >
              {itemsPerPageOptions.map((value) => (
                <MenuItem key={value} value={String(value)} data-testid={`bookmarks-page-items-per-page-option-${value}`}>
                  {value}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
      </Paper>

      {/* Category Sections */}
      <Stack spacing={3} data-testid="bookmarks-page-categories">
        {sortedCategories.map((category) => (
          <CategorySectionWithBookmarks
            key={category.id}
            category={category}
            userId={userId}
            itemsPerPage={itemsPerPage}
            itemsSort={itemsSort}
            resolution={defaultResolution}
            onPublicToggle={handlePublicToggle}
            onEditCategory={handleEditCategory}
            onItemClick={navigateToDetail}
          />
        ))}
      </Stack>

      {/* Category Create/Edit/Delete Modals */}
      {editingCategory ? (
        <CategoryEditDeleteDialog
          open={modalOpen}
          onClose={handleModalClose}
          category={editingCategory}
          categories={categories}
          userId={userId}
          onUpdate={handleUpdate}
          onDelete={handleDelete}
          isUpdating={updateCategoryMutation.isPending}
          isDeleting={deleteCategoryMutation.isPending}
          redirectAfterDelete={false}
          dataTestId="bookmarks-page-category-modal"
        />
      ) : (
        <CategoryFormModal
          open={modalOpen}
          onClose={handleModalClose}
          onSubmit={handleCreateSubmit}
          mode="create"
          isSubmitting={createCategoryMutation.isPending}
          dataTestId="bookmarks-page-category-create-modal"
        />
      )}
    </Box>
  )
}

/**
 * CategorySectionWithBookmarks - Wrapper component that fetches bookmarks for a category
 */
interface CategorySectionWithBookmarksProps {
  category: BookmarkCategory
  userId: string
  itemsPerPage: number
  itemsSort: ItemsSortOption
  resolution: ThumbnailResolution
  onPublicToggle: (categoryId: string, isPublic: boolean) => void
  onEditCategory: (category: BookmarkCategory) => void
  onItemClick?: (item: GalleryItem) => void
}

function CategorySectionWithBookmarks({
  category,
  userId,
  itemsPerPage,
  itemsSort,
  resolution,
  onPublicToggle,
  onEditCategory,
  onItemClick,
}: CategorySectionWithBookmarksProps) {
  const { data: bookmarksData, isLoading } = useCategoryBookmarks(category.id, userId, {
    limit: itemsPerPage,
    sortField: itemsSort.field,
    sortOrder: itemsSort.order,
  })

  const bookmarks = bookmarksData?.items || []

  return (
    <CategorySection
      category={category}
      bookmarks={bookmarks}
      resolution={resolution}
      isLoading={isLoading}
      itemsPerPage={itemsPerPage}
      onPublicToggle={onPublicToggle}
      onEditCategory={onEditCategory}
      onItemClick={onItemClick}
      dataTestId={`bookmarks-page-category-${category.id}`}
    />
  )
}

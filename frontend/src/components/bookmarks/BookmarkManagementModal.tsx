import { useState, useEffect, useMemo } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControlLabel,
  Switch,
  Box,
  Typography,
  Autocomplete,
  TextField,
  MenuItem,
  IconButton,
  Tooltip,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import SwapVertIcon from '@mui/icons-material/SwapVert'
import { useBookmarkCategories, useBookmarkMutations } from '../../hooks'
import { bookmarksService } from '../../services'
import type { Bookmark, BookmarkCategory } from '../../types/domain'

export interface BookmarkManagementModalProps {
  open: boolean
  onClose: () => void
  bookmark: Bookmark
  userId: string
  dataTestId?: string
}

/**
 * BookmarkManagementModal - Modal for managing bookmark settings
 *
 * Allows users to:
 * - Toggle public/private status
 * - Manage category memberships
 * - Remove bookmark
 */
export function BookmarkManagementModal({
  open,
  onClose,
  bookmark,
  userId,
  dataTestId = 'bookmark-management-modal',
}: BookmarkManagementModalProps) {
  const [isPublic, setIsPublic] = useState(bookmark.isPublic)
  const [selectedCategories, setSelectedCategories] = useState<BookmarkCategory[]>([])
  const [sortMode, setSortMode] = useState<'updated_at' | 'name'>('updated_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [bookmarkCategories, setBookmarkCategories] = useState<string[]>([])
  const [isLoadingCategories, setIsLoadingCategories] = useState(true)

  const { data: categoriesData, isLoading: categoriesLoading } = useBookmarkCategories(userId)
  const { syncCategories, deleteBookmark } = useBookmarkMutations(userId)

  // Fetch bookmark's current categories on mount
  useEffect(() => {
    if (open && bookmark.id) {
      const fetchBookmarkCategories = async () => {
        try {
          setIsLoadingCategories(true)
          const categoryIds = await bookmarksService.getBookmarkCategories(bookmark.id)
          setBookmarkCategories(categoryIds)
        } catch (error) {
          console.error('Error fetching bookmark categories:', error)
        } finally {
          setIsLoadingCategories(false)
        }
      }

      fetchBookmarkCategories()
    }
  }, [open, bookmark.id])

  // Pre-select categories based on fetched bookmark categories
  useEffect(() => {
    if (!isLoadingCategories && categoriesData && bookmarkCategories.length > 0) {
      const selected = categoriesData.items.filter((cat) =>
        bookmarkCategories.includes(cat.id)
      )
      setSelectedCategories(selected)
    }
  }, [isLoadingCategories, categoriesData, bookmarkCategories])

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      setIsPublic(bookmark.isPublic)
    }
  }, [open, bookmark.isPublic])

  // Sort categories based on current sort mode and order
  const sortedCategories = useMemo(() => {
    if (!categoriesData) return []

    const categories = [...categoriesData.items]
    categories.sort((a, b) => {
      let comparison = 0

      if (sortMode === 'updated_at') {
        const dateA = new Date(a.updatedAt).getTime()
        const dateB = new Date(b.updatedAt).getTime()
        comparison = dateB - dateA // Most recent first by default
      } else {
        // Alphabetical
        comparison = a.name.localeCompare(b.name)
      }

      return sortOrder === 'asc' ? -comparison : comparison
    })

    return categories
  }, [categoriesData, sortMode, sortOrder])

  const handleSave = async () => {
    try {
      const categoryIds = selectedCategories.map((cat) => cat.id)

      await syncCategories.mutateAsync({
        bookmarkId: bookmark.id,
        categoryIds,
      })

      onClose()
    } catch (error) {
      console.error('Error saving bookmark:', error)
    }
  }

  const handleRemove = async () => {
    try {
      await deleteBookmark.mutateAsync({
        bookmarkId: bookmark.id,
        contentId: bookmark.contentId,
        contentSourceType: bookmark.contentSourceType,
      })

      onClose()
    } catch (error) {
      console.error('Error removing bookmark:', error)
    }
  }

  const handleClose = () => {
    if (!syncCategories.isPending && !deleteBookmark.isPending) {
      onClose()
    }
  }

  const toggleSortOrder = () => {
    setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))
  }

  const isSubmitting = syncCategories.isPending || deleteBookmark.isPending
  const isLoading = categoriesLoading || isLoadingCategories

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      disableRestoreFocus
      data-testid={dataTestId}
    >
      <DialogTitle data-testid={`${dataTestId}-title`}>
        Manage Bookmark
      </DialogTitle>
      <DialogContent data-testid={`${dataTestId}-content`}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <FormControlLabel
            control={
              <Switch
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                disabled={isSubmitting}
                data-testid="bookmark-public-toggle"
              />
            }
            label={
              <Box>
                <Typography variant="body2">Public</Typography>
                <Typography variant="caption" color="text.secondary">
                  Public bookmarks have not yet been implemented. As of now, even if you set it to public, all bookmarks will be private.
                </Typography>
              </Box>
            }
            data-testid={`${dataTestId}-public-control`}
          />

          <Box>
            <Box sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
              <TextField
                label="Sort by"
                value={sortMode}
                onChange={(e) => setSortMode(e.target.value as 'updated_at' | 'name')}
                select
                size="small"
                disabled={isSubmitting}
                sx={{ flexGrow: 1 }}
                data-testid="bookmark-categories-sort-dropdown"
              >
                <MenuItem value="updated_at">Recent activity</MenuItem>
                <MenuItem value="name">Alphabetical</MenuItem>
              </TextField>
              <Tooltip title={sortOrder === 'asc' ? 'Ascending' : 'Descending'}>
                <IconButton
                  onClick={toggleSortOrder}
                  size="small"
                  disabled={isSubmitting}
                  data-testid="bookmark-categories-sort-order-toggle"
                  aria-label={`Sort order: ${sortOrder === 'asc' ? 'Ascending' : 'Descending'}`}
                >
                  <SwapVertIcon />
                </IconButton>
              </Tooltip>
            </Box>

            <Autocomplete
              multiple
              options={sortedCategories}
              getOptionLabel={(option) => option.name}
              value={selectedCategories}
              onChange={(_, newValue) => setSelectedCategories(newValue)}
              disabled={isSubmitting || isLoading}
              loading={isLoading}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Categories"
                  placeholder="Select categories"
                  helperText="Leave empty to use 'Uncategorized'"
                />
              )}
              data-testid="bookmark-categories-dropdown"
            />
          </Box>
        </Box>
      </DialogContent>
      <DialogActions
        sx={{ justifyContent: 'space-between', px: 3, pb: 2 }}
        data-testid={`${dataTestId}-actions`}
      >
        {/* Delete button - left side */}
        <Tooltip title="Remove bookmark" arrow>
          <IconButton
            onClick={handleRemove}
            disabled={isSubmitting}
            color="error"
            data-testid="bookmark-remove-button"
            aria-label="Remove bookmark"
          >
            <DeleteIcon />
          </IconButton>
        </Tooltip>

        {/* Right side buttons */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            onClick={handleClose}
            disabled={isSubmitting}
            data-testid="bookmark-cancel-button"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={isSubmitting}
            data-testid="bookmark-save-button"
          >
            Save
          </Button>
        </Box>
      </DialogActions>
    </Dialog>
  )
}

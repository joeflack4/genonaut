import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  Box,
  MenuItem,
  Typography,
  IconButton,
  Tooltip,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import type {
  BookmarkCategory,
  BookmarkCategoryCreateRequest,
  BookmarkCategoryUpdateRequest,
} from '../../types/domain'

export interface CategoryFormModalProps {
  open: boolean
  onClose: () => void
  onSubmit: (data: BookmarkCategoryCreateRequest | BookmarkCategoryUpdateRequest) => void
  onDelete?: () => void  // Optional delete handler (only in edit mode)
  category?: BookmarkCategory | null
  categories?: BookmarkCategory[]  // For parent selection
  mode: 'create' | 'edit'
  isSubmitting?: boolean
  dataTestId?: string
}

/**
 * CategoryFormModal - Modal for creating and editing bookmark categories
 *
 * Supports both create and edit modes with form validation
 */
export function CategoryFormModal({
  open,
  onClose,
  onSubmit,
  onDelete,
  category,
  categories = [],
  mode,
  isSubmitting = false,
  dataTestId = 'category-form-modal',
}: CategoryFormModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isPublic, setIsPublic] = useState(false)
  const [parentId, setParentId] = useState<string>('')
  const [errors, setErrors] = useState<Record<string, string>>({})

  // Initialize form with category data in edit mode
  useEffect(() => {
    if (mode === 'edit' && category) {
      setName(category.name)
      setDescription(category.description || '')
      setIsPublic(category.isPublic)
      setParentId(category.parentId || '')
    } else {
      // Reset form in create mode
      setName('')
      setDescription('')
      setIsPublic(false)
      setParentId('')
    }
    setErrors({})
  }, [mode, category, open])

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!name.trim()) {
      newErrors.name = 'Category name is required'
    } else if (name.trim().length < 2) {
      newErrors.name = 'Category name must be at least 2 characters'
    } else if (name.trim().length > 100) {
      newErrors.name = 'Category name must be less than 100 characters'
    }

    if (description && description.length > 500) {
      newErrors.description = 'Description must be less than 500 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = () => {
    if (!validate()) {
      return
    }

    const formData: BookmarkCategoryCreateRequest | BookmarkCategoryUpdateRequest = {
      name: name.trim(),
      description: description.trim() || undefined,
      isPublic,
      parentId: parentId || undefined,
    }

    onSubmit(formData)
  }

  const handleClose = () => {
    if (!isSubmitting) {
      onClose()
    }
  }

  // Filter out current category and its descendants from parent options (prevent circular references)
  const availableParents = categories.filter((cat) => {
    // Never allow "Uncategorized" as a parent category
    if (cat.name === 'Uncategorized') return false

    if (mode === 'edit' && category) {
      // Can't select self as parent
      if (cat.id === category.id) return false
      // TODO: Also filter out descendants to prevent circular references
      // This would require building a tree structure
    }
    return true
  })

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
        {mode === 'create' ? 'Create Category' : 'Edit Category'}
      </DialogTitle>
      <DialogContent data-testid={`${dataTestId}-content`}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <TextField
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={Boolean(errors.name)}
            helperText={errors.name}
            required
            fullWidth
            autoFocus
            disabled={isSubmitting}
            slotProps={{
              htmlInput: { 'data-testid': `${dataTestId}-name-input` }
            }}
            data-testid={`${dataTestId}-name-field`}
          />

          <TextField
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            error={Boolean(errors.description)}
            helperText={errors.description}
            multiline
            rows={3}
            fullWidth
            disabled={isSubmitting}
            slotProps={{
              htmlInput: { 'data-testid': `${dataTestId}-description-input` }
            }}
            data-testid={`${dataTestId}-description-field`}
          />

          <TextField
            label="Parent Category"
            value={parentId}
            onChange={(e) => setParentId(e.target.value)}
            select
            fullWidth
            disabled={isSubmitting}
            helperText="Optional: Leave blank for top-level category"
            slotProps={{
              select: {
                displayEmpty: true,
              },
              htmlInput: {
                'data-testid': `${dataTestId}-parent-select`,
              }
            }}
            data-testid={`${dataTestId}-parent-field`}
          >
            <MenuItem value="" data-testid={`${dataTestId}-parent-option-none`}>
              None (Top Level)
            </MenuItem>
            {availableParents.map((cat) => (
              <MenuItem
                key={cat.id}
                value={cat.id}
                data-testid={`${dataTestId}-parent-option-${cat.id}`}
              >
                {cat.name}
              </MenuItem>
            ))}
          </TextField>

          <FormControlLabel
            control={
              <Switch
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                disabled={isSubmitting}
                slotProps={{
                  input: { 'data-testid': `${dataTestId}-public-switch` }
                }}
              />
            }
            label={
              <Box>
                <Typography variant="body2">Public</Typography>
                <Typography variant="caption" color="text.secondary">
                  Make this category visible to others
                </Typography>
              </Box>
            }
            data-testid={`${dataTestId}-public-control`}
          />
        </Box>
      </DialogContent>
      <DialogActions
        sx={{ justifyContent: mode === 'edit' && onDelete ? 'space-between' : 'flex-end', px: 3, pb: 2 }}
        data-testid={`${dataTestId}-actions`}
      >
        {/* Delete button - only in edit mode */}
        {mode === 'edit' && onDelete && (
          <Tooltip title="Delete category" arrow>
            <IconButton
              onClick={onDelete}
              disabled={isSubmitting}
              color="error"
              data-testid={`${dataTestId}-delete-button`}
              aria-label="Delete category"
            >
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        )}

        {/* Right side buttons */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            onClick={handleClose}
            disabled={isSubmitting}
            data-testid={`${dataTestId}-cancel-button`}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={isSubmitting}
            data-testid={`${dataTestId}-submit-button`}
          >
            {mode === 'create' ? 'Create' : 'Save'}
          </Button>
        </Box>
      </DialogActions>
    </Dialog>
  )
}

import { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Typography,
  Box,
} from '@mui/material'
import type { BookmarkCategory } from '../../types/domain'

export interface DeleteCategoryConfirmationModalProps {
  open: boolean
  onClose: () => void
  onConfirm: (targetCategoryId: string | null, deleteAll: boolean) => void
  category: BookmarkCategory
  availableCategories: BookmarkCategory[]
  isDeleting?: boolean
  dataTestId?: string
}

/**
 * DeleteCategoryConfirmationModal - Confirmation modal for deleting a category
 *
 * Features:
 * - Option to move bookmarks to another category (default: "Uncategorized")
 * - Option to delete all bookmarks in the category
 * - Alphabetical category list with "Uncategorized" at top
 */
export function DeleteCategoryConfirmationModal({
  open,
  onClose,
  onConfirm,
  category,
  availableCategories,
  isDeleting = false,
  dataTestId = 'delete-category-modal',
}: DeleteCategoryConfirmationModalProps) {
  // Find Uncategorized category
  const uncategorizedCategory = availableCategories.find((cat) => cat.name === 'Uncategorized')

  const [targetCategoryId, setTargetCategoryId] = useState<string>(
    uncategorizedCategory?.id || ''
  )
  const [deleteAll, setDeleteAll] = useState(false)

  // Sort categories: Uncategorized first, then alphabetical
  const sortedCategories = [...availableCategories].sort((a, b) => {
    if (a.name === 'Uncategorized') return -1
    if (b.name === 'Uncategorized') return 1
    return a.name.localeCompare(b.name)
  })

  const handleConfirm = () => {
    onConfirm(deleteAll ? null : targetCategoryId, deleteAll)
  }

  const handleClose = () => {
    if (!isDeleting) {
      onClose()
    }
  }

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
        Delete Category
      </DialogTitle>
      <DialogContent data-testid={`${dataTestId}-content`}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <Typography variant="body2" data-testid={`${dataTestId}-message`}>
            Are you sure you want to delete this category?
            <br />
            All bookmarks will be moved to the category selected below, unless you check "Delete & unbookmark all items."
          </Typography>

          <TextField
            label="Delete and move bookmarks"
            value={targetCategoryId}
            onChange={(e) => setTargetCategoryId(e.target.value)}
            select
            fullWidth
            disabled={isDeleting || deleteAll}
            helperText="Bookmarks will be moved to this category"
            slotProps={{
              htmlInput: {
                'data-testid': `${dataTestId}-target-select`,
              },
            }}
            data-testid={`${dataTestId}-target-field`}
          >
            {sortedCategories.map((cat) => (
              <MenuItem
                key={cat.id}
                value={cat.id}
                data-testid={`${dataTestId}-target-option-${cat.id}`}
              >
                {cat.name}
              </MenuItem>
            ))}
          </TextField>

          <FormControlLabel
            control={
              <Checkbox
                checked={deleteAll}
                onChange={(e) => setDeleteAll(e.target.checked)}
                disabled={isDeleting}
                slotProps={{
                  input: { 'data-testid': `${dataTestId}-delete-all-checkbox` }
                }}
              />
            }
            label="Delete & unbookmark all items."
            data-testid={`${dataTestId}-delete-all-control`}
          />
        </Box>
      </DialogContent>
      <DialogActions
        sx={{ justifyContent: 'center', pb: 2 }}
        data-testid={`${dataTestId}-actions`}
      >
        <Button
          onClick={handleClose}
          disabled={isDeleting}
          data-testid={`${dataTestId}-cancel-button`}
        >
          Cancel
        </Button>
        <Button
          onClick={handleConfirm}
          variant="contained"
          color="error"
          disabled={isDeleting}
          data-testid={`${dataTestId}-confirm-button`}
        >
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  )
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CategoryFormModal } from './CategoryFormModal'
import { DeleteCategoryConfirmationModal } from './DeleteCategoryConfirmationModal'
import type {
  BookmarkCategory,
  BookmarkCategoryUpdateRequest,
} from '../../types/domain'

export interface CategoryEditDeleteDialogProps {
  open: boolean
  onClose: () => void
  category: BookmarkCategory
  categories: BookmarkCategory[]
  userId: string
  onUpdate: (categoryId: string, data: BookmarkCategoryUpdateRequest) => void
  onDelete: (categoryId: string, targetCategoryId: string | null, deleteAll: boolean) => void
  isUpdating?: boolean
  isDeleting?: boolean
  redirectAfterDelete?: boolean  // If true, navigate to /bookmarks after delete
  dataTestId?: string
}

/**
 * CategoryEditDeleteDialog - Shared component for editing and deleting categories
 *
 * Combines CategoryFormModal and DeleteCategoryConfirmationModal with shared logic.
 * Used by both BookmarksPage and BookmarksCategoryPage.
 *
 * Features:
 * - Edit category details
 * - Delete category with confirmation
 * - Optional redirect after deletion
 */
export function CategoryEditDeleteDialog({
  open,
  onClose,
  category,
  categories,
  userId,
  onUpdate,
  onDelete,
  isUpdating = false,
  isDeleting = false,
  redirectAfterDelete = false,
  dataTestId = 'category-edit-delete-dialog',
}: CategoryEditDeleteDialogProps) {
  const navigate = useNavigate()
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)

  const handleUpdate = (data: BookmarkCategoryUpdateRequest) => {
    onUpdate(category.id, data)
  }

  const handleDeleteClick = () => {
    setDeleteModalOpen(true)
  }

  const handleDeleteModalClose = () => {
    setDeleteModalOpen(false)
  }

  const handleDeleteConfirm = (targetCategoryId: string | null, deleteAll: boolean) => {
    onDelete(category.id, targetCategoryId, deleteAll)

    // Close both modals
    setDeleteModalOpen(false)

    // Optionally redirect after delete
    if (redirectAfterDelete) {
      navigate('/bookmarks')
    }
  }

  // Filter out current category from available targets
  const availableCategories = categories.filter((cat) => cat.id !== category.id)

  return (
    <>
      {/* Edit Modal */}
      <CategoryFormModal
        open={open}
        onClose={onClose}
        onSubmit={handleUpdate}
        onDelete={handleDeleteClick}
        category={category}
        categories={categories}
        mode="edit"
        isSubmitting={isUpdating}
        dataTestId={dataTestId}
      />

      {/* Delete Confirmation Modal */}
      <DeleteCategoryConfirmationModal
        open={deleteModalOpen}
        onClose={handleDeleteModalClose}
        onConfirm={handleDeleteConfirm}
        category={category}
        availableCategories={availableCategories}
        isDeleting={isDeleting}
        dataTestId={`${dataTestId}-delete`}
      />
    </>
  )
}

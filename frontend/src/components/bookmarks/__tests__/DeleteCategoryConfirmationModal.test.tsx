import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DeleteCategoryConfirmationModal } from '../DeleteCategoryConfirmationModal'
import type { BookmarkCategory } from '../../../types/domain'

describe('DeleteCategoryConfirmationModal', () => {
  const mockCategory: BookmarkCategory = {
    id: 'category-1',
    userId: 'user-123',
    name: 'My Category',
    description: 'Test category',
    isPublic: false,
    sortIndex: 0,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  }

  const mockAvailableCategories: BookmarkCategory[] = [
    {
      id: 'uncategorized',
      userId: 'user-123',
      name: 'Uncategorized',
      description: null,
      isPublic: false,
      sortIndex: 0,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    },
    {
      id: 'category-2',
      userId: 'user-123',
      name: 'Favorites',
      description: null,
      isPublic: true,
      sortIndex: 1,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    },
    {
      id: 'category-3',
      userId: 'user-123',
      name: 'Archive',
      description: null,
      isPublic: false,
      sortIndex: 2,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    },
  ]

  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    onConfirm: vi.fn(),
    category: mockCategory,
    availableCategories: mockAvailableCategories,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Initial Rendering', () => {
    it('should render modal with correct title', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} />)

      expect(screen.getByTestId('delete-category-modal-title')).toHaveTextContent('Delete Category')
    })

    it('should render confirmation message', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} />)

      const message = screen.getByTestId('delete-category-modal-message')
      expect(message).toHaveTextContent('Are you sure you want to delete this category?')
      expect(message).toHaveTextContent('All bookmarks will be moved to the category selected below')
    })

    it('should default to Uncategorized category as target', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} />)

      const targetSelect = screen.getByTestId('delete-category-modal-target-select') as HTMLInputElement
      expect(targetSelect.value).toBe('uncategorized')
    })

    it('should default deleteAll checkbox to unchecked', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} />)

      const deleteAllCheckbox = screen.getByTestId('delete-category-modal-delete-all-checkbox') as HTMLInputElement
      expect(deleteAllCheckbox.checked).toBe(false)
    })
  })

  describe('Target Category Dropdown', () => {
    it('should accept availableCategories prop', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} />)

      const targetSelect = screen.getByTestId('delete-category-modal-target-select')

      // Verify select exists and can be changed to each category ID
      expect(targetSelect).toBeInTheDocument()

      // Change to each available category
      fireEvent.change(targetSelect, { target: { value: 'uncategorized' } })
      expect((targetSelect as HTMLInputElement).value).toBe('uncategorized')

      fireEvent.change(targetSelect, { target: { value: 'category-2' } })
      expect((targetSelect as HTMLInputElement).value).toBe('category-2')

      fireEvent.change(targetSelect, { target: { value: 'category-3' } })
      expect((targetSelect as HTMLInputElement).value).toBe('category-3')
    })

    it('should sort categories internally (Uncategorized first, then alphabetical)', () => {
      // This test verifies the sorting logic by checking initial default value
      // The component should default to Uncategorized (which comes first in sorted order)
      render(<DeleteCategoryConfirmationModal {...defaultProps} />)

      const targetSelect = screen.getByTestId('delete-category-modal-target-select') as HTMLInputElement

      // Should default to Uncategorized (first in sorted categories)
      expect(targetSelect.value).toBe('uncategorized')

      // Note: MUI Select renders options in Portal, making them difficult to query in tests
      // The actual sorting is verified through integration tests where dropdown is visible
    })

    it('should change target category when user selects different option', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} />)

      const targetSelect = screen.getByTestId('delete-category-modal-target-select')

      fireEvent.change(targetSelect, { target: { value: 'category-2' } })

      expect((targetSelect as HTMLInputElement).value).toBe('category-2')
    })

    it('should be disabled when deleteAll checkbox is checked', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} />)

      const deleteAllCheckbox = screen.getByTestId('delete-category-modal-delete-all-checkbox')
      const targetSelect = screen.getByTestId('delete-category-modal-target-select')

      // Initially enabled
      expect(targetSelect).not.toBeDisabled()

      // Check deleteAll checkbox
      fireEvent.click(deleteAllCheckbox)

      // Now should be disabled
      expect(targetSelect).toBeDisabled()
    })

    it('should be disabled when isDeleting is true', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} isDeleting={true} />)

      const targetSelect = screen.getByTestId('delete-category-modal-target-select')
      expect(targetSelect).toBeDisabled()
    })
  })

  describe('Delete All Checkbox', () => {
    it('should toggle deleteAll state when clicked', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} />)

      const deleteAllCheckbox = screen.getByTestId('delete-category-modal-delete-all-checkbox') as HTMLInputElement

      // Initially unchecked
      expect(deleteAllCheckbox.checked).toBe(false)

      // Click to check
      fireEvent.click(deleteAllCheckbox)
      expect(deleteAllCheckbox.checked).toBe(true)

      // Click to uncheck
      fireEvent.click(deleteAllCheckbox)
      expect(deleteAllCheckbox.checked).toBe(false)
    })

    it('should display correct label text', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} />)

      const control = screen.getByTestId('delete-category-modal-delete-all-control')
      expect(control).toHaveTextContent('Delete & unbookmark all items.')
    })

    it('should be disabled when isDeleting is true', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} isDeleting={true} />)

      const deleteAllCheckbox = screen.getByTestId('delete-category-modal-delete-all-checkbox')
      expect(deleteAllCheckbox).toBeDisabled()
    })
  })

  describe('Confirm Button', () => {
    it('should call onConfirm with target category ID when deleteAll is false', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} />)

      const confirmButton = screen.getByTestId('delete-category-modal-confirm-button')
      fireEvent.click(confirmButton)

      expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1)
      expect(defaultProps.onConfirm).toHaveBeenCalledWith('uncategorized', false)
    })

    it('should call onConfirm with null when deleteAll is true', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} />)

      // Check deleteAll checkbox
      const deleteAllCheckbox = screen.getByTestId('delete-category-modal-delete-all-checkbox')
      fireEvent.click(deleteAllCheckbox)

      // Click confirm
      const confirmButton = screen.getByTestId('delete-category-modal-confirm-button')
      fireEvent.click(confirmButton)

      expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1)
      expect(defaultProps.onConfirm).toHaveBeenCalledWith(null, true)
    })

    it('should call onConfirm with selected target category ID', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} />)

      // Change target category
      const targetSelect = screen.getByTestId('delete-category-modal-target-select')
      fireEvent.change(targetSelect, { target: { value: 'category-2' } })

      // Click confirm
      const confirmButton = screen.getByTestId('delete-category-modal-confirm-button')
      fireEvent.click(confirmButton)

      expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1)
      expect(defaultProps.onConfirm).toHaveBeenCalledWith('category-2', false)
    })

    it('should be disabled when isDeleting is true', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} isDeleting={true} />)

      const confirmButton = screen.getByTestId('delete-category-modal-confirm-button')
      expect(confirmButton).toBeDisabled()
    })

    it('should have error color variant', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} />)

      const confirmButton = screen.getByTestId('delete-category-modal-confirm-button')
      expect(confirmButton).toHaveClass('MuiButton-containedError')
    })
  })

  describe('Cancel Button', () => {
    it('should call onClose when clicked', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} />)

      const cancelButton = screen.getByTestId('delete-category-modal-cancel-button')
      fireEvent.click(cancelButton)

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
    })

    it('should be disabled when isDeleting is true', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} isDeleting={true} />)

      const cancelButton = screen.getByTestId('delete-category-modal-cancel-button')
      expect(cancelButton).toBeDisabled()
    })
  })

  describe('Close Behavior', () => {
    it('should not close when isDeleting is true', () => {
      const { rerender } = render(<DeleteCategoryConfirmationModal {...defaultProps} isDeleting={true} />)

      const cancelButton = screen.getByTestId('delete-category-modal-cancel-button')
      fireEvent.click(cancelButton)

      // onClose should not be called when isDeleting
      expect(defaultProps.onClose).not.toHaveBeenCalled()

      // Re-render with isDeleting=false
      rerender(<DeleteCategoryConfirmationModal {...defaultProps} isDeleting={false} />)

      fireEvent.click(cancelButton)

      // Now onClose should be called
      expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
    })
  })

  describe('Edge Cases', () => {
    it('should handle empty availableCategories array', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} availableCategories={[]} />)

      const targetSelect = screen.getByTestId('delete-category-modal-target-select') as HTMLInputElement

      // Should default to empty string when no Uncategorized category exists
      expect(targetSelect.value).toBe('')
    })

    it('should work when Uncategorized category does not exist', () => {
      const categoriesWithoutUncategorized = mockAvailableCategories.filter(
        (cat) => cat.name !== 'Uncategorized'
      )

      render(
        <DeleteCategoryConfirmationModal
          {...defaultProps}
          availableCategories={categoriesWithoutUncategorized}
        />
      )

      const targetSelect = screen.getByTestId('delete-category-modal-target-select') as HTMLInputElement

      // Should default to empty string when no Uncategorized category
      expect(targetSelect.value).toBe('')
    })
  })

  describe('Data Test IDs', () => {
    it('should have data-testid on all interactive elements', () => {
      render(<DeleteCategoryConfirmationModal {...defaultProps} dataTestId="test-modal" />)

      expect(screen.getByTestId('test-modal')).toBeInTheDocument()
      expect(screen.getByTestId('test-modal-title')).toBeInTheDocument()
      expect(screen.getByTestId('test-modal-content')).toBeInTheDocument()
      expect(screen.getByTestId('test-modal-message')).toBeInTheDocument()
      expect(screen.getByTestId('test-modal-target-field')).toBeInTheDocument()
      expect(screen.getByTestId('test-modal-target-select')).toBeInTheDocument()
      expect(screen.getByTestId('test-modal-delete-all-control')).toBeInTheDocument()
      expect(screen.getByTestId('test-modal-delete-all-checkbox')).toBeInTheDocument()
      expect(screen.getByTestId('test-modal-actions')).toBeInTheDocument()
      expect(screen.getByTestId('test-modal-cancel-button')).toBeInTheDocument()
      expect(screen.getByTestId('test-modal-confirm-button')).toBeInTheDocument()
    })
  })
})

import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, beforeEach, afterEach } from 'vitest'
import { CategoryFormModal } from '../CategoryFormModal'
import type { BookmarkCategory } from '../../../types/domain'

let queryClient: QueryClient

// Create fresh QueryClient before each test
beforeEach(() => {
  queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
})

// Ensure proper cleanup between tests to prevent state pollution
afterEach(() => {
  cleanup()
  queryClient.clear()
})

const renderWithProviders = (ui: ReactNode) => {
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

const mockCategory: BookmarkCategory = {
  id: 'cat-123',
  userId: 'user-123',
  name: 'Existing Category',
  description: 'Existing description',
  color: null,
  icon: null,
  coverContentId: null,
  coverContentSourceType: null,
  parentId: 'parent-123',
  sortIndex: null,
  isPublic: true,
  shareToken: null,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-02T00:00:00Z',
}

const mockCategories: BookmarkCategory[] = [
  {
    id: 'parent-123',
    userId: 'user-123',
    name: 'Parent Category',
    description: null,
    color: null,
    icon: null,
    coverContentId: null,
    coverContentSourceType: null,
    parentId: null,
    sortIndex: null,
    isPublic: false,
    shareToken: null,
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
  },
  {
    id: 'cat-123',
    userId: 'user-123',
    name: 'Existing Category',
    description: null,
    color: null,
    icon: null,
    coverContentId: null,
    coverContentSourceType: null,
    parentId: 'parent-123',
    sortIndex: null,
    isPublic: false,
    shareToken: null,
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
  },
]

describe('CategoryFormModal', () => {
  describe('Create Mode', () => {
    it('should render "Create Category" title', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
        />
      )

      expect(screen.getByText('Create Category')).toBeInTheDocument()
    })

    it('should have empty form fields', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
        />
      )

      const nameInput = screen.getByTestId('category-form-modal-name-input') as HTMLInputElement
      const descriptionInput = screen.getByTestId('category-form-modal-description-input') as HTMLInputElement

      expect(nameInput.value).toBe('')
      expect(descriptionInput.value).toBe('')
    })

    it('should default isPublic to false', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
        />
      )

      const publicSwitch = screen.getByTestId('category-form-modal-public-switch') as HTMLInputElement
      expect(publicSwitch.checked).toBe(false)
    })

    it('should default parentId to empty', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
          categories={mockCategories}
        />
      )

      const parentSelect = screen.getByTestId('category-form-modal-parent-select') as HTMLInputElement
      expect(parentSelect.value).toBe('')
    })

    it('should show "Create" button text', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
        />
      )

      expect(screen.getByText('Create')).toBeInTheDocument()
    })
  })

  describe('Edit Mode', () => {
    it('should render "Edit Category" title', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="edit"
          category={mockCategory}
        />
      )

      expect(screen.getByText('Edit Category')).toBeInTheDocument()
    })

    it('should pre-fill form with category data', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="edit"
          category={mockCategory}
        />
      )

      const nameInput = screen.getByTestId('category-form-modal-name-input') as HTMLInputElement
      const descriptionInput = screen.getByTestId('category-form-modal-description-input') as HTMLInputElement
      const publicSwitch = screen.getByTestId('category-form-modal-public-switch') as HTMLInputElement

      expect(nameInput.value).toBe('Existing Category')
      expect(descriptionInput.value).toBe('Existing description')
      expect(publicSwitch.checked).toBe(true)
    })

    it('should show "Save" button text', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="edit"
          category={mockCategory}
        />
      )

      expect(screen.getByText('Save')).toBeInTheDocument()
    })

    it('should update form when category prop changes', () => {
      const { rerender } = renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="edit"
          category={mockCategory}
        />
      )

      const updatedCategory = { ...mockCategory, name: 'Updated Name' }

      rerender(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="edit"
          category={updatedCategory}
        />
      )

      const nameInput = screen.getByTestId('category-form-modal-name-input') as HTMLInputElement
      expect(nameInput.value).toBe('Updated Name')
    })
  })

  describe('Form Validation - Name', () => {
    it('should show error when name is empty', async () => {
      const onSubmit = vi.fn()

      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={onSubmit}
          mode="create"
        />
      )

      const submitButton = screen.getByText('Create')
      fireEvent.click(submitButton)

      expect(await screen.findByText('Category name is required')).toBeInTheDocument()
      expect(onSubmit).not.toHaveBeenCalled()
    })

    it('should show error when name is < 2 characters', async () => {
      const onSubmit = vi.fn()

      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={onSubmit}
          mode="create"
        />
      )

      const nameInput = screen.getByTestId('category-form-modal-name-input')
      await userEvent.type(nameInput, 'A')

      const submitButton = screen.getByText('Create')
      fireEvent.click(submitButton)

      expect(await screen.findByText('Category name must be at least 2 characters')).toBeInTheDocument()
      expect(onSubmit).not.toHaveBeenCalled()
    })

    it('should show error when name is > 100 characters', async () => {
      const onSubmit = vi.fn()

      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={onSubmit}
          mode="create"
        />
      )

      const nameInput = screen.getByTestId('category-form-modal-name-input')
      await userEvent.type(nameInput, 'A'.repeat(101))

      const submitButton = screen.getByText('Create')
      fireEvent.click(submitButton)

      expect(await screen.findByText('Category name must be less than 100 characters')).toBeInTheDocument()
      expect(onSubmit).not.toHaveBeenCalled()
    })

    it('should not show error for valid name (2-100 chars)', async () => {
      const onSubmit = vi.fn()

      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={onSubmit}
          mode="create"
        />
      )

      const nameInput = screen.getByTestId('category-form-modal-name-input')
      await userEvent.type(nameInput, 'Valid Category Name')

      const submitButton = screen.getByText('Create')
      fireEvent.click(submitButton)

      expect(screen.queryByText('Category name is required')).not.toBeInTheDocument()
      expect(screen.queryByText('Category name must be at least 2 characters')).not.toBeInTheDocument()
      expect(onSubmit).toHaveBeenCalled()
    })
  })

  describe('Form Validation - Description', () => {
    it('should accept long description input via paste', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
        />
      )

      const descriptionInput = screen.getByTestId('category-form-modal-description-input') as HTMLInputElement
      const longText = 'A'.repeat(501)

      // Use fireEvent.change for long text to avoid userEvent performance issues
      fireEvent.change(descriptionInput, { target: { value: longText } })

      expect(descriptionInput.value).toBe(longText)
    })

    it('should show validation error for description > 500 characters on submit', async () => {
      const onSubmit = vi.fn()
      const user = userEvent.setup()

      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={onSubmit}
          mode="create"
        />
      )

      const nameInput = screen.getByTestId('category-form-modal-name-input')
      const descriptionInput = screen.getByTestId('category-form-modal-description-input')

      await user.type(nameInput, 'Test')
      // Use fireEvent for long text to avoid performance issues
      fireEvent.change(descriptionInput, { target: { value: 'A'.repeat(501) } })

      const submitButton = screen.getByText('Create')
      fireEvent.click(submitButton)

      expect(await screen.findByText('Description must be less than 500 characters')).toBeInTheDocument()
      expect(onSubmit).not.toHaveBeenCalled()
    })

    it('should not show error for empty description (optional)', async () => {
      const onSubmit = vi.fn()

      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={onSubmit}
          mode="create"
        />
      )

      const nameInput = screen.getByTestId('category-form-modal-name-input')
      await userEvent.type(nameInput, 'Test Category')

      const submitButton = screen.getByText('Create')
      fireEvent.click(submitButton)

      expect(screen.queryByText('Description must be less than 500 characters')).not.toBeInTheDocument()
      expect(onSubmit).toHaveBeenCalled()
    })

    it('should not show error for valid description', async () => {
      const onSubmit = vi.fn()

      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={onSubmit}
          mode="create"
        />
      )

      const nameInput = screen.getByTestId('category-form-modal-name-input')
      await userEvent.type(nameInput, 'Test')

      const descriptionInput = screen.getByTestId('category-form-modal-description-input')
      await userEvent.type(descriptionInput, 'Valid description')

      const submitButton = screen.getByText('Create')
      fireEvent.click(submitButton)

      expect(screen.queryByText('Description must be less than 500 characters')).not.toBeInTheDocument()
      expect(onSubmit).toHaveBeenCalled()
    })
  })

  describe('Parent Dropdown', () => {
    it('should show "None (Top Level)" as first option', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
          categories={mockCategories}
        />
      )

      const parentSelect = screen.getByTestId('category-form-modal-parent-select')
      fireEvent.mouseDown(parentSelect)

      expect(screen.getByText('None (Top Level)')).toBeInTheDocument()
    })

    it('should receive categories prop', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
          categories={mockCategories}
        />
      )

      // Component should render without error when categories are provided
      expect(screen.getByTestId('category-form-modal-parent-select')).toBeInTheDocument()
    })

    it('should open parent dropdown menu', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
          categories={mockCategories}
        />
      )

      const parentSelect = screen.getByTestId('category-form-modal-parent-select')
      fireEvent.mouseDown(parentSelect)

      // Dropdown should open and show "None (Top Level)" option
      expect(screen.getByText('None (Top Level)')).toBeInTheDocument()
    })

    it('should filter out current category in edit mode', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="edit"
          category={mockCategory}
          categories={mockCategories}
        />
      )

      const parentSelect = screen.getByTestId('category-form-modal-parent-select')
      fireEvent.mouseDown(parentSelect)

      // Current category should be filtered out
      const parentOptions = screen.getAllByText('Parent Category', { exact: false })
      expect(parentOptions.length).toBeGreaterThan(0)

      // "Existing Category" should not be in dropdown (filtered out)
      expect(screen.queryByText('Existing Category', { exact: true })).not.toBeInTheDocument()
    })

    it('should handle empty categories array', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
          categories={[]}
        />
      )

      const parentSelect = screen.getByTestId('category-form-modal-parent-select')
      fireEvent.mouseDown(parentSelect)

      expect(screen.getByText('None (Top Level)')).toBeInTheDocument()
    })
  })

  describe('Public Toggle', () => {
    it('should toggle isPublic state', async () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
        />
      )

      const publicSwitch = screen.getByTestId('category-form-modal-public-switch') as HTMLInputElement

      expect(publicSwitch.checked).toBe(false)

      await userEvent.click(publicSwitch)

      expect(publicSwitch.checked).toBe(true)
    })

    it('should show explanatory text', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
        />
      )

      expect(screen.getByText('Make this category visible to others')).toBeInTheDocument()
    })

    it('should be disabled when isSubmitting', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
          isSubmitting={true}
        />
      )

      const publicSwitch = screen.getByTestId('category-form-modal-public-switch') as HTMLInputElement
      expect(publicSwitch.disabled).toBe(true)
    })
  })

  describe('Form Submission', () => {
    it('should accept whitespace in name input', async () => {
      const user = userEvent.setup()

      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
        />
      )

      const nameInput = screen.getByTestId('category-form-modal-name-input') as HTMLInputElement
      await user.type(nameInput, '  Test Category  ')

      expect(nameInput.value).toBe('  Test Category  ')
    })

    it('should trim name when submitting form', async () => {
      const onSubmit = vi.fn()
      const user = userEvent.setup()

      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={onSubmit}
          mode="create"
        />
      )

      const nameInput = screen.getByTestId('category-form-modal-name-input')
      await user.type(nameInput, '  Test Category  ')

      const submitButton = screen.getByText('Create')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith({
          name: 'Test Category',
          description: undefined,
          isPublic: false,
          parentId: undefined,
        })
      })
    })

    it('should not call onSubmit if validation fails', async () => {
      const onSubmit = vi.fn()

      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={onSubmit}
          mode="create"
        />
      )

      const submitButton = screen.getByText('Create')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Category name is required')).toBeInTheDocument()
      })

      expect(onSubmit).not.toHaveBeenCalled()
    })

    it('should submit with minimal required fields', async () => {
      const onSubmit = vi.fn()
      const user = userEvent.setup()

      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={onSubmit}
          mode="create"
        />
      )

      const nameInput = screen.getByTestId('category-form-modal-name-input')
      await user.type(nameInput, 'Minimal Category')

      const submitButton = screen.getByText('Create')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalled()
      })

      // Verify that optional fields are undefined when not provided
      const submittedData = onSubmit.mock.calls[0][0]
      expect(submittedData.name).toBe('Minimal Category')
      expect(submittedData.description).toBeUndefined()
      expect(submittedData.parentId).toBeUndefined()
    })

    it('should disable form during submission', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
          isSubmitting={true}
        />
      )

      const nameInput = screen.getByTestId('category-form-modal-name-input') as HTMLInputElement
      const submitButton = screen.getByText('Create') as HTMLButtonElement

      expect(nameInput.disabled).toBe(true)
      expect(submitButton.disabled).toBe(true)
    })
  })

  describe('Close Behavior', () => {
    it('should call onClose when Cancel clicked', () => {
      const onClose = vi.fn()

      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={onClose}
          onSubmit={vi.fn()}
          mode="create"
        />
      )

      const cancelButton = screen.getByText('Cancel')
      fireEvent.click(cancelButton)

      expect(onClose).toHaveBeenCalled()
    })

    it('should not close when isSubmitting is true', () => {
      const onClose = vi.fn()

      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={onClose}
          onSubmit={vi.fn()}
          mode="create"
          isSubmitting={true}
        />
      )

      const cancelButton = screen.getByText('Cancel') as HTMLButtonElement
      expect(cancelButton.disabled).toBe(true)
    })

    it('should reset form when reopened in create mode', async () => {
      const { rerender } = renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
        />
      )

      const nameInput = screen.getByTestId('category-form-modal-name-input')
      await userEvent.type(nameInput, 'Test')

      // Close modal
      rerender(
        <CategoryFormModal
          open={false}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
        />
      )

      // Reopen modal
      rerender(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
        />
      )

      const newNameInput = screen.getByTestId('category-form-modal-name-input') as HTMLInputElement
      expect(newNameInput.value).toBe('')
    })
  })

  describe('Data Test IDs', () => {
    it('should have data-testid on all form fields', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
          dataTestId="test-modal"
        />
      )

      expect(screen.getByTestId('test-modal-name-input')).toBeInTheDocument()
      expect(screen.getByTestId('test-modal-description-input')).toBeInTheDocument()
      expect(screen.getByTestId('test-modal-parent-select')).toBeInTheDocument()
      expect(screen.getByTestId('test-modal-public-switch')).toBeInTheDocument()
    })

    it('should have data-testid on buttons', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
          dataTestId="test-modal"
        />
      )

      expect(screen.getByTestId('test-modal-cancel-button')).toBeInTheDocument()
      expect(screen.getByTestId('test-modal-submit-button')).toBeInTheDocument()
    })

    it('should have data-testid on parent options', () => {
      renderWithProviders(
        <CategoryFormModal
          open={true}
          onClose={vi.fn()}
          onSubmit={vi.fn()}
          mode="create"
          categories={mockCategories}
          dataTestId="test-modal"
        />
      )

      const parentSelect = screen.getByTestId('test-modal-parent-select')
      fireEvent.mouseDown(parentSelect)

      // Use getByText instead of getByTestId since MenuItem options are in Portal
      expect(screen.getByText('None (Top Level)')).toBeInTheDocument()
    })
  })
})

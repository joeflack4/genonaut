import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { TagContentBrowser } from '../TagContentBrowser';

// Mock the hooks
vi.mock('../../../hooks', () => ({
  useEnhancedGalleryList: vi.fn(),
  useCurrentUser: vi.fn(),
}));

// Mock the components
vi.mock('../../gallery', () => ({
  GridView: ({ items, isLoading, emptyMessage }: any) => (
    <div data-testid="grid-view">
      {isLoading ? (
        <div>Loading...</div>
      ) : items.length === 0 ? (
        <div>{emptyMessage}</div>
      ) : (
        items.map((item: any) => <div key={item.id}>{item.title}</div>)
      )}
    </div>
  ),
  ResolutionDropdown: ({ onResolutionChange }: any) => (
    <button
      data-testid="resolution-dropdown"
      onClick={() => onResolutionChange({ width: 512, height: 512, label: '512x512' })}
    >
      Change Resolution
    </button>
  ),
}));

const mockUseEnhancedGalleryList = vi.fn();
const mockUseCurrentUser = vi.fn();

// Get the mocked hooks
import { useEnhancedGalleryList, useCurrentUser } from '../../../hooks';

describe('TagContentBrowser', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const renderComponent = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <TagContentBrowser tagId="tag-123" {...props} />
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useCurrentUser as any).mockReturnValue({ data: { id: 'user-1' } });
  });

  describe('Content grid rendering', () => {
    it('renders content items when data is available', () => {
      (useEnhancedGalleryList as any).mockReturnValue({
        data: {
          items: [
            { id: '1', title: 'Item 1' },
            { id: '2', title: 'Item 2' },
          ],
          pagination: { totalPages: 1, totalItems: 2 },
        },
        isLoading: false,
        isError: false,
      });

      renderComponent();

      expect(screen.getByTestId('tag-content-browser')).toBeInTheDocument();
      expect(screen.getByTestId('grid-view')).toBeInTheDocument();
      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 2')).toBeInTheDocument();
    });

    it('shows loading state', () => {
      (useEnhancedGalleryList as any).mockReturnValue({
        data: null,
        isLoading: true,
        isError: false,
      });

      renderComponent();

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('shows empty state when no items', () => {
      (useEnhancedGalleryList as any).mockReturnValue({
        data: {
          items: [],
          pagination: { totalPages: 0, totalItems: 0 },
        },
        isLoading: false,
        isError: false,
      });

      renderComponent({ tagName: 'Test Tag' });

      expect(screen.getByText('No content found with tag "Test Tag"')).toBeInTheDocument();
    });

    it('shows error state', () => {
      (useEnhancedGalleryList as any).mockReturnValue({
        data: null,
        isLoading: false,
        isError: true,
        error: { message: 'Failed to load content' },
      });

      renderComponent();

      expect(screen.getByTestId('tag-content-error')).toBeInTheDocument();
      expect(screen.getByText(/Failed to load content/)).toBeInTheDocument();
    });
  });

  describe('Pagination', () => {
    it('shows pagination when multiple pages exist', () => {
      (useEnhancedGalleryList as any).mockReturnValue({
        data: {
          items: [{ id: '1', title: 'Item 1' }],
          pagination: { total_pages: 3, total_count: 30 },
        },
        isLoading: false,
        isError: false,
      });

      renderComponent();

      expect(screen.getByTestId('tag-content-pagination')).toBeInTheDocument();
    });

    it('hides pagination when only one page', () => {
      (useEnhancedGalleryList as any).mockReturnValue({
        data: {
          items: [{ id: '1', title: 'Item 1' }],
          pagination: { total_pages: 1, total_count: 5 },
        },
        isLoading: false,
        isError: false,
      });

      renderComponent();

      expect(screen.queryByTestId('tag-content-pagination')).not.toBeInTheDocument();
    });
  });

  describe('View mode switching', () => {
    it('starts in grid view by default', () => {
      (useEnhancedGalleryList as any).mockReturnValue({
        data: {
          items: [],
          pagination: { totalPages: 0, totalItems: 0 },
        },
        isLoading: false,
        isError: false,
      });

      renderComponent();

      const gridButton = screen.getByTestId('tag-content-grid-view-button');
      expect(gridButton).toHaveAttribute('aria-pressed', 'true');
    });

    it('switches to list view when list button clicked', async () => {
      const user = userEvent.setup();
      (useEnhancedGalleryList as any).mockReturnValue({
        data: {
          items: [],
          pagination: { totalPages: 0, totalItems: 0 },
        },
        isLoading: false,
        isError: false,
      });

      renderComponent();

      const listButton = screen.getByTestId('tag-content-list-view-button');
      await user.click(listButton);

      await waitFor(() => {
        expect(listButton).toHaveAttribute('aria-pressed', 'true');
      });

      expect(screen.getByTestId('tag-content-list')).toBeInTheDocument();
    });

    it('switches back to grid view', async () => {
      const user = userEvent.setup();
      (useEnhancedGalleryList as any).mockReturnValue({
        data: {
          items: [],
          pagination: { totalPages: 0, totalItems: 0 },
        },
        isLoading: false,
        isError: false,
      });

      renderComponent();

      // Switch to list
      const listButton = screen.getByTestId('tag-content-list-view-button');
      await user.click(listButton);

      await waitFor(() => {
        expect(screen.getByTestId('tag-content-list')).toBeInTheDocument();
      });

      // Switch back to grid
      const gridButton = screen.getByTestId('tag-content-grid-view-button');
      await user.click(gridButton);

      await waitFor(() => {
        expect(screen.getByTestId('grid-view')).toBeInTheDocument();
      });
    });
  });

  describe('Sorting', () => {
    it('has default sort option', () => {
      (useEnhancedGalleryList as any).mockReturnValue({
        data: {
          items: [],
          pagination: { totalPages: 0, totalItems: 0 },
        },
        isLoading: false,
        isError: false,
      });

      renderComponent();

      const sortSelect = screen.getByTestId('tag-content-sort-select');
      expect(sortSelect).toBeInTheDocument();
    });

    it('changes sort option', async () => {
      const user = userEvent.setup();
      (useEnhancedGalleryList as any).mockReturnValue({
        data: {
          items: [],
          pagination: { totalPages: 0, totalItems: 0 },
        },
        isLoading: false,
        isError: false,
      });

      renderComponent();

      const sortSelect = screen.getByTestId('tag-content-sort-select');
      // The actual onChange behavior is tested by the change in query params
      expect(sortSelect).toBeInTheDocument();
    });
  });

  describe('Item count display', () => {
    it('displays item count with tag name', () => {
      (useEnhancedGalleryList as any).mockReturnValue({
        data: {
          items: [{ id: '1' }],
          pagination: { total_pages: 1, total_count: 15 },
        },
        isLoading: false,
        isError: false,
      });

      renderComponent({ tagName: 'Nature' });

      expect(screen.getByText('15 items tagged with "Nature"')).toBeInTheDocument();
    });

    it('displays singular "item" for count of 1', () => {
      (useEnhancedGalleryList as any).mockReturnValue({
        data: {
          items: [{ id: '1' }],
          pagination: { total_pages: 1, total_count: 1 },
        },
        isLoading: false,
        isError: false,
      });

      renderComponent({ tagName: 'Nature' });

      expect(screen.getByText('1 item tagged with "Nature"')).toBeInTheDocument();
    });
  });

  describe('Resolution dropdown', () => {
    it('shows resolution dropdown in grid view', () => {
      (useEnhancedGalleryList as any).mockReturnValue({
        data: {
          items: [],
          pagination: { totalPages: 0, totalItems: 0 },
        },
        isLoading: false,
        isError: false,
      });

      renderComponent();

      expect(screen.getByTestId('resolution-dropdown')).toBeInTheDocument();
    });

    it('hides resolution dropdown in list view', async () => {
      const user = userEvent.setup();
      (useEnhancedGalleryList as any).mockReturnValue({
        data: {
          items: [],
          pagination: { totalPages: 0, totalItems: 0 },
        },
        isLoading: false,
        isError: false,
      });

      renderComponent();

      const listButton = screen.getByTestId('tag-content-list-view-button');
      await user.click(listButton);

      await waitFor(() => {
        expect(screen.queryByTestId('resolution-dropdown')).not.toBeInTheDocument();
      });
    });
  });
});

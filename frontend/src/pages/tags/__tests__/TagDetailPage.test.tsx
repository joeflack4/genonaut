import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { TagDetailPage } from '../TagDetailPage';

// Mock hooks
vi.mock('../../../hooks', () => ({
  useTagDetail: vi.fn(),
  useRateTag: vi.fn(),
  useCurrentUser: vi.fn(),
  useEnhancedGalleryList: vi.fn(),
}));

// Mock components
vi.mock('../../../components/tags/StarRating', () => ({
  StarRating: ({ label, value, averageRating, onChange }: any) => (
    <div data-testid={`star-rating-${label?.toLowerCase().replace(/\s+/g, '-')}`}>
      <span>{label}</span>
      <span>{value !== null ? `User: ${value}` : averageRating !== null ? `Avg: ${averageRating}` : 'No rating'}</span>
      {onChange && (
        <button onClick={() => onChange(4.5)} data-testid="rate-button">
          Rate
        </button>
      )}
    </div>
  ),
}));

vi.mock('../../../components/tags/TagContentBrowser', () => ({
  TagContentBrowser: ({ tagId, tagName }: any) => (
    <div data-testid="tag-content-browser">
      Content for tag {tagId} ({tagName})
    </div>
  ),
}));

import { useTagDetail, useRateTag, useCurrentUser } from '../../../hooks';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('TagDetailPage', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="/tags/:tagId" element={<TagDetailPage />} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>,
      { wrapper: undefined }
    );
  };

  const mockRateTag = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useCurrentUser as any).mockReturnValue({ data: { id: 'user-1' } });
    (useRateTag as any).mockReturnValue({
      mutate: mockRateTag,
      isPending: false,
    });

    // Mock window.history.pushState for navigation
    window.history.pushState({}, '', '/tags/tag-123');
  });

  describe('Page rendering with tag data', () => {
    it('renders tag detail page with complete data', () => {
      (useTagDetail as any).mockReturnValue({
        data: {
          tag: { id: 'tag-123', name: 'Nature Photography' },
          parents: [
            { id: 'parent-1', name: 'Photography' },
            { id: 'parent-2', name: 'Art' },
          ],
          children: [
            { id: 'child-1', name: 'Landscape' },
            { id: 'child-2', name: 'Wildlife' },
          ],
          user_rating: 4.0,
          average_rating: 4.3,
          rating_count: 25,
        },
        isLoading: false,
        error: null,
      });

      renderComponent();

      expect(screen.getByTestId('tag-detail-page')).toBeInTheDocument();
      expect(screen.getByTestId('tag-detail-title')).toHaveTextContent('Nature Photography');
    });

    it('shows loading state', () => {
      (useTagDetail as any).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
      });

      renderComponent();

      expect(screen.getByTestId('tag-detail-loading')).toBeInTheDocument();
    });

    it('shows error state when tag not found', () => {
      (useTagDetail as any).mockReturnValue({
        data: null,
        isLoading: false,
        error: { message: 'Tag not found' },
      });

      renderComponent();

      expect(screen.getByTestId('tag-detail-error')).toBeInTheDocument();
      expect(screen.getByText(/Tag not found/)).toBeInTheDocument();
    });
  });

  describe('Parent/child links', () => {
    it('displays parent tags as clickable chips', async () => {
      const user = userEvent.setup();
      (useTagDetail as any).mockReturnValue({
        data: {
          tag: { id: 'tag-123', name: 'Nature Photography' },
          parents: [
            { id: 'parent-1', name: 'Photography' },
            { id: 'parent-2', name: 'Art' },
          ],
          children: [],
          user_rating: null,
          average_rating: null,
          rating_count: 0,
        },
        isLoading: false,
        error: null,
      });

      renderComponent();

      expect(screen.getByTestId('tag-detail-parents-section')).toBeInTheDocument();
      expect(screen.getByText('Photography')).toBeInTheDocument();
      expect(screen.getByText('Art')).toBeInTheDocument();

      const parentChip = screen.getByTestId('tag-detail-parent-parent-1');
      await user.click(parentChip);

      expect(mockNavigate).toHaveBeenCalledWith(
        '/tags/parent-1',
        expect.objectContaining({
          state: expect.objectContaining({
            from: 'tags',
          }),
        })
      );
    });

    it('displays child tags as clickable chips', async () => {
      const user = userEvent.setup();
      (useTagDetail as any).mockReturnValue({
        data: {
          tag: { id: 'tag-123', name: 'Nature Photography' },
          parents: [],
          children: [
            { id: 'child-1', name: 'Landscape' },
            { id: 'child-2', name: 'Wildlife' },
          ],
          user_rating: null,
          average_rating: null,
          rating_count: 0,
        },
        isLoading: false,
        error: null,
      });

      renderComponent();

      expect(screen.getByTestId('tag-detail-children-section')).toBeInTheDocument();
      expect(screen.getByText('Landscape')).toBeInTheDocument();
      expect(screen.getByText('Wildlife')).toBeInTheDocument();

      const childChip = screen.getByTestId('tag-detail-child-child-1');
      await user.click(childChip);

      expect(mockNavigate).toHaveBeenCalledWith(
        '/tags/child-1',
        expect.objectContaining({
          state: expect.objectContaining({
            from: 'tags',
          }),
        })
      );
    });

    it('hides parent section when no parents', () => {
      (useTagDetail as any).mockReturnValue({
        data: {
          tag: { id: 'tag-123', name: 'Root Tag' },
          parents: [],
          children: [],
          user_rating: null,
          average_rating: null,
          rating_count: 0,
        },
        isLoading: false,
        error: null,
      });

      renderComponent();

      expect(screen.queryByTestId('tag-detail-parents-section')).not.toBeInTheDocument();
    });

    it('hides children section when no children', () => {
      (useTagDetail as any).mockReturnValue({
        data: {
          tag: { id: 'tag-123', name: 'Leaf Tag' },
          parents: [],
          children: [],
          user_rating: null,
          average_rating: null,
          rating_count: 0,
        },
        isLoading: false,
        error: null,
      });

      renderComponent();

      expect(screen.queryByTestId('tag-detail-children-section')).not.toBeInTheDocument();
    });
  });

  describe('Rating display', () => {
    it('displays both user rating and average rating', () => {
      (useTagDetail as any).mockReturnValue({
        data: {
          tag: { id: 'tag-123', name: 'Test Tag' },
          parents: [],
          children: [],
          user_rating: 4.0,
          average_rating: 4.3,
          rating_count: 25,
        },
        isLoading: false,
        error: null,
      });

      renderComponent();

      expect(screen.getByTestId('tag-detail-ratings-section')).toBeInTheDocument();

      // Average rating (read-only)
      const avgRating = screen.getByTestId('star-rating-average-rating');
      expect(avgRating).toHaveTextContent('Avg: 4.3');

      // User rating (interactive)
      const user_rating = screen.getByTestId('star-rating-your-rating');
      expect(user_rating).toHaveTextContent('User: 4');
    });

    it('allows user to rate the tag', async () => {
      const user = userEvent.setup();
      (useTagDetail as any).mockReturnValue({
        data: {
          tag: { id: 'tag-123', name: 'Test Tag' },
          parents: [],
          children: [],
          user_rating: null,
          average_rating: 4.3,
          rating_count: 25,
        },
        isLoading: false,
        error: null,
      });

      renderComponent();

      const rateButton = screen.getByTestId('rate-button');
      await user.click(rateButton);

      expect(mockRateTag).toHaveBeenCalledWith(
        {
          tagId: 'tag-123',
          params: {
            user_id: 'user-1',
            rating: 4.5
          }
        },
        expect.any(Object)
      );
    });

    it('shows saving indicator when rating is being submitted', () => {
      (useRateTag as any).mockReturnValue({
        mutate: mockRateTag,
        isPending: true,
      });

      (useTagDetail as any).mockReturnValue({
        data: {
          tag: { id: 'tag-123', name: 'Test Tag' },
          parents: [],
          children: [],
          user_rating: 3.0,
          average_rating: 4.0,
          rating_count: 10,
        },
        isLoading: false,
        error: null,
      });

      renderComponent();

      expect(screen.getByText('Saving...')).toBeInTheDocument();
    });
  });

  describe('Content browser integration', () => {
    it('initially hides content browser', () => {
      (useTagDetail as any).mockReturnValue({
        data: {
          tag: { id: 'tag-123', name: 'Test Tag' },
          parents: [],
          children: [],
          user_rating: null,
          average_rating: null,
          rating_count: 0,
        },
        isLoading: false,
        error: null,
      });

      renderComponent();

      expect(screen.queryByTestId('tag-detail-content-section')).not.toBeInTheDocument();
    });

    it('shows content browser when browse button clicked', async () => {
      const user = userEvent.setup();
      (useTagDetail as any).mockReturnValue({
        data: {
          tag: { id: 'tag-123', name: 'Test Tag' },
          parents: [],
          children: [],
          user_rating: null,
          average_rating: null,
          rating_count: 0,
        },
        isLoading: false,
        error: null,
      });

      renderComponent();

      const browseButton = screen.getByTestId('tag-detail-browse-button');
      await user.click(browseButton);

      await waitFor(() => {
        expect(screen.getByTestId('tag-detail-content-section')).toBeInTheDocument();
        expect(screen.getByTestId('tag-content-browser')).toBeInTheDocument();
      });
    });

    it('hides content browser when browse button clicked again', async () => {
      const user = userEvent.setup();
      (useTagDetail as any).mockReturnValue({
        data: {
          tag: { id: 'tag-123', name: 'Test Tag' },
          parents: [],
          children: [],
          user_rating: null,
          average_rating: null,
          rating_count: 0,
        },
        isLoading: false,
        error: null,
      });

      renderComponent();

      const browseButton = screen.getByTestId('tag-detail-browse-button');

      // Show
      await user.click(browseButton);
      await waitFor(() => {
        expect(screen.getByTestId('tag-content-browser')).toBeInTheDocument();
      });

      // Hide
      await user.click(browseButton);
      await waitFor(() => {
        expect(screen.queryByTestId('tag-detail-content-section')).not.toBeInTheDocument();
      });
    });
  });

  describe('Back button', () => {
    it('navigates back when back button is clicked', async () => {
      const user = userEvent.setup();
      (useTagDetail as any).mockReturnValue({
        data: {
          tag: { id: 'tag-123', name: 'Test Tag' },
          parents: [],
          children: [],
          user_rating: null,
          average_rating: null,
          rating_count: 0,
        },
        isLoading: false,
        error: null,
      });

      renderComponent();

      const backButton = screen.getByTestId('tag-detail-back-button');
      await user.click(backButton);

      expect(mockNavigate).toHaveBeenCalledWith('/tags');
    });

    it('is present in error state', async () => {
      const user = userEvent.setup();
      (useTagDetail as any).mockReturnValue({
        data: null,
        isLoading: false,
        error: { message: 'Not found' },
      });

      renderComponent();

      const backButton = screen.getByTestId('tag-detail-back-button');
      await user.click(backButton);

      expect(mockNavigate).toHaveBeenCalledWith('/tags');
    });
  });
});

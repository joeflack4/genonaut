/**
 * Tests for TagSearchFilter component
 */

import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import TagSearchFilter from '../TagSearchFilter';
import * as tagHierarchyHooks from '../../../hooks/useTagHierarchy';

// Mock the hooks
vi.mock('../../../hooks/useTagHierarchy');

const mockUseTagSearch = vi.mocked(tagHierarchyHooks.useTagSearch);
const mockUseTagBreadcrumbs = vi.mocked(tagHierarchyHooks.useTagBreadcrumbs);

// Test data
const mockSearchResults = [
  { id: 'abstract', name: 'Abstract', parent: 'art_movements' },
  { id: 'digital_art', name: 'Digital Art', parent: 'artistic_medium' },
  { id: 'photography', name: 'Photography', parent: 'artistic_medium' },
];

const mockBreadcrumbs = [
  { id: 'art_movements', name: 'Art Movements', parent: null },
  { id: 'abstract', name: 'Abstract', parent: 'art_movements' },
];

// Wrapper component for providers
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('TagSearchFilter', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock for breadcrumbs
    mockUseTagBreadcrumbs.mockReturnValue({
      breadcrumbs: mockBreadcrumbs,
      isRoot: false,
      depth: 2,
    });
  });

  it('renders search input with placeholder', () => {
    mockUseTagSearch.mockReturnValue({
      results: [],
      isLoading: false,
      error: null,
      hasQuery: false,
      totalResults: 0,
    } as any);

    render(
      <TestWrapper>
        <TagSearchFilter placeholder="Custom placeholder" />
      </TestWrapper>
    );

    expect(screen.getByPlaceholderText('Custom placeholder')).toBeInTheDocument();
  });

  it('shows search results when typing', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <TagSearchFilter />
      </TestWrapper>
    );

    const searchInput = screen.getByRole('textbox');

    // First setup the mock before typing
    mockUseTagSearch.mockReturnValue({
      results: mockSearchResults,
      isLoading: false,
      error: null,
      hasQuery: true,
      totalResults: 3,
    } as any);

    await user.type(searchInput, 'art');

    // Wait for results to appear
    await waitFor(() => {
      expect(screen.getByText('3 results found')).toBeInTheDocument();
    });
  });

  it('shows loading state during search', () => {
    mockUseTagSearch.mockReturnValue({
      results: [],
      isLoading: true,
      error: null,
      hasQuery: true,
      totalResults: 0,
    } as any);

    render(
      <TestWrapper>
        <TagSearchFilter />
      </TestWrapper>
    );

    // Focus the input to show results
    act(() => {
      const searchInput = screen.getByRole('textbox');
      searchInput.focus();
    });

    expect(screen.getByText('Searching...')).toBeInTheDocument();
  });

  it('shows error state when search fails', async () => {
    const user = userEvent.setup();

    mockUseTagSearch.mockReturnValue({
      results: [],
      isLoading: false,
      error: new Error('Search failed'),
      hasQuery: true,
      totalResults: 0,
    } as any);

    render(
      <TestWrapper>
        <TagSearchFilter />
      </TestWrapper>
    );

    const searchInput = screen.getByRole('textbox');
    await user.type(searchInput, 'test');

    await waitFor(() => {
      expect(screen.getByText('Failed to search tags. Please try again.')).toBeInTheDocument();
    });
  });

  it('shows no results message when no matches found', async () => {
    const user = userEvent.setup();

    mockUseTagSearch.mockReturnValue({
      results: [],
      isLoading: false,
      error: null,
      hasQuery: true,
      totalResults: 0,
    } as any);

    render(
      <TestWrapper>
        <TagSearchFilter />
      </TestWrapper>
    );

    const searchInput = screen.getByRole('textbox');
    await user.type(searchInput, 'nonexistent');

    await waitFor(() => {
      expect(screen.getByText('No tags found matching "nonexistent"')).toBeInTheDocument();
    });
  });

  it('calls onTagSelect when result is clicked', async () => {
    const user = userEvent.setup();
    const mockOnTagSelect = vi.fn();

    mockUseTagSearch.mockReturnValue({
      results: mockSearchResults,
      isLoading: false,
      error: null,
      hasQuery: true,
      totalResults: 3,
    } as any);

    render(
      <TestWrapper>
        <TagSearchFilter onTagSelect={mockOnTagSelect} />
      </TestWrapper>
    );

    const searchInput = screen.getByRole('textbox');
    await user.type(searchInput, 'art');

    // Wait for results to appear
    await waitFor(() => {
      expect(screen.getByText('Abstract')).toBeInTheDocument();
    });

    // Click on a result
    const result = screen.getByText('Abstract');
    await user.click(result);

    expect(mockOnTagSelect).toHaveBeenCalledWith('abstract', 'Abstract');
  });

  it('clears search when clear button is clicked', async () => {
    const user = userEvent.setup();

    mockUseTagSearch.mockReturnValue({
      results: mockSearchResults,
      isLoading: false,
      error: null,
      hasQuery: true,
      totalResults: 3,
    } as any);

    render(
      <TestWrapper>
        <TagSearchFilter />
      </TestWrapper>
    );

    const searchInput = screen.getByRole('textbox') as HTMLInputElement;
    await user.type(searchInput, 'test');

    expect(searchInput.value).toBe('test');

    // Click clear button
    const clearButton = screen.getByLabelText('Clear search');
    await user.click(clearButton);

    expect(searchInput.value).toBe('');
  });

  it('shows breadcrumbs when enabled', async () => {
    const user = userEvent.setup();

    mockUseTagSearch.mockReturnValue({
      results: mockSearchResults,
      isLoading: false,
      error: null,
      hasQuery: true,
      totalResults: 3,
    } as any);

    render(
      <TestWrapper>
        <TagSearchFilter showBreadcrumbs={true} />
      </TestWrapper>
    );

    const searchInput = screen.getByRole('textbox');
    await user.type(searchInput, 'abstract');

    // Wait for results to appear
    await waitFor(() => {
      expect(screen.getByText('Abstract')).toBeInTheDocument();
    });

    // Should show breadcrumb path
    expect(screen.getAllByText('Art Movements')[0]).toBeInTheDocument();
  });

  it.skip('limits results when maxResults is set', async () => {
    const user = userEvent.setup();

    const manyResults = Array.from({ length: 20 }, (_, i) => ({
      id: `tag${i}`,
      name: `Tag ${i}`,
      parent: 'parent',
    }));

    mockUseTagSearch.mockReturnValue({
      results: manyResults,
      isLoading: false,
      error: null,
      hasQuery: true,
      totalResults: 20,
    } as any);

    render(
      <TestWrapper>
        <TagSearchFilter maxResults={5} />
      </TestWrapper>
    );

    const searchInput = screen.getByRole('textbox');
    await user.type(searchInput, 'tag');

    await waitFor(() => {
      expect(screen.getByText('Showing 5 of 20 results')).toBeInTheDocument();
    });

    // Should only show 5 results even though we have 20
    expect(screen.getAllByText(/^Tag \d+$/)).toHaveLength(5);
  });
});
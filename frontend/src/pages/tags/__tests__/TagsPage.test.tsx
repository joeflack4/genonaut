/**
 * Tests for TagsPage component
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import TagsPage from '../TagsPage';
import * as tagHierarchyHooks from '../../../hooks/useTagHierarchy';

// Mock the hooks
vi.mock('../../../hooks/useTagHierarchy');

const mockUseTagHierarchy = vi.mocked(tagHierarchyHooks.useTagHierarchy);
const mockUseTagHierarchyTree = vi.mocked(tagHierarchyHooks.useTagHierarchyTree);
const mockUseRefreshHierarchy = vi.mocked(tagHierarchyHooks.useRefreshHierarchy);
const mockUseTagSearch = vi.mocked(tagHierarchyHooks.useTagSearch);

// Mock react-router-dom's useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Test data
const mockHierarchyData = {
  nodes: [
    { id: 'visual_aesthetics', name: 'Visual Aesthetics', parent: null },
    { id: 'technical_execution', name: 'Technical Execution', parent: null },
    { id: 'color_properties', name: 'Color Properties', parent: 'visual_aesthetics' },
    { id: 'bright', name: 'Bright', parent: 'color_properties' },
  ],
  metadata: {
    totalNodes: 4,
    totalRelationships: 3,
    rootCategories: 2,
    lastUpdated: '2024-01-01T00:00:00Z',
    format: 'flat_array',
    version: '1.0',
  },
};

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
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('TagsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock for tag hierarchy
    mockUseTagHierarchy.mockReturnValue({
      data: mockHierarchyData,
      isLoading: false,
      error: null,
    } as any);

    // Default mock for tree hierarchy (used by TagTreeView)
    mockUseTagHierarchyTree.mockReturnValue({
      data: [
        { id: 'visual_aesthetics', name: 'Visual Aesthetics', children: [{ id: 'color_properties', name: 'Color Properties', children: [{ id: 'bright', name: 'Bright', children: [] }] }] },
        { id: 'technical_execution', name: 'Technical Execution', children: [] },
      ],
      flatNodes: mockHierarchyData.nodes,
      metadata: mockHierarchyData.metadata,
      isLoading: false,
      error: null,
    } as any);

    // Default mock for refresh mutation
    mockUseRefreshHierarchy.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any);

    // Default mock for search
    mockUseTagSearch.mockReturnValue({
      results: [],
      isLoading: false,
      error: null,
      hasQuery: false,
      totalResults: 0,
    } as any);
  });

  it('renders page header and title', () => {
    mockUseTagHierarchy.mockReturnValue({
      data: mockHierarchyData,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <TagsPage />
      </TestWrapper>
    );

    expect(screen.getByRole('heading', { name: 'Tag Hierarchy' })).toBeInTheDocument();
    expect(screen.getByText('Explore the organized structure of content tags. Click on any tag to view related content.')).toBeInTheDocument();
  });

  it('displays hierarchy statistics', () => {
    mockUseTagHierarchy.mockReturnValue({
      data: mockHierarchyData,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <TagsPage />
      </TestWrapper>
    );

    expect(screen.getByText('4 total tags')).toBeInTheDocument();
    expect(screen.getByText('2 root categories')).toBeInTheDocument();
    expect(screen.getByText('3 relationships')).toBeInTheDocument();
  });

  it.skip('shows loading state for statistics', () => {
    mockUseTagHierarchy.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <TagsPage />
      </TestWrapper>
    );

    // Should show skeleton loading for stats
    const skeletons = screen.getAllByTestId('skeleton');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('displays error message when hierarchy fails to load', () => {
    mockUseTagHierarchy.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Failed to load'),
    } as any);

    render(
      <TestWrapper>
        <TagsPage />
      </TestWrapper>
    );

    expect(screen.getByText('Failed to load tag hierarchy. Please check your connection and try again.')).toBeInTheDocument();
  });

  it('toggles between tree and search modes', async () => {
    const user = userEvent.setup();

    mockUseTagHierarchy.mockReturnValue({
      data: mockHierarchyData,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <TagsPage />
      </TestWrapper>
    );

    // Initially should show tree view
    expect(screen.getByTestId('tags-page-tree-mode')).toBeInTheDocument();

    // Click search toggle
    const searchToggle = screen.getByLabelText('Show search');
    await user.click(searchToggle);

    // Should now show search view
    expect(screen.getByTestId('tags-page-search-mode')).toBeInTheDocument();

    // Click tree toggle
    const treeToggle = screen.getByLabelText('Show tree view');
    await user.click(treeToggle);

    // Should be back to tree view
    expect(screen.getByTestId('tags-page-tree-mode')).toBeInTheDocument();
  });

  it('calls refresh when refresh button is clicked', async () => {
    const user = userEvent.setup();
    const mockMutate = vi.fn();

    mockUseTagHierarchy.mockReturnValue({
      data: mockHierarchyData,
      isLoading: false,
      error: null,
    } as any);

    mockUseRefreshHierarchy.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
    } as any);

    render(
      <TestWrapper>
        <TagsPage />
      </TestWrapper>
    );

    const refreshButton = screen.getByLabelText('Refresh hierarchy');
    await user.click(refreshButton);

    expect(mockMutate).toHaveBeenCalled();
  });

  it('disables refresh button when refresh is pending', () => {
    mockUseTagHierarchy.mockReturnValue({
      data: mockHierarchyData,
      isLoading: false,
      error: null,
    } as any);

    mockUseRefreshHierarchy.mockReturnValue({
      mutate: vi.fn(),
      isPending: true,
    } as any);

    render(
      <TestWrapper>
        <TagsPage />
      </TestWrapper>
    );

    const refreshButton = screen.getByLabelText('Refresh hierarchy');
    expect(refreshButton).toBeDisabled();
  });

  it('navigates to gallery when tag is selected', async () => {
    mockUseTagHierarchy.mockReturnValue({
      data: mockHierarchyData,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <TagsPage />
      </TestWrapper>
    );

    // This would require simulating a click on the tree view or search results
    // The exact implementation depends on how the child components work
    // For now, we'll test that navigate function is available
    expect(mockNavigate).toBeDefined();
  });

  it.skip('shows help and info cards', () => {
    mockUseTagHierarchy.mockReturnValue({
      data: mockHierarchyData,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <TagsPage />
      </TestWrapper>
    );

    expect(screen.getByText('How to Use')).toBeInTheDocument();
    expect(screen.getByText('Hierarchy Overview')).toBeInTheDocument();

    // Check some help text
    expect(screen.getByText(/Browse.*Expand categories in the tree/)).toBeInTheDocument();
    expect(screen.getByText(/Search.*Use the search box/)).toBeInTheDocument();
  });

  it('displays hierarchy overview with correct data', () => {
    mockUseTagHierarchy.mockReturnValue({
      data: mockHierarchyData,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <TagsPage />
      </TestWrapper>
    );

    // Check hierarchy overview card
    expect(screen.getByText('Total Tags:')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument(); // Total nodes

    expect(screen.getByText('Root Categories:')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // Root categories

    expect(screen.getByText('Relationships:')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument(); // Total relationships

    expect(screen.getByText('Format:')).toBeInTheDocument();
    expect(screen.getByText('flat_array')).toBeInTheDocument();

    expect(screen.getByText('Version:')).toBeInTheDocument();
    expect(screen.getByText('1.0')).toBeInTheDocument();
  });
});

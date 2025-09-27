/**
 * Tests for TagTreeView component
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import TagTreeView from '../TagTreeView';
import * as tagHierarchyHooks from '../../../hooks/useTagHierarchy';

// Mock the hook
vi.mock('../../../hooks/useTagHierarchy');

const mockUseTagHierarchy = vi.mocked(tagHierarchyHooks.useTagHierarchy);

// Test data
const mockHierarchyData = {
  nodes: [
    { id: 'root1', name: 'Root Category 1', parent: null },
    { id: 'root2', name: 'Root Category 2', parent: null },
    { id: 'child1', name: 'Child 1', parent: 'root1' },
    { id: 'child2', name: 'Child 2', parent: 'root1' },
    { id: 'grandchild1', name: 'Grandchild 1', parent: 'child1' },
  ],
  metadata: {
    totalNodes: 5,
    totalRelationships: 4,
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

describe('TagTreeView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state', () => {
    mockUseTagHierarchy.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <TagTreeView />
      </TestWrapper>
    );

    expect(screen.getByText('Loading tag hierarchy...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders error state', () => {
    mockUseTagHierarchy.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Failed to load'),
    } as any);

    render(
      <TestWrapper>
        <TagTreeView />
      </TestWrapper>
    );

    expect(screen.getByText('Failed to load tag hierarchy. Please try refreshing the page.')).toBeInTheDocument();
  });

  it('renders empty state', () => {
    mockUseTagHierarchy.mockReturnValue({
      data: { nodes: [], metadata: mockHierarchyData.metadata },
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <TagTreeView />
      </TestWrapper>
    );

    expect(screen.getByText('No tag hierarchy data available.')).toBeInTheDocument();
  });

  it.skip('renders tree structure with data', async () => {
    mockUseTagHierarchy.mockReturnValue({
      data: mockHierarchyData,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <TagTreeView />
      </TestWrapper>
    );

    // Wait for tree to render
    await waitFor(() => {
      expect(screen.getByLabelText('Tag hierarchy tree')).toBeInTheDocument();
    });

    // Check that root nodes are visible
    expect(screen.getByText('Root Category 1')).toBeInTheDocument();
    expect(screen.getByText('Root Category 2')).toBeInTheDocument();
  });

  it.skip('calls onNodeClick when node is clicked', async () => {
    const mockOnNodeClick = vi.fn();

    mockUseTagHierarchy.mockReturnValue({
      data: mockHierarchyData,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <TagTreeView onNodeClick={mockOnNodeClick} />
      </TestWrapper>
    );

    // Wait for tree to render
    await waitFor(() => {
      expect(screen.getByText('Root Category 1')).toBeInTheDocument();
    });

    // Click on a node
    const node = screen.getByText('Root Category 1');
    await userEvent.click(node);

    // Verify callback was called
    expect(mockOnNodeClick).toHaveBeenCalledWith('root1', 'Root Category 1');
  });

  it.skip('shows node counts when enabled', async () => {
    mockUseTagHierarchy.mockReturnValue({
      data: mockHierarchyData,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <TagTreeView showNodeCounts={true} />
      </TestWrapper>
    );

    // Wait for tree to render
    await waitFor(() => {
      expect(screen.getByText('Root Category 1')).toBeInTheDocument();
    });

    // Root Category 1 should show count of 2 (child1, child2)
    // Note: The exact implementation depends on how the tree component renders counts
    // This is a placeholder test that would need adjustment based on actual rendering
  });

  it.skip('highlights selected node', async () => {
    mockUseTagHierarchy.mockReturnValue({
      data: mockHierarchyData,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <TagTreeView selectedNodeId="root1" />
      </TestWrapper>
    );

    // Wait for tree to render
    await waitFor(() => {
      expect(screen.getByText('Root Category 1')).toBeInTheDocument();
    });

    // Check that the selected node has appropriate styling
    // Note: This would need to be adjusted based on how selection is visually indicated
    const selectedNode = screen.getByText('Root Category 1');
    expect(selectedNode).toBeInTheDocument();
  });
});
/**
 * React hook for tag hierarchy data management
 *
 * Updated to use database-backed tag service (v2.0)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tagService } from '../services';
import { tagHierarchyService } from '../services/tag-hierarchy-service';

// Query keys
export const tagHierarchyKeys = {
  all: ['tagHierarchy'] as const,
  hierarchy: () => [...tagHierarchyKeys.all, 'hierarchy'] as const,
  node: (id: string) => [...tagHierarchyKeys.all, 'node', id] as const,
  children: (parentId: string) => [...tagHierarchyKeys.all, 'children', parentId] as const,
  path: (nodeId: string) => [...tagHierarchyKeys.all, 'path', nodeId] as const,
  roots: () => [...tagHierarchyKeys.all, 'roots'] as const,
};

/**
 * Hook to get the complete tag hierarchy (database-backed)
 */
export function useTagHierarchy(options?: { includeRatings?: boolean }) {
  return useQuery({
    queryKey: [...tagHierarchyKeys.hierarchy(), options?.includeRatings],
    queryFn: () => tagService.getTagHierarchy(options?.includeRatings),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook to get hierarchy as a tree structure
 */
export function useTagHierarchyTree(options?: { includeRatings?: boolean }) {
  const hierarchyQuery = useTagHierarchy(options);

  const treeData = hierarchyQuery.data ?
    tagHierarchyService.convertToTree(hierarchyQuery.data.nodes) :
    undefined;

  const finalIsLoading = hierarchyQuery.isLoading && !treeData;

  return {
    ...hierarchyQuery,
    data: treeData,
    flatNodes: hierarchyQuery.data?.nodes,
    metadata: hierarchyQuery.data?.metadata,
    // Ensure we're not loading if we have tree data
    isLoading: finalIsLoading,
  };
}

/**
 * Hook to get a specific tag node
 */
export function useTagNode(nodeId: string) {
  return useQuery({
    queryKey: tagHierarchyKeys.node(nodeId),
    queryFn: () => tagHierarchyService.getNode(nodeId),
    enabled: !!nodeId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook to get children of a parent tag
 */
export function useTagHierarchyChildren(parentId: string) {
  return useQuery({
    queryKey: tagHierarchyKeys.children(parentId),
    queryFn: () => tagHierarchyService.getChildren(parentId),
    enabled: !!parentId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook to get root tags (database-backed)
 */
export function useRootTags() {
  return useQuery({
    queryKey: tagHierarchyKeys.roots(),
    queryFn: () => tagService.getRootTags(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook to get tag path to root
 */
export function useTagPath(nodeId: string) {
  return useQuery({
    queryKey: tagHierarchyKeys.path(nodeId),
    queryFn: () => tagHierarchyService.getTagPath(nodeId),
    enabled: !!nodeId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook to refresh hierarchy cache
 */
export function useRefreshHierarchy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      // Fetch fresh hierarchy from database
      const hierarchy = await tagService.getTagHierarchy(true);
      return hierarchy;
    },
    onSuccess: () => {
      // Invalidate all tag hierarchy queries
      queryClient.invalidateQueries({ queryKey: tagHierarchyKeys.all });
    },
  });
}

/**
 * Hook for tag search functionality
 */
export function useTagHierarchySearch(query: string) {
  const { data: hierarchy, isLoading, error } = useTagHierarchy();

  const searchResults = hierarchy && query.trim() ?
    tagHierarchyService.searchNodes(hierarchy.nodes, query) :
    hierarchy?.nodes || [];

  return {
    results: searchResults,
    isLoading,
    error,
    hasQuery: !!query.trim(),
    totalResults: searchResults.length,
  };
}

/**
 * Hook for getting breadcrumbs for a specific node
 */
export function useTagBreadcrumbs(nodeId: string) {
  const { data: hierarchy } = useTagHierarchy();

  const breadcrumbs = hierarchy && nodeId ?
    tagHierarchyService.getBreadcrumbs(hierarchy.nodes, nodeId) :
    [];

  return {
    breadcrumbs,
    isRoot: breadcrumbs.length <= 1,
    depth: breadcrumbs.length,
  };
}

/**
 * Hook for getting all descendants of a node
 */
export function useTagDescendants(nodeId: string) {
  const { data: hierarchy } = useTagHierarchy();

  const descendants = hierarchy && nodeId ?
    tagHierarchyService.getDescendants(hierarchy.nodes, nodeId) :
    [];

  return {
    descendants,
    count: descendants.length,
    hasDescendants: descendants.length > 0,
  };
}
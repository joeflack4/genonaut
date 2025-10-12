/**
 * React hooks for tag CRUD, ratings, and favorites
 *
 * Database-backed tag management (v2.0)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tagService } from '../services';
import type {
  TagListParams,
  TagSearchParams,
  TagRateParams,
  TagFavoriteParams
} from '../services';
import type { ApiTag, ApiTagDetail, ApiEnhancedPaginatedResponse, ApiTagRatingValue } from '../types/api';

// Query keys
export const tagKeys = {
  all: ['tags'] as const,
  lists: () => [...tagKeys.all, 'list'] as const,
  list: (params: TagListParams) => [...tagKeys.lists(), params] as const,
  searches: () => [...tagKeys.all, 'search'] as const,
  search: (params: TagSearchParams) => [...tagKeys.searches(), params] as const,
  details: () => [...tagKeys.all, 'detail'] as const,
  detail: (tagId: string, userId?: string) => [...tagKeys.details(), tagId, userId] as const,
  children: (tagId: string) => [...tagKeys.all, 'children', tagId] as const,
  parents: (tagId: string) => [...tagKeys.all, 'parents', tagId] as const,
  statistics: () => [...tagKeys.all, 'statistics'] as const,
  ratings: () => [...tagKeys.all, 'ratings'] as const,
  userRating: (tagId: string, userId: string) => [...tagKeys.ratings(), tagId, userId] as const,
  favorites: () => [...tagKeys.all, 'favorites'] as const,
  userFavorites: (userId: string) => [...tagKeys.favorites(), userId] as const,
};

// Tag List Hooks

/**
 * Hook to list tags with pagination
 */
export function useTags(params: TagListParams = {}) {
  return useQuery<ApiEnhancedPaginatedResponse<ApiTag>>({
    queryKey: tagKeys.list(params),
    queryFn: () => tagService.listTags(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to search tags
 */
export function useTagSearch(params: TagSearchParams) {
  return useQuery<ApiEnhancedPaginatedResponse<ApiTag>>({
    queryKey: tagKeys.search(params),
    queryFn: () => tagService.searchTags(params),
    enabled: params.q.trim().length > 0,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook to get tag statistics
 */
export function useTagStatistics() {
  return useQuery({
    queryKey: tagKeys.statistics(),
    queryFn: () => tagService.getTagStatistics(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

// Tag Detail Hooks

/**
 * Hook to get tag detail including parents, children, and ratings
 */
export function useTagDetail(tagId: string, userId?: string) {
  return useQuery<ApiTagDetail>({
    queryKey: tagKeys.detail(tagId, userId),
    queryFn: () => tagService.getTagDetail(tagId, userId),
    enabled: !!tagId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to get tag children
 */
export function useTagChildren(tagId: string) {
  return useQuery<ApiTag[]>({
    queryKey: tagKeys.children(tagId),
    queryFn: () => tagService.getTagChildren(tagId),
    enabled: !!tagId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook to get tag parents
 */
export function useTagParents(tagId: string) {
  return useQuery<ApiTag[]>({
    queryKey: tagKeys.parents(tagId),
    queryFn: () => tagService.getTagParents(tagId),
    enabled: !!tagId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

// Rating Hooks

/**
 * Hook to get user's rating for a tag
 */
export function useUserTagRating(tagId: string, userId: string) {
  return useQuery<ApiTagRatingValue>({
    queryKey: tagKeys.userRating(tagId, userId),
    queryFn: () => tagService.getUserTagRating(tagId, userId),
    enabled: !!tagId && !!userId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook to rate a tag
 */
export function useRateTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tagId, params }: { tagId: string; params: TagRateParams }) =>
      tagService.rateTag(tagId, params),
    onSuccess: (_, variables) => {
      // Invalidate tag detail to refresh average rating
      queryClient.invalidateQueries({
        queryKey: tagKeys.detail(variables.tagId, variables.params.user_id)
      });
      // Invalidate user's rating for this tag
      queryClient.invalidateQueries({
        queryKey: tagKeys.userRating(variables.tagId, variables.params.user_id)
      });
    },
  });
}

/**
 * Hook to delete a tag rating
 */
export function useDeleteTagRating() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tagId, userId }: { tagId: string; userId: string }) =>
      tagService.deleteTagRating(tagId, userId),
    onSuccess: (_, variables) => {
      // Invalidate tag detail to refresh average rating
      queryClient.invalidateQueries({
        queryKey: tagKeys.detail(variables.tagId, variables.userId)
      });
      // Invalidate user's rating for this tag
      queryClient.invalidateQueries({
        queryKey: tagKeys.userRating(variables.tagId, variables.userId)
      });
    },
  });
}

// Favorite Hooks

/**
 * Hook to get user's favorite tags
 */
export function useUserFavorites(userId: string) {
  return useQuery<ApiTag[]>({
    queryKey: tagKeys.userFavorites(userId),
    queryFn: () => tagService.getUserFavorites(userId),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to add a tag to favorites
 */
export function useAddFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tagId, params }: { tagId: string; params: TagFavoriteParams }) =>
      tagService.addFavorite(tagId, params),
    onSuccess: (_, variables) => {
      // Invalidate user's favorites list
      queryClient.invalidateQueries({
        queryKey: tagKeys.userFavorites(variables.params.user_id)
      });
    },
  });
}

/**
 * Hook to remove a tag from favorites
 */
export function useRemoveFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tagId, params }: { tagId: string; params: TagFavoriteParams }) =>
      tagService.removeFavorite(tagId, params),
    onSuccess: (_, variables) => {
      // Invalidate user's favorites list
      queryClient.invalidateQueries({
        queryKey: tagKeys.userFavorites(variables.params.user_id)
      });
    },
  });
}

/**
 * Hook to check if a tag is in user's favorites
 *
 * Uses the favorites list to determine if a tag is favorited
 */
export function useIsTagFavorited(tagId: string, userId: string) {
  const { data: favorites, isLoading } = useUserFavorites(userId);

  const isFavorited = favorites?.some(tag => tag.id === tagId) ?? false;

  return {
    isFavorited,
    isLoading,
  };
}

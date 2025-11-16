import { useMutation, useQueryClient } from '@tanstack/react-query'
import { galleryService } from '../services'
import type { ApiSuccessResponse } from '../types/api'

/**
 * Hook providing mutation for deleting content
 * Automatically invalidates relevant queries on success
 *
 * @returns Mutation object with delete function and state (isPending, error, etc.)
 *
 * @example
 * ```tsx
 * const { mutate: deleteContent, isPending } = useDeleteContent()
 *
 * // Delete regular content
 * deleteContent(
 *   { contentId: 123 },
 *   {
 *     onSuccess: () => navigate('/gallery'),
 *     onError: (error) => console.error(error)
 *   }
 * )
 *
 * // Delete auto-generated content
 * deleteContent(
 *   { contentId: 456, sourceType: 'auto' },
 *   { onSuccess: () => navigate('/gallery') }
 * )
 * ```
 */
export function useDeleteContent() {
  const queryClient = useQueryClient()

  return useMutation<
    ApiSuccessResponse,
    Error,
    { contentId: number; sourceType?: 'regular' | 'auto' }
  >({
    mutationFn: ({ contentId, sourceType }) =>
      galleryService.deleteContent(contentId, { sourceType }),
    onSuccess: (_data, variables) => {
      // Invalidate the specific gallery item query
      queryClient.invalidateQueries({
        queryKey: ['gallery-item', variables.contentId],
      })

      // Invalidate all gallery list queries (will refetch current page)
      queryClient.invalidateQueries({
        queryKey: ['gallery'],
      })

      // Invalidate unified gallery queries
      queryClient.invalidateQueries({
        queryKey: ['unified-gallery'],
      })

      // Invalidate unified gallery stats
      queryClient.invalidateQueries({
        queryKey: ['unified-gallery-stats'],
      })
    },
  })
}

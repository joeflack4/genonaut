import { useState } from 'react'
import { IconButton, CircularProgress, Tooltip } from '@mui/material'
import BookmarkIcon from '@mui/icons-material/Bookmark'
import BookmarkBorderIcon from '@mui/icons-material/BookmarkBorder'
import { useBookmarkStatus, useBookmarkMutations } from '../../hooks'
import { BookmarkManagementModal } from './BookmarkManagementModal'
import type { Bookmark } from '../../types/domain'

interface BookmarkButtonProps {
  contentId: number
  contentSourceType?: string
  userId: string
  size?: 'small' | 'medium' | 'large'
  showLabel?: boolean
  onBookmarkClick?: (bookmark: { id: string; isBookmarked: boolean }) => void
  /**
   * Optional pre-fetched bookmark status from batch query
   * If provided, the component won't make an individual API call
   */
  bookmarkStatus?: {
    isBookmarked: boolean
    bookmark: Bookmark | undefined
  }
}

/**
 * Bookmark icon button component
 * Shows filled icon when bookmarked, outline when not
 * Clicking when not bookmarked creates a bookmark
 * Clicking when bookmarked opens management modal
 *
 * Can work in two modes:
 * 1. Individual mode: Fetches bookmark status individually (for detail pages)
 * 2. Batch mode: Uses pre-fetched status from parent (for grid/list pages)
 */
export function BookmarkButton({
  contentId,
  contentSourceType = 'items',
  userId,
  size = 'medium',
  showLabel = false,
  onBookmarkClick,
  bookmarkStatus: providedStatus,
}: BookmarkButtonProps) {
  // Only fetch individual status if not provided via props
  const individualStatus = useBookmarkStatus(
    providedStatus ? undefined : userId,
    providedStatus ? undefined : contentId,
    contentSourceType
  )

  // Use provided status if available, otherwise use individual fetch
  const { isBookmarked, bookmark, isLoading } = providedStatus
    ? { ...providedStatus, isLoading: false }
    : individualStatus

  const { createBookmark, deleteBookmark } = useBookmarkMutations(userId)
  const [isProcessing, setIsProcessing] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)

  // Optimistic UI state: shows immediate feedback before server confirms
  const [optimisticBookmarked, setOptimisticBookmarked] = useState<boolean | null>(null)

  // Use optimistic state if set, otherwise use actual bookmark status
  const displayBookmarked = optimisticBookmarked !== null ? optimisticBookmarked : isBookmarked

  const handleClick = async (e: React.MouseEvent) => {
    // Prevent event from bubbling to parent (e.g., grid cell navigation)
    e.stopPropagation()

    if (isProcessing) return

    try {
      if (isBookmarked && bookmark) {
        // Open management modal when bookmarked
        setModalOpen(true)
        return
      } else {
        // Optimistically show bookmark as added immediately
        setOptimisticBookmarked(true)

        try {
          // Create new bookmark (no loading state - optimistic UI provides immediate feedback)
          const newBookmark = await createBookmark.mutateAsync({
            contentId,
            contentSourceType,
          })

          // Success! Clear optimistic state (React Query will have updated the real data)
          setOptimisticBookmarked(null)

          if (onBookmarkClick) {
            onBookmarkClick({ id: newBookmark.id, isBookmarked: true })
          }
        } catch (error) {
          // Revert optimistic update on error
          setOptimisticBookmarked(null)
          console.error('Error creating bookmark:', error)
          throw error
        }
      }
    } catch (error) {
      console.error('Error handling bookmark:', error)
    }
  }

  const loading = isLoading || isProcessing

  return (
    <>
      <Tooltip title={displayBookmarked ? 'Manage bookmark' : 'Add bookmark'}>
        <span>
          <IconButton
            onClick={handleClick}
            size={size}
            disabled={loading}
            data-testid={`bookmark-button-${contentId}`}
            aria-label={displayBookmarked ? 'Manage bookmark' : 'Add bookmark'}
            sx={{
              color: displayBookmarked ? 'primary.main' : 'action.active',
            }}
          >
            {loading ? (
              <CircularProgress size={size === 'small' ? 16 : 24} />
            ) : displayBookmarked ? (
              <BookmarkIcon fontSize={size} data-testid="bookmark-icon-filled" />
            ) : (
              <BookmarkBorderIcon fontSize={size} data-testid="bookmark-icon-outline" />
            )}
          </IconButton>
        </span>
      </Tooltip>

      {isBookmarked && bookmark && (
        <BookmarkManagementModal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          bookmark={bookmark}
          userId={userId}
        />
      )}
    </>
  )
}

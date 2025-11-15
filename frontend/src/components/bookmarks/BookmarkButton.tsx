import { useState } from 'react'
import { IconButton, CircularProgress, Tooltip } from '@mui/material'
import BookmarkIcon from '@mui/icons-material/Bookmark'
import BookmarkBorderIcon from '@mui/icons-material/BookmarkBorder'
import { useBookmarkStatus, useBookmarkMutations } from '../../hooks'
import { BookmarkManagementModal } from './BookmarkManagementModal'

interface BookmarkButtonProps {
  contentId: number
  contentSourceType?: string
  userId: string
  size?: 'small' | 'medium' | 'large'
  showLabel?: boolean
  onBookmarkClick?: (bookmark: { id: string; isBookmarked: boolean }) => void
}

/**
 * Bookmark icon button component
 * Shows filled icon when bookmarked, outline when not
 * Clicking when not bookmarked creates a bookmark
 * Clicking when bookmarked opens management modal
 */
export function BookmarkButton({
  contentId,
  contentSourceType = 'items',
  userId,
  size = 'medium',
  showLabel = false,
  onBookmarkClick,
}: BookmarkButtonProps) {
  const { isBookmarked, bookmark, isLoading } = useBookmarkStatus(
    userId,
    contentId,
    contentSourceType
  )
  const { createBookmark, deleteBookmark } = useBookmarkMutations(userId)
  const [isProcessing, setIsProcessing] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)

  const handleClick = async () => {
    if (isProcessing) return

    setIsProcessing(true)
    try {
      if (isBookmarked && bookmark) {
        // Open management modal when bookmarked
        setModalOpen(true)
        setIsProcessing(false)
        return
      } else {
        // Create new bookmark
        const newBookmark = await createBookmark.mutateAsync({
          contentId,
          contentSourceType,
        })

        if (onBookmarkClick) {
          onBookmarkClick({ id: newBookmark.id, isBookmarked: true })
        }
      }
    } catch (error) {
      console.error('Error handling bookmark:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  const loading = isLoading || isProcessing

  return (
    <>
      <Tooltip title={isBookmarked ? 'Manage bookmark' : 'Add bookmark'}>
        <span>
          <IconButton
            onClick={handleClick}
            size={size}
            disabled={loading}
            data-testid={`bookmark-button-${contentId}`}
            aria-label={isBookmarked ? 'Manage bookmark' : 'Add bookmark'}
            sx={{
              color: isBookmarked ? 'primary.main' : 'action.active',
            }}
          >
            {loading ? (
              <CircularProgress size={size === 'small' ? 16 : 24} />
            ) : isBookmarked ? (
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

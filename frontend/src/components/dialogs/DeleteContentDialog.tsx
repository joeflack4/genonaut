import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Typography,
} from '@mui/material'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'

export interface DeleteContentDialogProps {
  /** Whether the dialog is open */
  open: boolean
  /** Callback when dialog should be closed */
  onClose: () => void
  /** Callback when delete is confirmed */
  onConfirm: () => void
  /** ID of the content being deleted */
  contentId: number
}

/**
 * Confirmation dialog for deleting content
 *
 * Displays a warning about permanent deletion and requires user confirmation.
 * When confirmed, calls onConfirm and closes the dialog. The actual deletion
 * is handled by the parent component.
 */
export function DeleteContentDialog({
  open,
  onClose,
  onConfirm,
  contentId,
}: DeleteContentDialogProps) {
  const handleConfirm = () => {
    onConfirm()
    onClose()
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      aria-labelledby="delete-content-dialog-title"
      aria-describedby="delete-content-dialog-description"
      data-testid="delete-content-dialog"
    >
      <DialogTitle
        id="delete-content-dialog-title"
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <WarningAmberIcon color="warning" />
        <span>Content deletion</span>
      </DialogTitle>

      <DialogContent>
        <DialogContentText
          id="delete-content-dialog-description"
          data-testid="delete-content-dialog-message"
        >
          Please confirm.{/* Are you sure you want to delete content <Typography component="span" fontWeight="bold">#{contentId}</Typography>? */}
        </DialogContentText>
        {/* <DialogContentText sx={{ mt: 2, color: 'warning.main' }}>
          This action cannot be undone.
        </DialogContentText> */}
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button
          onClick={onClose}
          color="primary"
          variant="outlined"
          data-testid="delete-content-dialog-cancel"
        >
          Cancel
        </Button>
        <Button
          onClick={handleConfirm}
          color="error"
          variant="contained"
          autoFocus
          data-testid="delete-content-dialog-confirm"
        >
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  )
}

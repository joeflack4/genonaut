import { useState } from 'react'
import {
  Box,
  Button,
  Checkbox,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import VisibilityIcon from '@mui/icons-material/Visibility'
import type { FlaggedContent } from '../../types/domain'
import { RiskBadge } from './RiskBadge'

interface FlaggedContentTableProps {
  items: FlaggedContent[]
  selectedIds: number[]
  onSelectionChange: (ids: number[]) => void
  onReview: (id: number, reviewed: boolean, notes?: string) => void
  onDelete: (id: number) => void
  currentUserId: string
}

export function FlaggedContentTable({
  items,
  selectedIds,
  onSelectionChange,
  onReview,
  onDelete,
}: FlaggedContentTableProps) {
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<FlaggedContent | null>(null)
  const [reviewNotes, setReviewNotes] = useState('')

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      onSelectionChange(items.map((item) => item.id))
    } else {
      onSelectionChange([])
    }
  }

  const handleSelectOne = (id: number) => {
    const newSelection = selectedIds.includes(id)
      ? selectedIds.filter((selectedId) => selectedId !== id)
      : [...selectedIds, id]
    onSelectionChange(newSelection)
  }

  const handleViewDetails = (item: FlaggedContent) => {
    setSelectedItem(item)
    setDetailDialogOpen(true)
  }

  const handleReviewClick = (item: FlaggedContent) => {
    setSelectedItem(item)
    setReviewNotes(item.notes ?? '')
    setReviewDialogOpen(true)
  }

  const handleReviewSubmit = () => {
    if (selectedItem) {
      onReview(selectedItem.id, true, reviewNotes.trim() || undefined)
      setReviewDialogOpen(false)
      setSelectedItem(null)
      setReviewNotes('')
    }
  }

  const handleDeleteClick = (item: FlaggedContent) => {
    setSelectedItem(item)
    setDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = () => {
    if (selectedItem) {
      onDelete(selectedItem.id)
      setDeleteDialogOpen(false)
      setSelectedItem(null)
    }
  }

  const allSelected = items.length > 0 && selectedIds.length === items.length
  const someSelected = selectedIds.length > 0 && selectedIds.length < items.length

  return (
    <>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  checked={allSelected}
                  indeterminate={someSelected}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell>Risk</TableCell>
              <TableCell>Content Preview</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Problem Words</TableCell>
              <TableCell>Problem %</TableCell>
              <TableCell>Flagged Date</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
                    No flagged content found. Try adjusting your filters.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow key={item.id} hover>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedIds.includes(item.id)}
                      onChange={() => handleSelectOne(item.id)}
                    />
                  </TableCell>
                  <TableCell>
                    <RiskBadge riskScore={item.riskScore} />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ maxWidth: 300 }} noWrap>
                      {item.flaggedText}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={item.contentSource === 'regular' ? 'Regular' : 'Auto'}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {item.totalProblemWords}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {item.problemPercentage.toFixed(1)}%
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {new Date(item.flaggedAt).toLocaleDateString()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {item.reviewed ? (
                      <Chip
                        icon={<CheckCircleIcon />}
                        label="Reviewed"
                        size="small"
                        color="success"
                        variant="outlined"
                      />
                    ) : (
                      <Chip label="Pending" size="small" variant="outlined" />
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                      <Tooltip title="View details">
                        <IconButton size="small" onClick={() => handleViewDetails(item)}>
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      {!item.reviewed && (
                        <Tooltip title="Mark as reviewed">
                          <IconButton
                            size="small"
                            color="success"
                            onClick={() => handleReviewClick(item)}
                          >
                            <CheckCircleIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteClick(item)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Stack>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Flagged Content Details</DialogTitle>
        <DialogContent>
          {selectedItem && (
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Risk Score
                </Typography>
                <RiskBadge riskScore={selectedItem.riskScore} size="medium" />
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Flagged Text
                </Typography>
                <Typography variant="body1">{selectedItem.flaggedText}</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Problem Words ({selectedItem.flaggedWords.length})
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                  {selectedItem.flaggedWords.map((word, index) => (
                    <Chip key={index} label={word} size="small" color="error" />
                  ))}
                </Box>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Statistics
                </Typography>
                <Typography variant="body2">
                  Total Problem Words: {selectedItem.totalProblemWords} /{' '}
                  {selectedItem.totalWords} ({selectedItem.problemPercentage.toFixed(2)}%)
                </Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Content Source
                </Typography>
                <Chip
                  label={selectedItem.contentSource === 'regular' ? 'Regular' : 'Auto-Generated'}
                  size="small"
                />
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Flagged Date
                </Typography>
                <Typography variant="body2">
                  {new Date(selectedItem.flaggedAt).toLocaleString()}
                </Typography>
              </Box>
              {selectedItem.reviewed && (
                <>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Review Status
                    </Typography>
                    <Chip label="Reviewed" size="small" color="success" />
                  </Box>
                  {selectedItem.reviewedAt && (
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Reviewed Date
                      </Typography>
                      <Typography variant="body2">
                        {new Date(selectedItem.reviewedAt).toLocaleString()}
                      </Typography>
                    </Box>
                  )}
                  {selectedItem.notes && (
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Review Notes
                      </Typography>
                      <Typography variant="body2">{selectedItem.notes}</Typography>
                    </Box>
                  )}
                </>
              )}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Review Dialog */}
      <Dialog open={reviewDialogOpen} onClose={() => setReviewDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Review Flagged Content</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Mark this content as reviewed. You can optionally add notes about your review decision.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            label="Review Notes (optional)"
            fullWidth
            multiline
            rows={3}
            value={reviewNotes}
            onChange={(e) => setReviewNotes(e.target.value)}
            placeholder="Add any notes about why this content is acceptable or needs attention..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReviewDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleReviewSubmit} variant="contained" color="success">
            Mark as Reviewed
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Flagged Content</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this flagged content? This will also delete the original
            content item. This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} variant="contained" color="error">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

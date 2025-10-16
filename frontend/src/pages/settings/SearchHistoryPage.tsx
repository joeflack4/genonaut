/**
 * Page displaying user's complete search history with management options.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Button,
  Paper,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Pagination,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import SearchIcon from '@mui/icons-material/Search'
import { useCurrentUser } from '../../hooks'
import {
  useSearchHistory,
  useDeleteSearchHistory,
  useClearSearchHistory,
} from '../../hooks/useSearchHistory'

export function SearchHistoryPage() {
  const navigate = useNavigate()
  const { data: currentUser } = useCurrentUser()
  const [page, setPage] = useState(1)
  const pageSize = 20
  const [clearDialogOpen, setClearDialogOpen] = useState(false)

  const userId = currentUser?.id || ''
  const { data, isLoading, error } = useSearchHistory(userId, page, pageSize)
  const deleteHistoryMutation = useDeleteSearchHistory(userId)
  const clearHistoryMutation = useClearSearchHistory(userId)

  const handleExecuteSearch = (searchQuery: string) => {
    navigate(`/gallery?search=${encodeURIComponent(searchQuery)}`)
  }

  const handleDeleteItem = (historyId: number) => {
    deleteHistoryMutation.mutate(historyId)
  }

  const handleClearAll = () => {
    clearHistoryMutation.mutate(undefined, {
      onSuccess: () => {
        setClearDialogOpen(false)
      },
    })
  }

  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value)
  }

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress data-testid="search-history-loading" />
      </Box>
    )
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error" data-testid="search-history-error">
          Failed to load search history. Please try again later.
        </Alert>
      </Box>
    )
  }

  const items = data?.items || []
  const pagination = data?.pagination

  return (
    <Box data-testid="search-history-page" sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Search History
        </Typography>
        {items.length > 0 && (
          <Button
            variant="outlined"
            color="error"
            onClick={() => setClearDialogOpen(true)}
            data-testid="clear-all-button"
          >
            Clear All
          </Button>
        )}
      </Box>

      {items.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }} data-testid="search-history-empty">
          <Typography variant="body1" color="text.secondary">
            No search history yet. Start searching to build your history.
          </Typography>
        </Paper>
      ) : (
        <>
          <Paper>
            <List data-testid="search-history-list">
              {items.map((item) => (
                <ListItem
                  key={item.id}
                  data-testid={`search-history-item-${item.id}`}
                  secondaryAction={
                    <Box>
                      <IconButton
                        edge="end"
                        aria-label="execute search"
                        data-testid={`execute-search-${item.id}`}
                        onClick={() => handleExecuteSearch(item.search_query)}
                        sx={{ mr: 1 }}
                      >
                        <SearchIcon />
                      </IconButton>
                      <IconButton
                        edge="end"
                        aria-label="delete"
                        data-testid={`delete-item-${item.id}`}
                        onClick={() => handleDeleteItem(item.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  }
                >
                  <ListItemText
                    primary={item.search_query}
                    secondary={new Date(item.created_at).toLocaleString()}
                    data-testid={`search-history-text-${item.id}`}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>

          {pagination && pagination.total_pages > 1 && (
            <Box display="flex" justifyContent="center" mt={3}>
              <Pagination
                count={pagination.total_pages}
                page={page}
                onChange={handlePageChange}
                color="primary"
                data-testid="search-history-pagination"
              />
            </Box>
          )}
        </>
      )}

      <Dialog
        open={clearDialogOpen}
        onClose={() => setClearDialogOpen(false)}
        data-testid="clear-dialog"
      >
        <DialogTitle>Clear All Search History?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            This will permanently delete all your search history. This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClearDialogOpen(false)} data-testid="cancel-clear">
            Cancel
          </Button>
          <Button
            onClick={handleClearAll}
            color="error"
            variant="contained"
            data-testid="confirm-clear"
            disabled={clearHistoryMutation.isPending}
          >
            {clearHistoryMutation.isPending ? 'Clearing...' : 'Clear All'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

/**
 * Page displaying user's complete search history with management options.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  TextField,
  InputAdornment,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import SearchIcon from '@mui/icons-material/Search'
import CloseIcon from '@mui/icons-material/Close'
import { useCurrentUser } from '../../hooks'
import {
  useSearchHistory,
  useDeleteSearchHistory,
  useClearSearchHistory,
} from '../../hooks/useSearchHistory'

type SortField = 'search_query' | 'last_searched_at' | 'search_count'
type SortOrder = 'asc' | 'desc'

/**
 * Parse search query into phrases (quoted) and individual words
 */
function parseSearchQuery(query: string): { phrases: string[]; words: string[] } {
  const phrases: string[] = []
  const words: string[] = []

  // Extract quoted phrases
  const phraseRegex = /"([^"]+)"/g
  let match
  while ((match = phraseRegex.exec(query)) !== null) {
    phrases.push(match[1].toLowerCase())
  }

  // Remove quoted phrases from query to get individual words
  const remainingText = query.replace(phraseRegex, '').trim()
  if (remainingText) {
    const extractedWords = remainingText.toLowerCase().split(/\s+/).filter(w => w.length > 0)
    words.push(...extractedWords)
  }

  return { phrases, words }
}

/**
 * Check if a search query text matches the filter using trigram-like fuzzy matching
 * Supports both quoted phrases (exact substring match) and individual words
 */
function matchesSearchFilter(searchQueryText: string, filterQuery: string): boolean {
  if (!filterQuery.trim()) {
    return true
  }

  const { phrases, words } = parseSearchQuery(filterQuery)
  const lowerText = searchQueryText.toLowerCase()

  // All phrases must match (exact substring)
  for (const phrase of phrases) {
    if (!lowerText.includes(phrase)) {
      return false
    }
  }

  // All words must match (fuzzy trigram-like matching)
  for (const word of words) {
    // Simple trigram approach: check if most characters appear in order
    if (!fuzzyMatch(lowerText, word)) {
      return false
    }
  }

  return true
}

/**
 * Fuzzy match using a simple character-order approach (trigram-like)
 * Returns true if most characters from the word appear in the text in order
 */
function fuzzyMatch(text: string, word: string): boolean {
  // For short words (< 3 chars), require exact substring match
  if (word.length < 3) {
    return text.includes(word)
  }

  // For longer words, allow some fuzzy matching
  // Check if the word appears as a substring (exact match)
  if (text.includes(word)) {
    return true
  }

  // Check if characters appear in order (allows for typos/insertions)
  let textIndex = 0
  let matchedChars = 0

  for (const char of word) {
    const foundIndex = text.indexOf(char, textIndex)
    if (foundIndex !== -1) {
      matchedChars++
      textIndex = foundIndex + 1
    }
  }

  // Require at least 80% of characters to match in order
  return matchedChars / word.length >= 0.8
}

export function SearchHistoryPage() {
  const navigate = useNavigate()
  const { data: currentUser } = useCurrentUser()
  const [page, setPage] = useState(1)
  const pageSize = 20
  const [clearDialogOpen, setClearDialogOpen] = useState(false)
  const [sortField, setSortField] = useState<SortField>('last_searched_at')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const [searchFilter, setSearchFilter] = useState('')
  const [searchInputFocused, setSearchInputFocused] = useState(false)

  const userId = currentUser?.id || ''
  const { data, isLoading, error } = useSearchHistory(userId, page, pageSize)
  const deleteHistoryMutation = useDeleteSearchHistory(userId)
  const clearHistoryMutation = useClearSearchHistory(userId)

  const handleExecuteSearch = (searchQuery: string) => {
    navigate(`/gallery?search=${encodeURIComponent(searchQuery)}`)
  }

  const handleDeleteItem = (searchQuery: string) => {
    deleteHistoryMutation.mutate(searchQuery)
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

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Toggle sort order if clicking the same field
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      // Set new field with descending as default
      setSortField(field)
      setSortOrder('desc')
    }
  }

  const handleSearchInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchFilter(event.target.value)
  }

  const handleSearchSubmit = () => {
    // Search filter is applied automatically via filteredItems
    // This function is here for the magnifying glass click, but filtering happens on input change
  }

  const handleSearchKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      handleSearchSubmit()
    }
  }

  const handleClearSearch = () => {
    setSearchFilter('')
  }

  // Filter items based on search query
  const filteredItems = (data?.items || []).filter(item =>
    matchesSearchFilter(item.search_query, searchFilter)
  )

  // Sort filtered items locally
  const sortedItems = [...filteredItems].sort((a, b) => {
    let comparison = 0
    if (sortField === 'search_query') {
      comparison = a.search_query.localeCompare(b.search_query)
    } else if (sortField === 'last_searched_at') {
      comparison = new Date(a.last_searched_at).getTime() - new Date(b.last_searched_at).getTime()
    } else if (sortField === 'search_count') {
      comparison = a.search_count - b.search_count
    }
    return sortOrder === 'asc' ? comparison : -comparison
  })

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

  const items = sortedItems
  const pagination = data?.pagination

  return (
    <Box data-testid="search-history-page" sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Search History
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <TextField
            placeholder="Search searches..."
            value={searchFilter}
            onChange={handleSearchInputChange}
            onKeyPress={handleSearchKeyPress}
            onFocus={() => setSearchInputFocused(true)}
            onBlur={() => setSearchInputFocused(false)}
            size="small"
            data-testid="search-history-filter-input"
            sx={{ width: 300 }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  {searchFilter && (
                    <IconButton
                      aria-label="clear search"
                      onClick={handleClearSearch}
                      edge="end"
                      size="small"
                      data-testid="clear-search-button"
                    >
                      <CloseIcon fontSize="small" />
                    </IconButton>
                  )}
                  {(searchInputFocused || searchFilter) && (
                    <IconButton
                      aria-label="search"
                      onClick={handleSearchSubmit}
                      edge="end"
                      size="small"
                      data-testid="submit-search-button"
                    >
                      <SearchIcon fontSize="small" />
                    </IconButton>
                  )}
                </InputAdornment>
              ),
            }}
          />
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
      </Box>

      {items.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }} data-testid="search-history-empty">
          <Typography variant="body1" color="text.secondary">
            {searchFilter
              ? 'No search history matches your filter.'
              : 'No search history yet. Start searching to build your history.'}
          </Typography>
        </Paper>
      ) : (
        <>
          <TableContainer component={Paper} data-testid="search-history-table">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ width: '100%' }}>
                    <TableSortLabel
                      active={sortField === 'search_query'}
                      direction={sortField === 'search_query' ? sortOrder : 'desc'}
                      onClick={() => handleSort('search_query')}
                      data-testid="sort-search-text"
                    >
                      Search text
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ whiteSpace: 'nowrap', width: '1%' }}>
                    <TableSortLabel
                      active={sortField === 'search_count'}
                      direction={sortField === 'search_count' ? sortOrder : 'desc'}
                      onClick={() => handleSort('search_count')}
                      data-testid="sort-search-count"
                    >
                      Searches
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ whiteSpace: 'nowrap', width: '1%' }}>
                    <TableSortLabel
                      active={sortField === 'last_searched_at'}
                      direction={sortField === 'last_searched_at' ? sortOrder : 'desc'}
                      onClick={() => handleSort('last_searched_at')}
                      data-testid="sort-last-searched"
                    >
                      Last searched
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ width: '1%', padding: '8px' }} />
                  <TableCell sx={{ width: '1%', padding: '8px' }} />
                </TableRow>
              </TableHead>
              <TableBody>
                {items.map((item, index) => (
                  <TableRow
                    key={`${item.search_query}-${index}`}
                    data-testid={`search-history-item-${index}`}
                    hover
                  >
                    <TableCell data-testid={`search-history-text-${index}`}>
                      {item.search_query}
                    </TableCell>
                    <TableCell sx={{ whiteSpace: 'nowrap', textAlign: 'center' }}>
                      {item.search_count}
                    </TableCell>
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>
                      {new Date(item.last_searched_at).toLocaleString()}
                    </TableCell>
                    <TableCell sx={{ padding: '8px' }}>
                      <IconButton
                        aria-label="execute search"
                        data-testid={`execute-search-${index}`}
                        onClick={() => handleExecuteSearch(item.search_query)}
                        size="small"
                      >
                        <SearchIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                    <TableCell sx={{ padding: '8px' }}>
                      <IconButton
                        aria-label="delete"
                        data-testid={`delete-item-${index}`}
                        onClick={() => handleDeleteItem(item.search_query)}
                        size="small"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

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

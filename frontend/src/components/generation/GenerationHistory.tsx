import { useState, useMemo } from 'react'
import {
  Box,
  Grid,
  Typography,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Pagination,
  PaginationItem,
  Alert,
  CircularProgress,
  IconButton,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material'
import {
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import { GenerationCard } from './GenerationCard'
import { ImageViewer } from './ImageViewer'
import { VirtualScrollList } from '../common/VirtualScrollList'
import { useGenerationJobService } from '../../hooks/useGenerationJobService'
import type { GenerationJobResponse, GenerationJobListParams } from '../../services/generation-job-service'

export function GenerationHistory() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedGeneration, setSelectedGeneration] = useState<GenerationJobResponse | null>(null)
  const [viewerOpen, setViewerOpen] = useState(false)
  const [useVirtualScrolling, setUseVirtualScrolling] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generationsResponse, setGenerationsResponse] = useState<{ items: GenerationJobResponse[]; total: number } | null>(null)
  const [pendingDeleteId, setPendingDeleteId] = useState<number | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const { listGenerationJobs, deleteGenerationJob } = useGenerationJobService()

  const pageSize = useVirtualScrolling ? 100 : 12 // Load more items when using virtual scrolling

  // Build query parameters
  const queryParams = useMemo((): GenerationJobListParams => {
    const params: GenerationJobListParams = {
      skip: (page - 1) * pageSize,
      limit: pageSize,
      user_id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9', // TODO: Get from auth context
    }

    if (statusFilter) {
      params.status = statusFilter
    }

    return params
  }, [page, pageSize, statusFilter])

  // Fetch generations list
  const fetchGenerations = useMemo(() => async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await listGenerationJobs(queryParams)
      setGenerationsResponse(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch generations')
    } finally {
      setLoading(false)
    }
  }, [listGenerationJobs, queryParams])

  // Fetch on mount and when query params change
  useMemo(() => {
    fetchGenerations()
  }, [fetchGenerations])

  // Derived state - wrap generations in useMemo to prevent re-renders
  const generations = useMemo(() => {
    return generationsResponse?.items || []
  }, [generationsResponse?.items])

  const totalPages = generationsResponse ? Math.ceil(generationsResponse.total / pageSize) : 1

  const handleRefresh = () => {
    setPage(1)
    fetchGenerations()
  }

  const handleStatusFilterChange = (status: string) => {
    setStatusFilter(status)
    setPage(1)
  }

  const handleViewGeneration = (generation: GenerationJobResponse) => {
    setSelectedGeneration(generation)
    setViewerOpen(true)
  }

  const handleRequestDelete = (id: number) => {
    setPendingDeleteId(id)
    setDeleteError(null)
  }

  const handleConfirmDelete = async () => {
    if (pendingDeleteId === null || isDeleting) {
      return
    }

    setIsDeleting(true)
    setDeleteError(null)

    try {
      await deleteGenerationJob(pendingDeleteId)
      setPendingDeleteId(null)
      // Refresh the list after successful deletion
      fetchGenerations()
    } catch (error) {
      console.error('Failed to delete generation:', error)
      setDeleteError(error instanceof Error ? error.message : 'Failed to delete generation')
    } finally {
      setIsDeleting(false)
    }
  }

  const handleCancelDelete = () => {
    setPendingDeleteId(null)
    setDeleteError(null)
  }

  const handleDeleteGeneration = (id: number) => {
    handleRequestDelete(id)
  }

  const filteredGenerations = useMemo(() => {
    return generations.filter(gen =>
      searchTerm === '' ||
      gen.prompt.toLowerCase().includes(searchTerm.toLowerCase()) ||
      gen.checkpoint_model.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [generations, searchTerm])

  // Render generation card for virtual scrolling
  const renderGenerationCard = (generation: GenerationJobResponse) => (
    <Box sx={{ p: 1 }}>
      <GenerationCard
        generation={generation}
        onView={() => handleViewGeneration(generation)}
        onDelete={() => handleDeleteGeneration(generation.id)}
      />
    </Box>
  )

  if (loading && generations.length === 0) {
    return (
      <Box display="flex" alignItems="center" justifyContent="center" sx={{ py: 4 }}>
        <CircularProgress sx={{ mr: 2 }} />
        <Typography>Loading generations...</Typography>
      </Box>
    )
  }

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
          <Button onClick={handleRefresh} size="small" sx={{ ml: 1 }}>
            Retry
          </Button>
        </Alert>
      )}

      {/* Filters and Controls */}
      <Box display="flex" alignItems="center" gap={2} sx={{ mb: 3, flexWrap: 'wrap' }}>
        <TextField
          size="small"
          label="Search"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search prompts or models..."
          sx={{ minWidth: 200 }}
          inputProps={{ 'data-testid': 'search-input' }}
        />

        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={statusFilter}
            onChange={(e) => handleStatusFilterChange(e.target.value)}
            label="Status"
            inputProps={{ 'data-testid': 'status-filter-input' }}
            SelectDisplayProps={{ 'data-testid': 'status-filter' }}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="pending">Pending</MenuItem>
            <MenuItem value="running">Running</MenuItem>
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="failed">Failed</MenuItem>
            <MenuItem value="cancelled">Cancelled</MenuItem>
          </Select>
        </FormControl>

        <FormControlLabel
          control={
            <Switch
              checked={useVirtualScrolling}
              onChange={(e) => setUseVirtualScrolling(e.target.checked)}
              size="small"
              inputProps={{ 'data-testid': 'virtual-scroll-toggle' }}
            />
          }
          label="Virtual Scrolling"
          sx={{ ml: 1 }}
        />

        <IconButton onClick={handleRefresh} disabled={loading}>
          <RefreshIcon />
        </IconButton>
      </Box>

      {/* Generation Grid */}
      {filteredGenerations.length > 0 ? (
        <>
          {useVirtualScrolling ? (
            <Box data-testid="generation-list">
              <VirtualScrollList
                items={filteredGenerations}
                itemHeight={300} // Approximate height of a generation card
                containerHeight={600} // Fixed height for virtual scrolling
                renderItem={renderGenerationCard}
                overscan={3}
              />
            </Box>
          ) : (
            <Grid container spacing={2} data-testid="generation-list">
              {filteredGenerations.map((generation) => (
                <Grid key={generation.id} size={{ xs: 12, sm: 6, md: 4, lg: 3 }} data-testid="generation-list-item">
                  <GenerationCard
                    generation={generation}
                    onView={() => handleViewGeneration(generation)}
                    onDelete={() => handleDeleteGeneration(generation.id)}
                  />
                </Grid>
              ))}
            </Grid>
          )}

          {/* Pagination - only show for non-virtual scrolling */}
          {!useVirtualScrolling && totalPages > 1 && (
            <Box display="flex" justifyContent="center" sx={{ mt: 4 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_, newPage) => setPage(newPage)}
                color="primary"
                size="large"
                renderItem={(item) => (
                  <PaginationItem
                    {...item}
                    data-testid={
                      item.type === 'next'
                        ? 'next-page'
                        : item.type === 'previous'
                          ? 'previous-page'
                          : undefined
                    }
                  />
                )}
              />
            </Box>
          )}
        </>
      ) : (
        <Box
          display="flex"
          alignItems="center"
          justifyContent="center"
          flexDirection="column"
          sx={{ py: 8 }}
        >
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No generations found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {searchTerm || statusFilter
              ? 'Try adjusting your search or filters'
              : 'Create your first generation to see it here'}
          </Typography>
          {(searchTerm || statusFilter) && (
            <Button
              variant="outlined"
              onClick={() => {
                setSearchTerm('')
                setStatusFilter('')
              }}
            >
              Clear Filters
            </Button>
          )}
        </Box>
      )}

      {/* Loading Overlay */}
      {loading && generations.length > 0 && (
        <Box
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
          display="flex"
          alignItems="center"
          justifyContent="center"
          bgcolor="rgba(255, 255, 255, 0.7)"
          zIndex={1}
        >
          <CircularProgress />
        </Box>
      )}

      {/* Image Viewer Dialog */}
      {selectedGeneration && (
        <ImageViewer
          generation={selectedGeneration}
          open={viewerOpen}
          onClose={() => {
            setViewerOpen(false)
            setSelectedGeneration(null)
          }}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={pendingDeleteId !== null}
        onClose={handleCancelDelete}
        data-testid="generation-delete-dialog"
        disableRestoreFocus
      >
        <DialogTitle>Delete generation?</DialogTitle>
        <DialogContent>
          <Typography variant="body2">
            Are you sure you want to delete this generation? This action cannot be undone.
          </Typography>
          {deleteError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {deleteError}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={handleCancelDelete}
            disabled={isDeleting}
            data-testid="generation-delete-cancel"
          >
            Cancel
          </Button>
          <Button
            onClick={handleConfirmDelete}
            color="error"
            disabled={isDeleting}
            data-testid="generation-delete-confirm"
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

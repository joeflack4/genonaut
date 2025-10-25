import { useState, useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
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
import { VirtualScrollList } from '../common/VirtualScrollList'
import { ResolutionDropdown } from '../gallery/ResolutionDropdown'
import { useGenerationJobService } from '../../hooks/useGenerationJobService'
import { usePersistedState } from '../../hooks/usePersistedState'
import type { GenerationJobResponse, GenerationJobListParams } from '../../services/generation-job-service'
import type { ThumbnailResolutionId } from '../../types/domain'
import { DEFAULT_THUMBNAIL_RESOLUTION_ID, THUMBNAIL_RESOLUTION_OPTIONS } from '../../constants/gallery'

export function GenerationHistory() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState('')
  const [useVirtualScrolling, setUseVirtualScrolling] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generationsResponse, setGenerationsResponse] = useState<{ items: GenerationJobResponse[]; total: number } | null>(null)
  const [pendingDeleteId, setPendingDeleteId] = useState<number | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [resolutionId, setResolutionId] = usePersistedState<ThumbnailResolutionId>(
    'generation-history:resolution',
    DEFAULT_THUMBNAIL_RESOLUTION_ID
  )

  const navigate = useNavigate()
  const { listGenerationJobs, deleteGenerationJob } = useGenerationJobService()

  const resolution = useMemo(
    () => THUMBNAIL_RESOLUTION_OPTIONS.find((r) => r.id === resolutionId) || THUMBNAIL_RESOLUTION_OPTIONS[5],
    [resolutionId]
  )

  // Calculate items per row based on viewport width
  const [itemsPerRow, setItemsPerRow] = useState(4)

  useEffect(() => {
    const updateItemsPerRow = () => {
      const containerWidth = window.innerWidth - 64 // Account for padding
      const itemWidth = resolution.width + 16 // Card width + gap
      const calculatedItemsPerRow = Math.max(1, Math.floor(containerWidth / itemWidth))
      setItemsPerRow(calculatedItemsPerRow)
    }

    updateItemsPerRow()
    window.addEventListener('resize', updateItemsPerRow)
    return () => window.removeEventListener('resize', updateItemsPerRow)
  }, [resolution.width])

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
    if (generation.content_id) {
      navigate(`/view/${generation.content_id}`)
    }
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
      (gen.checkpoint_model && gen.checkpoint_model.toLowerCase().includes(searchTerm.toLowerCase()))
    )
  }, [generations, searchTerm])

  // Group generations into rows for virtual scrolling
  const generationRows = useMemo(() => {
    const rows = []
    for (let i = 0; i < filteredGenerations.length; i += itemsPerRow) {
      rows.push(filteredGenerations.slice(i, i + itemsPerRow))
    }
    return rows
  }, [filteredGenerations, itemsPerRow])

  // Calculate row height based on resolution and aspect ratio
  const rowHeight = useMemo(() => {
    const aspectRatio = resolution.height / resolution.width
    const cardHeight = resolution.width * aspectRatio + 200 // Add space for metadata
    return cardHeight + 16 // Add gap
  }, [resolution])

  // Render a row of generation cards for virtual scrolling
  const renderGenerationRow = (row: GenerationJobResponse[]) => (
    <Box
      sx={{
        display: 'grid',
        gap: 2,
        gridTemplateColumns: `repeat(${itemsPerRow}, minmax(${resolution.width}px, 1fr))`,
        alignItems: 'flex-start',
        px: 1,
      }}
    >
      {row.map((generation) => (
        <GenerationCard
          key={generation.id}
          generation={generation}
          resolution={resolution}
          onClick={() => handleViewGeneration(generation)}
          onDelete={() => handleDeleteGeneration(generation.id)}
        />
      ))}
    </Box>
  )

  const gridTemplateColumns = useMemo(
    () => `repeat(auto-fill, minmax(${resolution.width}px, 1fr))`,
    [resolution.width]
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

        <ResolutionDropdown
          currentResolution={resolutionId}
          onResolutionChange={setResolutionId}
          dataTestId="generation-history-resolution-dropdown"
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
                items={generationRows}
                itemHeight={rowHeight}
                containerHeight={window.innerHeight - 300} // Dynamic height based on viewport
                renderItem={renderGenerationRow}
                overscan={2}
              />
            </Box>
          ) : (
            <Box
              sx={{
                display: 'grid',
                gap: 2,
                gridTemplateColumns,
                alignItems: 'flex-start',
              }}
              data-testid="generation-list"
            >
              {filteredGenerations.map((generation) => (
                <Box key={generation.id} data-testid="generation-list-item">
                  <GenerationCard
                    generation={generation}
                    resolution={resolution}
                    onClick={() => handleViewGeneration(generation)}
                    onDelete={() => handleDeleteGeneration(generation.id)}
                  />
                </Box>
              ))}
            </Box>
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

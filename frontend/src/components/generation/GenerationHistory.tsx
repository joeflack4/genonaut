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
} from '@mui/material'
import {
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import { GenerationCard } from './GenerationCard'
import { ImageViewer } from './ImageViewer'
import { VirtualScrollList } from '../common/VirtualScrollList'
import { useGenerationsList } from '../../hooks/useCachedComfyUIService'
import type { ComfyUIGenerationResponse, ComfyUIGenerationListParams } from '../../services/comfyui-service'

export function GenerationHistory() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedGeneration, setSelectedGeneration] = useState<ComfyUIGenerationResponse | null>(null)
  const [viewerOpen, setViewerOpen] = useState(false)
  const [useVirtualScrolling, setUseVirtualScrolling] = useState(false)

  const pageSize = useVirtualScrolling ? 100 : 12 // Load more items when using virtual scrolling

  // Build query parameters
  const queryParams = useMemo((): ComfyUIGenerationListParams => {
    const params: ComfyUIGenerationListParams = {
      page,
      page_size: pageSize,
      user_id: 'demo-user', // TODO: Get from auth context
    }

    if (statusFilter) {
      params.status = statusFilter
    }

    return params
  }, [page, pageSize, statusFilter])

  // Use cached generations list
  const {
    data: generationsResponse,
    loading,
    error,
    refetch,
  } = useGenerationsList(queryParams)

  // Derived state - wrap generations in useMemo to prevent re-renders
  const generations = useMemo(() => {
    return generationsResponse?.items || []
  }, [generationsResponse?.items])

  const totalPages = generationsResponse ? Math.ceil(generationsResponse.pagination.total_count / pageSize) : 1

  const handleRefresh = () => {
    setPage(1)
    refetch()
  }

  const handleStatusFilterChange = (status: string) => {
    setStatusFilter(status)
    setPage(1)
  }

  const handleViewGeneration = (generation: ComfyUIGenerationResponse) => {
    setSelectedGeneration(generation)
    setViewerOpen(true)
  }

  const handleDeleteGeneration = async (id: number) => {
    // TODO: Implement delete functionality
    console.log('Delete generation:', id)
  }

  const filteredGenerations = useMemo(() => {
    return generations.filter(gen =>
      searchTerm === '' ||
      gen.prompt.toLowerCase().includes(searchTerm.toLowerCase()) ||
      gen.checkpoint_model.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [generations, searchTerm])

  // Render generation card for virtual scrolling
  const renderGenerationCard = (generation: ComfyUIGenerationResponse) => (
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
            <MenuItem value="processing">Processing</MenuItem>
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
    </Box>
  )
}

import { useState, useEffect } from 'react'
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
  Alert,
  CircularProgress,
  IconButton,
} from '@mui/material'
import {
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import { GenerationCard } from './GenerationCard'
import { ImageViewer } from './ImageViewer'
import { useComfyUIService } from '../../hooks/useComfyUIService'
import type { ComfyUIGenerationResponse, ComfyUIGenerationListParams } from '../../services/comfyui-service'

export function GenerationHistory() {
  const [generations, setGenerations] = useState<ComfyUIGenerationResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedGeneration, setSelectedGeneration] = useState<ComfyUIGenerationResponse | null>(null)
  const [viewerOpen, setViewerOpen] = useState(false)

  const { listGenerations } = useComfyUIService()
  const pageSize = 12

  useEffect(() => {
    loadGenerations()
  }, [page, statusFilter])

  const loadGenerations = async () => {
    setLoading(true)
    setError(null)

    try {
      const params: ComfyUIGenerationListParams = {
        page,
        page_size: pageSize,
        user_id: 'demo-user', // TODO: Get from auth context
      }

      if (statusFilter) {
        params.status = statusFilter
      }

      const response = await listGenerations(params)
      setGenerations(response.items)
      setTotalPages(Math.ceil(response.pagination.total_count / pageSize))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load generations')
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    setPage(1)
    loadGenerations()
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

  const filteredGenerations = generations.filter(gen =>
    searchTerm === '' ||
    gen.prompt.toLowerCase().includes(searchTerm.toLowerCase()) ||
    gen.checkpoint_model.toLowerCase().includes(searchTerm.toLowerCase())
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
      <Box display="flex" alignItems="center" gap={2} sx={{ mb: 3 }}>
        <TextField
          size="small"
          label="Search"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search prompts or models..."
          sx={{ minWidth: 200 }}
        />

        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={statusFilter}
            onChange={(e) => handleStatusFilterChange(e.target.value)}
            label="Status"
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="pending">Pending</MenuItem>
            <MenuItem value="processing">Processing</MenuItem>
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="failed">Failed</MenuItem>
            <MenuItem value="cancelled">Cancelled</MenuItem>
          </Select>
        </FormControl>

        <IconButton onClick={handleRefresh} disabled={loading}>
          <RefreshIcon />
        </IconButton>
      </Box>

      {/* Generation Grid */}
      {filteredGenerations.length > 0 ? (
        <>
          <Grid container spacing={2}>
            {filteredGenerations.map((generation) => (
              // @ts-ignore
              <Grid item xs={12} sm={6} md={4} lg={3} key={generation.id}>
                <GenerationCard
                  generation={generation}
                  onView={() => handleViewGeneration(generation)}
                  onDelete={() => handleDeleteGeneration(generation.id)}
                />
              </Grid>
            ))}
          </Grid>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box display="flex" justifyContent="center" sx={{ mt: 4 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_, newPage) => setPage(newPage)}
                color="primary"
                size="large"
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
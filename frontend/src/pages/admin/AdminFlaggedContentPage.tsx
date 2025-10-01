import { useState, useEffect, useCallback } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Drawer,
  IconButton,
  Pagination,
  Snackbar,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material'
import FilterListIcon from '@mui/icons-material/FilterList'
import RefreshIcon from '@mui/icons-material/Refresh'
import DeleteIcon from '@mui/icons-material/Delete'
import {
  FlaggedContentFilters,
  FlaggedContentTable,
} from '../../components/admin'
import { flaggedContentService } from '../../services'
import type { FlaggedContent, FlaggedContentFilters as Filters } from '../../types/domain'
import { ADMIN_USER_ID } from '../../constants/config'

const PAGE_SIZE = 10
const DRAWER_WIDTH = 320

export function AdminFlaggedContentPage() {
  const [items, setItems] = useState<FlaggedContent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [filtersOpen, setFiltersOpen] = useState(true)
  const [bulkDeleteDialogOpen, setBulkDeleteDialogOpen] = useState(false)
  const [filters, setFilters] = useState<Filters>({
    page: 1,
    pageSize: PAGE_SIZE,
    contentSource: 'all',
    minRiskScore: 0,
    maxRiskScore: 100,
    sortField: 'risk_score',
    sortOrder: 'desc',
  })

  const currentUserId = ADMIN_USER_ID

  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await flaggedContentService.listFlaggedContent(filters)
      setItems(result.items)
      setTotalPages(result.pagination.totalPages)
      setTotalCount(result.pagination.totalCount)
      setPage(result.pagination.page)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load flagged content')
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleFiltersChange = (newFilters: Filters) => {
    setFilters(newFilters)
    setSelectedIds([])
  }

  const handleClearFilters = () => {
    setFilters({
      page: 1,
      pageSize: PAGE_SIZE,
      contentSource: 'all',
      minRiskScore: 0,
      maxRiskScore: 100,
      sortField: 'risk_score',
      sortOrder: 'desc',
    })
    setSelectedIds([])
  }

  const handlePageChange = (_event: React.ChangeEvent<unknown>, newPage: number) => {
    setFilters({ ...filters, page: newPage })
    setSelectedIds([])
  }

  const handleReview = async (id: number, reviewed: boolean, notes?: string) => {
    try {
      await flaggedContentService.reviewFlaggedContent(id, {
        reviewed,
        reviewedBy: currentUserId,
        notes,
      })
      setSuccess('Content marked as reviewed')
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to review content')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await flaggedContentService.deleteFlaggedContent(id)
      setSuccess('Content deleted successfully')
      setSelectedIds(selectedIds.filter((selectedId) => selectedId !== id))
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete content')
    }
  }

  const handleBulkDelete = async () => {
    try {
      const result = await flaggedContentService.bulkDeleteFlaggedContent({
        ids: selectedIds,
      })

      if (result.errors.length > 0) {
        setError(
          `Deleted ${result.deletedCount} items. ${result.errors.length} errors occurred.`
        )
      } else {
        setSuccess(`Successfully deleted ${result.deletedCount} items`)
      }

      setSelectedIds([])
      setBulkDeleteDialogOpen(false)
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete content')
    }
  }

  const handleRefresh = () => {
    loadData()
  }

  return (
    <Box sx={{ display: 'flex', position: 'relative' }}>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { xs: '100%', md: `calc(100% - ${filtersOpen ? DRAWER_WIDTH : 0}px)` },
          transition: (theme) =>
            theme.transitions.create(['width', 'margin'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.leavingScreen,
            }),
        }}
      >
        <Stack spacing={3}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h4" component="h1" fontWeight={600}>
              Flagged Content Management
            </Typography>
            <Stack direction="row" spacing={1}>
              <Tooltip title="Refresh">
                <IconButton onClick={handleRefresh} disabled={loading}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title={filtersOpen ? 'Hide filters' : 'Show filters'}>
                <IconButton onClick={() => setFiltersOpen(!filtersOpen)}>
                  <FilterListIcon />
                </IconButton>
              </Tooltip>
            </Stack>
          </Box>

          {selectedIds.length > 0 && (
            <Card>
              <CardContent>
                <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between">
                  <Typography variant="body1">
                    {selectedIds.length} item{selectedIds.length !== 1 ? 's' : ''} selected
                  </Typography>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={() => setBulkDeleteDialogOpen(true)}
                  >
                    Delete Selected
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardContent>
              <Stack spacing={2}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    Showing {items.length} of {totalCount} flagged items
                  </Typography>
                </Box>

                {loading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
                    <CircularProgress />
                  </Box>
                ) : error ? (
                  <Alert severity="error">{error}</Alert>
                ) : (
                  <>
                    <FlaggedContentTable
                      items={items}
                      selectedIds={selectedIds}
                      onSelectionChange={setSelectedIds}
                      onReview={handleReview}
                      onDelete={handleDelete}
                      currentUserId={currentUserId}
                    />
                    {totalPages > 1 && (
                      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                        <Pagination
                          count={totalPages}
                          page={page}
                          onChange={handlePageChange}
                          color="primary"
                          shape="rounded"
                        />
                      </Box>
                    )}
                  </>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      </Box>

      <Drawer
        anchor="right"
        variant="persistent"
        open={filtersOpen}
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            boxSizing: 'border-box',
            p: 3,
            position: 'fixed',
          },
        }}
      >
        <FlaggedContentFilters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onClearFilters={handleClearFilters}
        />
      </Drawer>

      {/* Bulk Delete Confirmation Dialog */}
      <Dialog open={bulkDeleteDialogOpen} onClose={() => setBulkDeleteDialogOpen(false)}>
        <DialogTitle>Bulk Delete Flagged Content</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete {selectedIds.length} flagged item
            {selectedIds.length !== 1 ? 's' : ''}? This will also delete the original content items.
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleBulkDelete} variant="contained" color="error">
            Delete {selectedIds.length} Item{selectedIds.length !== 1 ? 's' : ''}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success Snackbar */}
      <Snackbar
        open={success !== null}
        autoHideDuration={4000}
        onClose={() => setSuccess(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSuccess(null)} severity="success" sx={{ width: '100%' }}>
          {success}
        </Alert>
      </Snackbar>

      {/* Error Snackbar */}
      <Snackbar
        open={error !== null}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setError(null)} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  )
}

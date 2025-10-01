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
    <Box sx={{ display: 'flex', position: 'relative' }} data-testid="admin-flagged-page-root">
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
        data-testid="admin-flagged-main"
      >
        <Stack spacing={3} data-testid="admin-flagged-content">
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }} data-testid="admin-flagged-header">
            <Typography variant="h4" component="h1" fontWeight={600} data-testid="admin-flagged-title">
              Flagged Content Management
            </Typography>
            <Stack direction="row" spacing={1} data-testid="admin-flagged-header-actions">
              <Tooltip title="Refresh">
                <IconButton onClick={handleRefresh} disabled={loading} data-testid="admin-flagged-refresh">
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title={filtersOpen ? 'Hide filters' : 'Show filters'}>
                <IconButton onClick={() => setFiltersOpen(!filtersOpen)} data-testid="admin-flagged-toggle-filters">
                  <FilterListIcon />
                </IconButton>
              </Tooltip>
            </Stack>
          </Box>

          {selectedIds.length > 0 && (
            <Card data-testid="admin-flagged-selection-card">
              <CardContent>
                <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between" data-testid="admin-flagged-selection-content">
                  <Typography variant="body1" data-testid="admin-flagged-selection-text">
                    {selectedIds.length} item{selectedIds.length !== 1 ? 's' : ''} selected
                  </Typography>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={() => setBulkDeleteDialogOpen(true)}
                    data-testid="admin-flagged-selection-delete"
                  >
                    Delete Selected
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          )}

          <Card data-testid="admin-flagged-table-card">
            <CardContent>
              <Stack spacing={2} data-testid="admin-flagged-table-section">
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }} data-testid="admin-flagged-summary">
                  <Typography variant="body2" color="text.secondary" data-testid="admin-flagged-summary-text">
                    Showing {items.length} of {totalCount} flagged items
                  </Typography>
                </Box>

                {loading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }} data-testid="admin-flagged-loading">
                    <CircularProgress data-testid="admin-flagged-loading-spinner" />
                  </Box>
                ) : error ? (
                  <Alert severity="error" data-testid="admin-flagged-error-alert">{error}</Alert>
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
                      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }} data-testid="admin-flagged-pagination">
                        <Pagination
                          count={totalPages}
                          page={page}
                          onChange={handlePageChange}
                          color="primary"
                          shape="rounded"
                          data-testid="admin-flagged-pagination-control"
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
        data-testid="admin-flagged-filters-drawer"
      >
        <FlaggedContentFilters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onClearFilters={handleClearFilters}
        />
      </Drawer>

      {/* Bulk Delete Confirmation Dialog */}
      <Dialog open={bulkDeleteDialogOpen} onClose={() => setBulkDeleteDialogOpen(false)} data-testid="admin-flagged-bulk-dialog">
        <DialogTitle data-testid="admin-flagged-bulk-dialog-title">Bulk Delete Flagged Content</DialogTitle>
        <DialogContent>
          <DialogContentText data-testid="admin-flagged-bulk-dialog-text">
            Are you sure you want to delete {selectedIds.length} flagged item
            {selectedIds.length !== 1 ? 's' : ''}? This will also delete the original content items.
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkDeleteDialogOpen(false)} data-testid="admin-flagged-bulk-dialog-cancel">Cancel</Button>
          <Button onClick={handleBulkDelete} variant="contained" color="error" data-testid="admin-flagged-bulk-dialog-confirm">
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
        data-testid="admin-flagged-success-snackbar"
      >
        <Alert onClose={() => setSuccess(null)} severity="success" sx={{ width: '100%' }} data-testid="admin-flagged-success-alert">
          {success}
        </Alert>
      </Snackbar>

      {/* Error Snackbar */}
      <Snackbar
        open={error !== null}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        data-testid="admin-flagged-error-snackbar"
      >
        <Alert onClose={() => setError(null)} severity="error" sx={{ width: '100%' }} data-testid="admin-flagged-error-alert">
          {error}
        </Alert>
      </Snackbar>
    </Box>
  )
}

import { useState } from 'react';
import {
  Box,
  Pagination,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Stack,
  IconButton,
  Tooltip,
} from '@mui/material';
import ListIcon from '@mui/icons-material/List';
import GridViewIcon from '@mui/icons-material/GridView';
import { useNavigate } from 'react-router-dom';
import { useEnhancedGalleryList, useCurrentUser } from '../../hooks';
import { GridView, ResolutionDropdown } from '../gallery';
import { ADMIN_USER_ID } from '../../constants/config';
import type { ThumbnailResolution, GalleryItem } from '../../types/domain';

const DEFAULT_PAGE_SIZE = 20;
const DEFAULT_RESOLUTION: ThumbnailResolution = { id: '256x256', width: 256, height: 256, label: '256x256' };

type SortOption = 'created_at' | 'quality_score';
type SortOrder = 'asc' | 'desc';
type ViewMode = 'grid' | 'list';

interface TagContentBrowserProps {
  /** Tag ID to filter content by */
  tagId: string;
  /** Tag name for display purposes */
  tagName?: string;
  /** Initial page size (default: 20) */
  pageSize?: number;
  /** Initial resolution (default: 256x256) */
  initialResolution?: ThumbnailResolution;
}

/**
 * TagContentBrowser Component
 *
 * Displays content items filtered by a specific tag.
 * Simplified version of the gallery page focused on a single tag.
 *
 * Features:
 * - Grid view with customizable thumbnail sizes
 * - List view option
 * - Pagination
 * - Sorting by date or quality
 * - Click to view content detail
 */
export function TagContentBrowser({
  tagId,
  tagName,
  pageSize = DEFAULT_PAGE_SIZE,
  initialResolution = DEFAULT_RESOLUTION,
}: TagContentBrowserProps) {
  const navigate = useNavigate();
  const { data: currentUser } = useCurrentUser();
  const userId = currentUser?.id ?? ADMIN_USER_ID;

  const [page, setPage] = useState(1);
  const [sortField, setSortField] = useState<SortOption>('created_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [resolution, setResolution] = useState<ThumbnailResolution>(initialResolution);

  // Fetch content filtered by this tag
  const {
    data: contentData,
    isLoading,
    isError,
    error,
  } = useEnhancedGalleryList({
    filters: {
      sortField,
      sortOrder,
      userId,
      tags: [tagId], // Filter by this tag only
      contentType: undefined, // Show all content types
    }
  });

  const totalPages = contentData?.pagination.total_pages ?? 0;
  const totalItems = contentData?.pagination.total_count ?? 0;
  const items = contentData?.items ?? [];

  const handlePageChange = (_event: React.ChangeEvent<unknown>, newPage: number) => {
    setPage(newPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSortChange = (event: any) => {
    const value = event.target.value as string;
    const [field, order] = value.split('-') as [SortOption, SortOrder];
    setSortField(field);
    setSortOrder(order);
    setPage(1); // Reset to first page on sort change
  };

  const handleItemClick = (item: GalleryItem) => {
    navigate(`/view/${item.id}`, {
      state: {
        fromGallery: true,
        fromTag: tagId,
        fromTagName: tagName,
      },
    });
  };

  const sortValue = `${sortField}-${sortOrder}`;

  return (
    <Box data-testid="tag-content-browser">
      {/* Header with view controls */}
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 3 }}
        data-testid="tag-content-browser-header"
      >
        <Typography variant="h6" color="text.secondary">
          {totalItems} {totalItems === 1 ? 'item' : 'items'}
          {tagName && ` tagged with "${tagName}"`}
        </Typography>

        <Stack direction="row" spacing={2} alignItems="center">
          {/* Sort dropdown */}
          <FormControl size="small" sx={{ minWidth: 200 }} data-testid="tag-content-sort-control">
            <InputLabel id="tag-content-sort-label">Sort</InputLabel>
            <Select
              labelId="tag-content-sort-label"
              value={sortValue}
              label="Sort"
              onChange={handleSortChange}
              data-testid="tag-content-sort-select"
            >
              <MenuItem value="created_at-desc">Newest First</MenuItem>
              <MenuItem value="created_at-asc">Oldest First</MenuItem>
              <MenuItem value="quality_score-desc">Highest Quality</MenuItem>
              <MenuItem value="quality_score-asc">Lowest Quality</MenuItem>
            </Select>
          </FormControl>

          {/* View mode toggle */}
          <Box data-testid="tag-content-view-toggle">
            <Tooltip title="List View">
              <IconButton
                color={viewMode === 'list' ? 'primary' : 'default'}
                onClick={() => setViewMode('list')}
                aria-pressed={viewMode === 'list'}
                data-testid="tag-content-list-view-button"
              >
                <ListIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Grid View">
              <IconButton
                color={viewMode === 'grid' ? 'primary' : 'default'}
                onClick={() => setViewMode('grid')}
                aria-pressed={viewMode === 'grid'}
                data-testid="tag-content-grid-view-button"
              >
                <GridViewIcon />
              </IconButton>
            </Tooltip>
          </Box>

          {/* Resolution dropdown (only show in grid view) */}
          {viewMode === 'grid' && (
            <ResolutionDropdown
              resolution={resolution.id}
              onResolutionChange={(resId) => {
                // Find the full resolution object from the ID
                const resolutions: ThumbnailResolution[] = [
                  { id: '256x256', width: 256, height: 256, label: '256x256' },
                  { id: '512x512', width: 512, height: 512, label: '512x512' },
                  { id: '512x768', width: 512, height: 768, label: '512x768' },
                ];
                const newRes = resolutions.find(r => r.id === resId) || DEFAULT_RESOLUTION;
                setResolution(newRes);
              }}
              dataTestId="tag-content-resolution-dropdown"
            />
          )}
        </Stack>
      </Stack>

      {/* Error state */}
      {isError && (
        <Typography color="error" sx={{ mb: 2 }} data-testid="tag-content-error">
          Error loading content: {error?.message ?? 'Unknown error'}
        </Typography>
      )}

      {/* Content grid or list */}
      {viewMode === 'grid' ? (
        <GridView
          items={items}
          resolution={resolution}
          isLoading={isLoading}
          onItemClick={handleItemClick}
          emptyMessage={
            tagName
              ? `No content found with tag "${tagName}"`
              : 'No content found with this tag'
          }
          dataTestId="tag-content-grid"
        />
      ) : (
        <Box data-testid="tag-content-list">
          {/* TODO: Implement list view - for now show a placeholder */}
          <Typography variant="body2" color="text.secondary">
            List view coming soon
          </Typography>
        </Box>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <Box
          sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}
          data-testid="tag-content-pagination"
        >
          <Pagination
            count={totalPages}
            page={page}
            onChange={handlePageChange}
            color="primary"
            showFirstButton
            showLastButton
          />
        </Box>
      )}
    </Box>
  );
}

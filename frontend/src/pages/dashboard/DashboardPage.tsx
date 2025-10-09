import { useState, useMemo } from 'react'
import {
  Box,
  Card,
  CardContent,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Skeleton,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material'
import ViewListIcon from '@mui/icons-material/ViewList'
import GridViewIcon from '@mui/icons-material/GridView'
import { useNavigate } from 'react-router-dom'
import { useGalleryList, useGalleryAutoList, useGalleryStats, useCurrentUser } from '../../hooks'
import { ADMIN_USER_ID } from '../../constants/config'
import type { GalleryItem, ThumbnailResolutionId, ViewMode } from '../../types/domain'
import {
  DASHBOARD_VIEW_MODE_STORAGE_KEY,
  DEFAULT_GRID_VIEW_MODE,
  DEFAULT_THUMBNAIL_RESOLUTION,
  DEFAULT_THUMBNAIL_RESOLUTION_ID,
  DEFAULT_VIEW_MODE,
  THUMBNAIL_RESOLUTION_OPTIONS,
} from '../../constants/gallery'
import { GridView as GalleryGridView, ResolutionDropdown } from '../../components/gallery'
import { loadViewMode, persistViewMode } from '../../utils/viewModeStorage'

const DEFAULT_USER_ID = ADMIN_USER_ID

const galleryStatItems = [
  { key: 'userGalleryCount' as const, label: 'Your gens' },
  { key: 'userAutoGalleryCount' as const, label: 'Your auto-gens' },
  { key: 'totalGalleryCount' as const, label: 'Community gens' },
  { key: 'totalAutoGalleryCount' as const, label: 'Community auto-gens' },
]

export function DashboardPage() {
  const { data: currentUser } = useCurrentUser()
  const userId = currentUser?.id ?? DEFAULT_USER_ID
  const navigate = useNavigate()

  const [viewMode, setViewMode] = useState<ViewMode>(() =>
    loadViewMode(DASHBOARD_VIEW_MODE_STORAGE_KEY, DEFAULT_VIEW_MODE)
  )

  const isGridView = viewMode.startsWith('grid-')

  const currentGridResolutionId = useMemo<ThumbnailResolutionId>(() => {
    if (isGridView) {
      const resolutionId = viewMode.slice(5) as ThumbnailResolutionId
      const exists = THUMBNAIL_RESOLUTION_OPTIONS.some((option) => option.id === resolutionId)
      if (exists) {
        return resolutionId
      }
    }
    return DEFAULT_THUMBNAIL_RESOLUTION_ID
  }, [isGridView, viewMode])

  const currentResolution = useMemo(
    () =>
      THUMBNAIL_RESOLUTION_OPTIONS.find((option) => option.id === currentGridResolutionId) ??
      DEFAULT_THUMBNAIL_RESOLUTION,
    [currentGridResolutionId]
  )

  const updateViewMode = (mode: ViewMode) => {
    setViewMode(mode)
    persistViewMode(DASHBOARD_VIEW_MODE_STORAGE_KEY, mode)
  }

  const handleSelectListView = () => {
    updateViewMode('list')
  }

  const handleSelectGridView = () => {
    const nextMode = isGridView ? viewMode : DEFAULT_GRID_VIEW_MODE
    updateViewMode(nextMode)
  }

  const handleResolutionChange = (resolutionId: ThumbnailResolutionId) => {
    const nextMode: ViewMode = `grid-${resolutionId}`
    updateViewMode(nextMode)
  }

  const navigateToDetail = (item: GalleryItem) => {
    navigate(`/view/${item.id}`, {
      state: {
        sourceType: item.sourceType,
        from: 'dashboard',
        fallbackPath: '/dashboard',
      },
    })
  }

  const { data: galleryStats, isLoading: galleryStatsLoading } = useGalleryStats(userId)

  // Your recent gens (regular content from content_items table)
  const { data: userRecentGallery, isLoading: userRecentGalleryLoading } = useGalleryList({
    limit: 5,
    sort: 'recent',
    creator_id: userId,
  })

  // Your recent auto-gens (from content_items_auto table)
  const { data: userRecentAutoGens, isLoading: userRecentAutoGensLoading } = useGalleryAutoList({
    limit: 5,
    sort: 'recent',
    creator_id: userId,
  })

  // Community recent gens (regular content from content_items table, excluding user's content)
  const { data: allRecentGallery, isLoading: recentGalleryLoading } = useGalleryList({
    limit: 20, // Get more to filter out user's content
    sort: 'recent',
  })

  // Community recent auto-gens (from content_items_auto table, excluding user's content)
  const { data: allRecentAutoGens, isLoading: communityRecentAutoGensLoading } = useGalleryAutoList({
    limit: 20, // Get more to filter out user's content
    sort: 'recent',
  })

  // Filter community content to exclude user's own content
  const recentGallery = allRecentGallery ? {
    ...allRecentGallery,
    items: allRecentGallery.items.filter(item => item.creatorId !== userId).slice(0, 5)
  } : undefined

  const communityRecentAutoGens = allRecentAutoGens ? {
    ...allRecentAutoGens,
    items: allRecentAutoGens.items.filter(item => item.creatorId !== userId).slice(0, 5)
  } : undefined

  return (
    <Stack spacing={4} component="section" data-testid="dashboard-page-root">
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        justifyContent="space-between"
        alignItems={{ xs: 'flex-start', sm: 'center' }}
        spacing={2}
        data-testid="dashboard-header"
      >
        <Typography
          component="h1"
          variant="h4"
          fontWeight={600}
          gutterBottom
          data-testid="dashboard-header-title"
        >
          Welcome back{currentUser?.name ? `, ${currentUser.name}` : ''}
        </Typography>
        <Stack direction="row" spacing={1} alignItems="center" data-testid="dashboard-view-toggle-group">
          <Tooltip title="List view" enterDelay={300} arrow>
            <IconButton
              aria-label="Switch to list view"
              color={isGridView ? 'default' : 'primary'}
              onClick={handleSelectListView}
              data-testid="dashboard-view-toggle-list"
              aria-pressed={!isGridView}
            >
              <ViewListIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Grid view" enterDelay={300} arrow>
            <IconButton
              aria-label="Switch to grid view"
              color={isGridView ? 'primary' : 'default'}
              onClick={handleSelectGridView}
              data-testid="dashboard-view-toggle-grid"
              aria-pressed={isGridView}
            >
              <GridViewIcon />
            </IconButton>
          </Tooltip>
          {isGridView && (
            <ResolutionDropdown
              currentResolution={currentGridResolutionId}
              onResolutionChange={handleResolutionChange}
              dataTestId="dashboard-resolution-dropdown"
            />
          )}
        </Stack>
      </Stack>

      <Box
        component="section"
        sx={{
          display: 'grid',
          gap: 3,
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))', lg: 'repeat(4, minmax(0, 1fr))' },
        }}
        data-testid="dashboard-stat-grid"
      >
        {galleryStatItems.map(({ key, label }) => (
          <Card
            key={key}
            sx={{ height: '100%', bgcolor: 'background.paper' }}
            data-testid={`dashboard-stat-card-${key}`}
          >
            <CardContent>
              <Typography
                variant="subtitle2"
                color="text.secondary"
                gutterBottom
                data-testid={`dashboard-stat-card-${key}-label`}
              >
                {label}
              </Typography>
              {galleryStatsLoading ? (
                <Skeleton variant="text" height={48} width={80} data-testid={`dashboard-stat-card-${key}-loading`} />
              ) : (
                <Typography
                  variant="h4"
                  fontWeight={600}
                  data-testid={`dashboard-stat-card-${key}-value`}
                >
                  {galleryStats ? galleryStats[key].toLocaleString() : '—'}
                </Typography>
              )}
            </CardContent>
          </Card>
        ))}
      </Box>

      <Card component="section" data-testid="dashboard-user-recent-card">
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom data-testid="dashboard-user-recent-title">
            Your recent gens
          </Typography>
          {isGridView ? (
            <GalleryGridView
              items={userRecentGallery?.items ?? []}
              resolution={currentResolution}
              isLoading={userRecentGalleryLoading}
              onItemClick={navigateToDetail}
              loadingPlaceholderCount={3}
              dataTestId="dashboard-user-recent-grid"
              emptyMessage="No recent gens available."
            />
          ) : userRecentGalleryLoading ? (
            <Stack spacing={2} data-testid="dashboard-user-recent-loading">
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} variant="rectangular" height={56} data-testid={`dashboard-user-recent-skeleton-${index}`} />
              ))}
            </Stack>
          ) : userRecentGallery && userRecentGallery.items.length > 0 ? (
            <List data-testid="dashboard-user-recent-list">
              {userRecentGallery.items.map((item) => (
                <ListItem
                  key={item.id}
                  disablePadding
                  disableGutters
                  divider
                  data-testid={`dashboard-user-recent-item-${item.id}`}
                >
                  <ListItemButton onClick={() => navigateToDetail(item)} data-testid={`dashboard-user-recent-item-${item.id}-button`}>
                    <ListItemText
                      primary={item.title}
                      secondary={item.createdAt ? new Date(item.createdAt).toLocaleString() : undefined}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary" data-testid="dashboard-user-recent-empty">
              No recent content available.
            </Typography>
          )}
        </CardContent>
      </Card>

      <Card component="section" data-testid="dashboard-user-autogens-card">
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom data-testid="dashboard-user-autogens-title">
            Your recent auto-gens
          </Typography>
          {isGridView ? (
            <GalleryGridView
              items={userRecentAutoGens?.items ?? []}
              resolution={currentResolution}
              isLoading={userRecentAutoGensLoading}
              onItemClick={navigateToDetail}
              loadingPlaceholderCount={3}
              dataTestId="dashboard-user-autogens-grid"
              emptyMessage="No recent auto-gens available."
            />
          ) : userRecentAutoGensLoading ? (
            <Stack spacing={2} data-testid="dashboard-user-autogens-loading">
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} variant="rectangular" height={56} data-testid={`dashboard-user-autogens-skeleton-${index}`} />
              ))}
            </Stack>
          ) : userRecentAutoGens && userRecentAutoGens.items.length > 0 ? (
            <List data-testid="dashboard-user-autogens-list">
              {userRecentAutoGens.items.map((item) => (
                <ListItem
                  key={item.id}
                  disablePadding
                  disableGutters
                  divider
                  data-testid={`dashboard-user-autogens-item-${item.id}`}
                >
                  <ListItemButton onClick={() => navigateToDetail(item)} data-testid={`dashboard-user-autogens-item-${item.id}-button`}>
                    <ListItemText
                      primary={item.title}
                      secondary={item.createdAt ? new Date(item.createdAt).toLocaleString() : undefined}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary" data-testid="dashboard-user-autogens-empty">
              No recent auto-gens available.
            </Typography>
          )}
        </CardContent>
      </Card>

      <Card component="section" data-testid="dashboard-community-recent-card">
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom data-testid="dashboard-community-recent-title">
            Community recent gens
          </Typography>
          {isGridView ? (
            <GalleryGridView
              items={recentGallery?.items ?? []}
              resolution={currentResolution}
              isLoading={recentGalleryLoading}
              onItemClick={navigateToDetail}
              loadingPlaceholderCount={3}
              dataTestId="dashboard-community-recent-grid"
              emptyMessage="No community gens available."
            />
          ) : recentGalleryLoading ? (
            <Stack spacing={2} data-testid="dashboard-community-recent-loading">
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} variant="rectangular" height={56} data-testid={`dashboard-community-recent-skeleton-${index}`} />
              ))}
            </Stack>
          ) : recentGallery && recentGallery.items.length > 0 ? (
            <List data-testid="dashboard-community-recent-list">
              {recentGallery.items.map((item) => (
                <ListItem
                  key={item.id}
                  disablePadding
                  disableGutters
                  divider
                  data-testid={`dashboard-community-recent-item-${item.id}`}
                >
                  <ListItemButton onClick={() => navigateToDetail(item)} data-testid={`dashboard-community-recent-item-${item.id}-button`}>
                    <ListItemText
                      primary={item.title}
                      secondary={item.createdAt ? new Date(item.createdAt).toLocaleString() : undefined}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary" data-testid="dashboard-community-recent-empty">
              No Community recent gens available.
            </Typography>
          )}
        </CardContent>
      </Card>

      <Card component="section" data-testid="dashboard-community-autogens-card">
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom data-testid="dashboard-community-autogens-title">
            Community recent auto-gens
          </Typography>
          {isGridView ? (
            <GalleryGridView
              items={communityRecentAutoGens?.items ?? []}
              resolution={currentResolution}
              isLoading={communityRecentAutoGensLoading}
              onItemClick={navigateToDetail}
              loadingPlaceholderCount={3}
              dataTestId="dashboard-community-autogens-grid"
              emptyMessage="No community auto-gens available."
            />
          ) : communityRecentAutoGensLoading ? (
            <Stack spacing={2} data-testid="dashboard-community-autogens-loading">
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} variant="rectangular" height={56} data-testid={`dashboard-community-autogens-skeleton-${index}`} />
              ))}
            </Stack>
          ) : communityRecentAutoGens && communityRecentAutoGens.items.length > 0 ? (
            <List data-testid="dashboard-community-autogens-list">
              {communityRecentAutoGens.items.map((item) => (
                <ListItem
                  key={item.id}
                  disablePadding
                  disableGutters
                  divider
                  data-testid={`dashboard-community-autogens-item-${item.id}`}
                >
                  <ListItemButton onClick={() => navigateToDetail(item)} data-testid={`dashboard-community-autogens-item-${item.id}-button`}>
                    <ListItemText
                      primary={item.title}
                      secondary={item.createdAt ? new Date(item.createdAt).toLocaleString() : undefined}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary" data-testid="dashboard-community-autogens-empty">
              No community recent auto-gens available.
            </Typography>
          )}
        </CardContent>
      </Card>
    </Stack>
  )
}

import { Box, Card, CardContent, List, ListItem, ListItemText, Skeleton, Stack, Typography } from '@mui/material'
import { useGalleryList, useGalleryAutoList, useGalleryStats, useCurrentUser } from '../../hooks'
import { ADMIN_USER_ID } from '../../constants/config'

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
      <Stack spacing={1} data-testid="dashboard-header">
        <Typography
          component="h1"
          variant="h4"
          fontWeight={600}
          gutterBottom
          data-testid="dashboard-header-title"
        >
          Welcome back{currentUser?.name ? `, ${currentUser.name}` : ''}
        </Typography>
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
          {userRecentGalleryLoading ? (
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
                  disableGutters
                  divider
                  data-testid={`dashboard-user-recent-item-${item.id}`}
                >
                  <ListItemText
                    primary={item.title}
                    secondary={item.createdAt ? new Date(item.createdAt).toLocaleString() : undefined}
                  />
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
          {userRecentAutoGensLoading ? (
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
                  disableGutters
                  divider
                  data-testid={`dashboard-user-autogens-item-${item.id}`}
                >
                  <ListItemText
                    primary={item.title}
                    secondary={item.createdAt ? new Date(item.createdAt).toLocaleString() : undefined}
                  />
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
          {recentGalleryLoading ? (
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
                  disableGutters
                  divider
                  data-testid={`dashboard-community-recent-item-${item.id}`}
                >
                  <ListItemText
                    primary={item.title}
                    secondary={item.createdAt ? new Date(item.createdAt).toLocaleString() : undefined}
                  />
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
          {communityRecentAutoGensLoading ? (
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
                  disableGutters
                  divider
                  data-testid={`dashboard-community-autogens-item-${item.id}`}
                >
                  <ListItemText
                    primary={item.title}
                    secondary={item.createdAt ? new Date(item.createdAt).toLocaleString() : undefined}
                  />
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

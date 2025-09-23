import { Box, Card, CardContent, List, ListItem, ListItemText, Skeleton, Stack, Typography } from '@mui/material'
import { useGalleryList, useGalleryAutoList, useGalleryStats, useCurrentUser } from '../../hooks'
import { ADMIN_USER_ID } from '../../constants/config'

const DEFAULT_USER_ID = ADMIN_USER_ID

const galleryStatItems = [
  { key: 'userGalleryCount' as const, label: 'Your gens' },
  { key: 'totalGalleryCount' as const, label: 'Community gens' },
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
    <Stack spacing={4} component="section">
      <Stack spacing={1}>
        <Typography component="h1" variant="h4" fontWeight={600} gutterBottom>
          Welcome back{currentUser?.name ? `, ${currentUser.name}` : ''}
        </Typography>
      </Stack>

      <Box
        component="section"
        sx={{
          display: 'grid',
          gap: 3,
          gridTemplateColumns: { xs: '1fr', md: 'repeat(2, minmax(0, 1fr))' },
        }}
      >
        {galleryStatItems.map(({ key, label }) => (
          <Card key={key} sx={{ height: '100%', bgcolor: 'background.paper' }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                {label}
              </Typography>
              {galleryStatsLoading ? (
                <Skeleton variant="text" height={48} width={80} />
              ) : (
                <Typography variant="h4" fontWeight={600}>
                  {galleryStats ? galleryStats[key] : '—'}
                </Typography>
              )}
            </CardContent>
          </Card>
        ))}
      </Box>

      <Card component="section">
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom>
            Your recent gens
          </Typography>
          {userRecentGalleryLoading ? (
            <Stack spacing={2}>
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} variant="rectangular" height={56} />
              ))}
            </Stack>
          ) : userRecentGallery && userRecentGallery.items.length > 0 ? (
            <List>
              {userRecentGallery.items.map((item) => (
                <ListItem key={item.id} disableGutters divider>
                  <ListItemText
                    primary={item.title}
                    secondary={item.createdAt ? new Date(item.createdAt).toLocaleString() : undefined}
                  />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No recent works available.
            </Typography>
          )}
        </CardContent>
      </Card>

      <Card component="section">
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom>
            Your recent auto-gens
          </Typography>
          {userRecentAutoGensLoading ? (
            <Stack spacing={2}>
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} variant="rectangular" height={56} />
              ))}
            </Stack>
          ) : userRecentAutoGens && userRecentAutoGens.items.length > 0 ? (
            <List>
              {userRecentAutoGens.items.map((item) => (
                <ListItem key={item.id} disableGutters divider>
                  <ListItemText
                    primary={item.title}
                    secondary={item.createdAt ? new Date(item.createdAt).toLocaleString() : undefined}
                  />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No recent auto-gens available.
            </Typography>
          )}
        </CardContent>
      </Card>

      <Card component="section">
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom>
            Community recent gens
          </Typography>
          {recentGalleryLoading ? (
            <Stack spacing={2}>
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} variant="rectangular" height={56} />
              ))}
            </Stack>
          ) : recentGallery && recentGallery.items.length > 0 ? (
            <List>
              {recentGallery.items.map((item) => (
                <ListItem key={item.id} disableGutters divider>
                  <ListItemText
                    primary={item.title}
                    secondary={item.createdAt ? new Date(item.createdAt).toLocaleString() : undefined}
                  />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No Community recent gens available.
            </Typography>
          )}
        </CardContent>
      </Card>

      <Card component="section">
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom>
            Community recent auto-gens
          </Typography>
          {communityRecentAutoGensLoading ? (
            <Stack spacing={2}>
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} variant="rectangular" height={56} />
              ))}
            </Stack>
          ) : communityRecentAutoGens && communityRecentAutoGens.items.length > 0 ? (
            <List>
              {communityRecentAutoGens.items.map((item) => (
                <ListItem key={item.id} disableGutters divider>
                  <ListItemText
                    primary={item.title}
                    secondary={item.createdAt ? new Date(item.createdAt).toLocaleString() : undefined}
                  />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No community recent auto-gens available.
            </Typography>
          )}
        </CardContent>
      </Card>
    </Stack>
  )
}

import { Box, Card, CardContent, List, ListItem, ListItemText, Skeleton, Stack, Typography } from '@mui/material'
import { useGalleryList, useGalleryStats, useCurrentUser } from '../../hooks'

const DEFAULT_USER_ID = 1

const galleryStatItems = [
  { key: 'userGalleryCount' as const, label: 'Your works' },
  { key: 'totalGalleryCount' as const, label: 'Community works' },
]

export function DashboardPage() {
  const { data: currentUser } = useCurrentUser()
  const userId = currentUser?.id ?? DEFAULT_USER_ID

  const { data: galleryStats, isLoading: galleryStatsLoading } = useGalleryStats(userId)
  const { data: userRecentGallery, isLoading: userRecentGalleryLoading } = useGalleryList({
    limit: 5,
    sort: 'recent',
    creator_id: userId,
  })
  // TODO: Replace with actual auto-gen filtering when API supports it
  const { data: userRecentAutoGens, isLoading: userRecentAutoGensLoading } = useGalleryList({
    limit: 5,
    sort: 'recent',
    creator_id: userId,
  })
  const { data: recentGallery, isLoading: recentGalleryLoading } = useGalleryList({
    limit: 5,
    sort: 'recent',
  })
  // TODO: Replace with actual auto-gen filtering when API supports it
  const { data: communityRecentAutoGens, isLoading: communityRecentAutoGensLoading } = useGalleryList({
    limit: 5,
    sort: 'recent',
  })

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
            Your recent works
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
            Community recent works
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
              No community recent works available.
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

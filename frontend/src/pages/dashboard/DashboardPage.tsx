import { Box, Card, CardContent, List, ListItem, ListItemText, Skeleton, Stack, Typography } from '@mui/material'
import { useContentList, useContentStats, useCurrentUser } from '../../hooks'

const DEFAULT_USER_ID = 1

const contentStatItems = [
  { key: 'userContentCount' as const, label: 'User Content' },
  { key: 'totalContentCount' as const, label: 'Community Content' },
]

export function DashboardPage() {
  const { data: currentUser } = useCurrentUser()
  const userId = currentUser?.id ?? DEFAULT_USER_ID

  const { data: contentStats, isLoading: contentStatsLoading } = useContentStats(userId)
  const { data: recentContent, isLoading: recentContentLoading } = useContentList({
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
        {contentStatItems.map(({ key, label }) => (
          <Card key={key} sx={{ height: '100%', bgcolor: 'background.paper' }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                {label}
              </Typography>
              {contentStatsLoading ? (
                <Skeleton variant="text" height={48} width={80} />
              ) : (
                <Typography variant="h4" fontWeight={600}>
                  {contentStats ? contentStats[key] : '—'}
                </Typography>
              )}
            </CardContent>
          </Card>
        ))}
      </Box>

      <Card component="section">
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom>
            Recent Content
          </Typography>
          {recentContentLoading ? (
            <Stack spacing={2}>
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} variant="rectangular" height={56} />
              ))}
            </Stack>
          ) : recentContent && recentContent.items.length > 0 ? (
            <List>
              {recentContent.items.map((item) => (
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
              No recent content available.
            </Typography>
          )}
        </CardContent>
      </Card>
    </Stack>
  )
}

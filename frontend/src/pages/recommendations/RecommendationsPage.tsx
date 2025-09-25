import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  List,
  ListItem,
  ListItemText,
  Skeleton,
  Stack,
  Typography,
} from '@mui/material'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import PendingIcon from '@mui/icons-material/Pending'
import { useCurrentUser, useRecommendations, useServeRecommendation } from '../../hooks'
import { ADMIN_USER_ID } from '../../constants/config'

const DEFAULT_USER_ID = ADMIN_USER_ID

export function RecommendationsPage() {
  const { data: currentUser } = useCurrentUser()
  const userId = currentUser?.id ?? DEFAULT_USER_ID

  const { data: recommendations, isLoading } = useRecommendations(Number(userId))
  const { mutateAsync: markServed, isPending } = useServeRecommendation(Number(userId))

  const handleMarkServed = (id: number) => markServed(id)

  return (
    <Stack spacing={4} component="section">
      <Stack spacing={1}>
        <Typography component="h1" variant="h4" fontWeight={600} gutterBottom>
          Recommendations
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Review generated recommendations and mark the ones you have actioned.
        </Typography>
      </Stack>

      <Card>
        <CardContent>
          {isLoading ? (
            <Stack spacing={2}>
              {Array.from({ length: 4 }).map((_, index) => (
                <Skeleton key={index} variant="rectangular" height={72} />
              ))}
            </Stack>
          ) : recommendations && recommendations.length > 0 ? (
            <List>
              {recommendations.map((recommendation) => {
                const served = Boolean(recommendation.servedAt)

                return (
                  <ListItem
                    key={recommendation.id}
                    divider
                    alignItems="flex-start"
                    secondaryAction={
                      served ? null : (
                        <Button
                          variant="outlined"
                          onClick={() => handleMarkServed(recommendation.id)}
                          disabled={isPending}
                        >
                          Mark as served
                        </Button>
                      )
                    }
                  >
                    <ListItemText
                      primary={
                        <Stack direction="row" spacing={2} alignItems="center">
                          <Typography variant="h6" component="span">
                            Recommendation #{recommendation.id}
                          </Typography>
                          <Chip
                            label={recommendation.algorithm}
                            color="primary"
                            variant="outlined"
                            size="small"
                          />
                        </Stack>
                      }
                      secondary={
                        <Box sx={{ mt: 1, display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                          <Typography variant="body2" color="text.secondary" component="span">
                            Score {(recommendation.score * 100).toFixed(0)}%
                          </Typography>
                          <Stack direction="row" spacing={1} alignItems="center">
                            {served ? (
                              <CheckCircleIcon fontSize="small" color="success" />
                            ) : (
                              <PendingIcon fontSize="small" color="warning" />
                            )}
                            <Typography variant="body2" color="text.secondary" component="span">
                              {served
                                ? `Served ${new Date(recommendation.servedAt as string).toLocaleString()}`
                                : `Created ${new Date(recommendation.createdAt).toLocaleString()}`}
                            </Typography>
                          </Stack>
                        </Box>
                      }
                      primaryTypographyProps={{ component: 'span' }}
                      secondaryTypographyProps={{ component: 'span' }}
                    />
                  </ListItem>
                )
              })}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No recommendations available. Generate new recommendations to populate this list.
            </Typography>
          )}
        </CardContent>
      </Card>
    </Stack>
  )
}

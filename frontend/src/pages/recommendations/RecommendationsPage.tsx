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

  const { data: recommendations, isLoading } = useRecommendations(userId)
  const { mutateAsync: markServed, isPending } = useServeRecommendation(userId)

  const handleMarkServed = (id: number) => markServed(id)

  return (
    <Stack spacing={4} component="section" data-testid="recommendations-page-root">
      <Stack spacing={1} data-testid="recommendations-header">
        <Typography component="h1" variant="h4" fontWeight={600} gutterBottom data-testid="recommendations-title">
          Recommendations
        </Typography>
        <Typography variant="body2" color="text.secondary" data-testid="recommendations-subtitle">
          Review generated recommendations and mark the ones you have actioned.
        </Typography>
      </Stack>

      <Card data-testid="recommendations-card">
        <CardContent>
          {isLoading ? (
            <Stack spacing={2} data-testid="recommendations-loading">
              {Array.from({ length: 4 }).map((_, index) => (
                <Skeleton
                  key={index}
                  variant="rectangular"
                  height={72}
                  data-testid={`recommendations-skeleton-${index}`}
                />
              ))}
            </Stack>
          ) : recommendations && recommendations.length > 0 ? (
            <List data-testid="recommendations-list">
              {recommendations.map((recommendation) => {
                const served = Boolean(recommendation.servedAt)

                return (
                  <ListItem
                    key={recommendation.id}
                    divider
                    alignItems="flex-start"
                    data-testid={`recommendations-item-${recommendation.id}`}
                    secondaryAction={
                      served ? null : (
                        <Button
                          variant="outlined"
                          onClick={() => handleMarkServed(recommendation.id)}
                          disabled={isPending}
                          data-testid={`recommendations-serve-button-${recommendation.id}`}
                        >
                          Mark as served
                        </Button>
                      )
                    }
                  >
                    <ListItemText
                      primary={
                        <Stack direction="row" spacing={2} alignItems="center" data-testid={`recommendations-item-${recommendation.id}-header`}>
                          <Typography variant="h6" component="span" data-testid={`recommendations-item-${recommendation.id}-title`}>
                            Recommendation #{recommendation.id}
                          </Typography>
                          <Chip
                            label={recommendation.algorithm}
                            color="primary"
                            variant="outlined"
                            size="small"
                            data-testid={`recommendations-item-${recommendation.id}-algorithm`}
                          />
                        </Stack>
                      }
                      secondary={
                        <Box
                          sx={{ mt: 1, display: 'flex', flexDirection: 'column', gap: 0.5 }}
                          data-testid={`recommendations-item-${recommendation.id}-details`}
                        >
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            component="span"
                            data-testid={`recommendations-item-${recommendation.id}-score`}
                          >
                            Score {(recommendation.score * 100).toFixed(0)}%
                          </Typography>
                          <Stack
                            direction="row"
                            spacing={1}
                            alignItems="center"
                            data-testid={`recommendations-item-${recommendation.id}-status`}
                          >
                            {served ? (
                              <CheckCircleIcon fontSize="small" color="success" data-testid={`recommendations-item-${recommendation.id}-served-icon`} />
                            ) : (
                              <PendingIcon fontSize="small" color="warning" data-testid={`recommendations-item-${recommendation.id}-pending-icon`} />
                            )}
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              component="span"
                              data-testid={`recommendations-item-${recommendation.id}-timestamp`}
                            >
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
            <Typography variant="body2" color="text.secondary" data-testid="recommendations-empty">
              No recommendations available. Generate new recommendations to populate this list.
            </Typography>
          )}
        </CardContent>
      </Card>
    </Stack>
  )
}

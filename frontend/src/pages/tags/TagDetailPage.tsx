import { useState } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import { useTagDetail, useRateTag, useCurrentUser } from '../../hooks';
import { StarRating } from '../../components/tags/StarRating';
import { TagContentBrowser } from '../../components/tags/TagContentBrowser';
import { ADMIN_USER_ID } from '../../constants/config';

interface TagDetailLocationState {
  from?: 'tags' | 'gallery' | 'hierarchy';
  fallbackPath?: string;
}

const DEFAULT_FALLBACK_PATH = '/gallery';

/**
 * TagDetailPage Component
 *
 * Displays detailed information about a single tag including:
 * - Tag name and hierarchy (parents/children)
 * - User rating and average rating
 * - Interactive rating widget
 * - Content browser filtered by this tag
 */
export function TagDetailPage() {
  const params = useParams<{ tagId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { data: currentUser } = useCurrentUser();
  const userId = currentUser?.id ?? ADMIN_USER_ID;

  const [showContentBrowser, setShowContentBrowser] = useState(false);

  const state = (location.state as TagDetailLocationState | undefined) ?? {};
  const fallbackPath = state.fallbackPath ?? (state.from === 'gallery' ? '/gallery' : DEFAULT_FALLBACK_PATH);

  const tagName = params.tagId ?? '';

  // Fetch tag details (backend accepts both UUID and name)
  const { data: tagDetail, isLoading, error } = useTagDetail(tagName, userId);

  // Rating mutation
  const rateTagMutation = useRateTag();

  const handleBack = () => {
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate(fallbackPath);
    }
  };

  const handleRatingChange = (newRating: number | null) => {
    if (newRating !== null && tagDetail?.tag.id) {
      rateTagMutation.mutate(
        {
          tagId: tagDetail.tag.id,
          params: {
            user_id: userId,
            rating: newRating
          }
        },
        {
          onError: (error) => {
            console.error('Failed to rate tag:', error);
            // TODO: Show error toast/snackbar
          },
        }
      );
    }
  };

  const handleParentClick = (parentName: string) => {
    navigate(`/tags/${parentName}`, {
      state: {
        from: 'tags',
        fallbackPath: `/tags/${tagName}`,
      },
    });
  };

  const handleChildClick = (childName: string) => {
    navigate(`/tags/${childName}`, {
      state: {
        from: 'tags',
        fallbackPath: `/tags/${tagName}`,
      },
    });
  };

  const handleBrowseContent = () => {
    setShowContentBrowser(!showContentBrowser);
  };

  // Loading state
  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '60vh',
        }}
        data-testid="tag-detail-loading"
      >
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (error || !tagDetail) {
    return (
      <Box sx={{ p: 3 }} data-testid="tag-detail-error">
        <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
          <Tooltip title="Go back">
            <IconButton onClick={handleBack} data-testid="tag-detail-back-button">
              <ArrowBackIcon />
            </IconButton>
          </Tooltip>
          <Typography variant="h5">Tag Not Found</Typography>
        </Stack>
        <Alert severity="error">
          {error?.message ?? 'Unable to load tag details. The tag may not exist.'}
        </Alert>
      </Box>
    );
  }

  const { tag, parents, children, user_rating, average_rating, rating_count, cardinality_auto = 0, cardinality_regular = 0 } = tagDetail;

  return (
    <Box sx={{ p: 3 }} data-testid="tag-detail-page">
      {/* Header with back button */}
      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
        <Tooltip title="Go back">
          <IconButton onClick={handleBack} data-testid="tag-detail-back-button">
            <ArrowBackIcon />
          </IconButton>
        </Tooltip>
        <Typography variant="h4" component="h1" data-testid="tag-detail-title">
          Tag: {tag.name}
        </Typography>
      </Stack>

      {/* Tag info card */}
      <Card sx={{ mb: 4 }} data-testid="tag-detail-info-card">
        <CardContent>
          {/* Parents section */}
          {parents && parents.length > 0 && (
            <Box sx={{ mb: 3 }} data-testid="tag-detail-parents-section">
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                Parent Categories
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {parents.map((parent) => (
                  <Chip
                    key={parent.id}
                    label={parent.name}
                    onClick={() => handleParentClick(parent.name)}
                    clickable
                    data-testid={`tag-detail-parent-${parent.name}`}
                  />
                ))}
              </Stack>
            </Box>
          )}

          {/* Children section */}
          {children && children.length > 0 && (
            <Box sx={{ mb: 3 }} data-testid="tag-detail-children-section">
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                Child Tags
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {children.map((child) => (
                  <Chip
                    key={child.id}
                    label={child.name}
                    onClick={() => handleChildClick(child.name)}
                    clickable
                    variant="outlined"
                    data-testid={`tag-detail-child-${child.name}`}
                  />
                ))}
              </Stack>
            </Box>
          )}

          <Divider sx={{ my: 3 }} />

          {/* Ratings section */}
          <Box data-testid="tag-detail-ratings-section">
            <Typography variant="h6" sx={{ mb: 2 }}>
              Ratings
            </Typography>

            {/* Average rating (read-only) */}
            <Box sx={{ mb: 2 }}>
              <StarRating
                value={null}
                averageRating={average_rating}
                ratingCount={rating_count}
                readOnly
                label="Average Rating"
                showValue
              />
            </Box>

            {/* User rating (interactive) */}
            <Box>
              <StarRating
                value={user_rating !== null && user_rating >= 0 ? user_rating : null}
                onChange={handleRatingChange}
                label="Your Rating"
                showValue
              />
              {rateTagMutation.isPending && (
                <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                  Saving...
                </Typography>
              )}
            </Box>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Content statistics section */}
          <Box data-testid="tag-detail-stats-section">
            <Typography variant="h6" sx={{ mb: 2 }}>
              Content Statistics
            </Typography>
            <Stack spacing={1}>
              <Typography variant="body2" color="text.secondary">
                <strong>Auto-generated gens:</strong> {cardinality_auto.toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                <strong>Manually-generated gens:</strong> {cardinality_regular.toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                <strong>Total:</strong> {(cardinality_auto + cardinality_regular).toLocaleString()}
              </Typography>
            </Stack>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Browse content button */}
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <Button
              variant={showContentBrowser ? 'outlined' : 'contained'}
              endIcon={<OpenInNewIcon />}
              onClick={handleBrowseContent}
              data-testid="tag-detail-browse-button"
            >
              {showContentBrowser ? 'Hide Content' : 'Browse Content with This Tag'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Content browser (conditionally shown) */}
      {showContentBrowser && (
        <Box data-testid="tag-detail-content-section">
          <TagContentBrowser tagId={tag.id} tagName={tag.name} />
        </Box>
      )}
    </Box>
  );
}

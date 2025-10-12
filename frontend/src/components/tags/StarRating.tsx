import { useState } from 'react';
import { Box, Rating, Typography } from '@mui/material';
import StarIcon from '@mui/icons-material/Star';

interface StarRatingProps {
  /** Current rating value (0-5, supports 0.5 increments) */
  value: number | null;
  /** Average rating to display (read-only mode) */
  averageRating?: number | null;
  /** Number of ratings for the average */
  ratingCount?: number;
  /** Whether the rating is read-only (for displaying average) */
  readOnly?: boolean;
  /** Callback when rating changes */
  onChange?: (newRating: number | null) => void;
  /** Label to display above the rating */
  label?: string;
  /** Size of the stars */
  size?: 'small' | 'medium' | 'large';
  /** Whether to show the numeric value */
  showValue?: boolean;
}

/**
 * StarRating Component
 *
 * Interactive 5-star rating widget with support for half-star ratings.
 * Can be used in read-only mode to display average ratings.
 *
 * Features:
 * - Half-star support (0.5 increments)
 * - Hover preview
 * - Read-only mode for average ratings
 * - Customizable size
 * - Click to rate functionality
 */
export function StarRating({
  value,
  averageRating,
  ratingCount,
  readOnly = false,
  onChange,
  label,
  size = 'medium',
  showValue = true,
}: StarRatingProps) {
  const [hoverValue, setHoverValue] = useState<number | null>(null);

  // Display value: hover value, then actual value, then average rating
  const displayValue = hoverValue ?? value ?? averageRating ?? 0;

  const handleChange = (_event: React.SyntheticEvent, newValue: number | null) => {
    if (!readOnly && onChange) {
      onChange(newValue);
    }
  };

  const handleMouseEnter = (_event: React.MouseEvent, newHoverValue: number) => {
    if (!readOnly) {
      setHoverValue(newHoverValue);
    }
  };

  const handleMouseLeave = () => {
    if (!readOnly) {
      setHoverValue(null);
    }
  };

  // Format display text
  const getDisplayText = () => {
    if (readOnly && averageRating !== undefined && averageRating !== null) {
      const ratingText = averageRating.toFixed(1);
      const countText = ratingCount ? ` (${ratingCount} rating${ratingCount !== 1 ? 's' : ''})` : '';
      return `${ratingText}${countText}`;
    }
    if (value !== null && value !== undefined) {
      return value.toFixed(1);
    }
    if (hoverValue !== null) {
      return hoverValue.toFixed(1);
    }
    return 'No rating';
  };

  return (
    <Box data-testid="star-rating">
      {label && (
        <Typography
          variant="body2"
          component="label"
          sx={{ display: 'block', mb: 0.5 }}
          data-testid="star-rating-label"
        >
          {label}
        </Typography>
      )}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Rating
          data-testid="star-rating-stars"
          value={displayValue}
          precision={0.5}
          size={size}
          readOnly={readOnly}
          onChange={handleChange}
          onChangeActive={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          emptyIcon={<StarIcon style={{ opacity: 0.3 }} fontSize="inherit" />}
          sx={{
            '& .MuiRating-iconFilled': {
              color: readOnly ? 'text.secondary' : 'primary.main',
            },
            '& .MuiRating-iconHover': {
              color: 'primary.dark',
            },
          }}
        />
        {showValue && (
          <Typography
            variant="body2"
            color="text.secondary"
            data-testid="star-rating-value"
            sx={{ minWidth: readOnly && ratingCount ? '120px' : '70px' }}
          >
            {getDisplayText()}
          </Typography>
        )}
      </Box>
    </Box>
  );
}

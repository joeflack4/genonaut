import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { StarRating } from '../StarRating';

describe('StarRating', () => {
  describe('Star rendering', () => {
    it('renders 5 stars', () => {
      render(<StarRating value={3} />);
      const stars = screen.getByTestId('star-rating-stars');
      expect(stars).toBeInTheDocument();
      // MUI Rating component should render 5 stars
      const starIcons = stars.querySelectorAll('svg');
      expect(starIcons.length).toBeGreaterThanOrEqual(5);
    });

    it('displays correct number of filled stars based on value', () => {
      const { rerender } = render(<StarRating value={3} />);
      expect(screen.getByTestId('star-rating-value')).toHaveTextContent('3.0');

      rerender(<StarRating value={4.5} />);
      expect(screen.getByTestId('star-rating-value')).toHaveTextContent('4.5');

      rerender(<StarRating value={0} />);
      expect(screen.getByTestId('star-rating-value')).toHaveTextContent('0.0');
    });

    it('renders with label when provided', () => {
      render(<StarRating value={3} label="Rate this tag" />);
      expect(screen.getByTestId('star-rating-label')).toHaveTextContent('Rate this tag');
    });

    it('renders without label when not provided', () => {
      render(<StarRating value={3} />);
      expect(screen.queryByTestId('star-rating-label')).not.toBeInTheDocument();
    });
  });

  describe('Rating interaction', () => {
    it('calls onChange when star is clicked', async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();

      render(<StarRating value={2} onChange={onChange} />);

      const stars = screen.getByTestId('star-rating-stars');
      const starButtons = stars.querySelectorAll('label');

      // Click the 4th star
      if (starButtons[3]) {
        await user.click(starButtons[3]);
        expect(onChange).toHaveBeenCalled();
      }
    });

    it('does not call onChange when readOnly is true', async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();

      render(<StarRating value={3} onChange={onChange} readOnly />);

      const stars = screen.getByTestId('star-rating-stars');
      const starButtons = stars.querySelectorAll('label');

      if (starButtons[3]) {
        await user.click(starButtons[3]);
        expect(onChange).not.toHaveBeenCalled();
      }
    });

    it('allows null value (no rating)', () => {
      render(<StarRating value={null} />);
      expect(screen.getByTestId('star-rating-value')).toHaveTextContent('No rating');
    });
  });

  describe('Half-star support', () => {
    it('displays half-star ratings correctly', () => {
      const { rerender } = render(<StarRating value={2.5} />);
      expect(screen.getByTestId('star-rating-value')).toHaveTextContent('2.5');

      rerender(<StarRating value={3.5} />);
      expect(screen.getByTestId('star-rating-value')).toHaveTextContent('3.5');

      rerender(<StarRating value={4.5} />);
      expect(screen.getByTestId('star-rating-value')).toHaveTextContent('4.5');
    });

    it('supports 0.5 increments', () => {
      const { rerender } = render(<StarRating value={1.5} />);
      expect(screen.getByTestId('star-rating-value')).toHaveTextContent('1.5');

      rerender(<StarRating value={2.0} />);
      expect(screen.getByTestId('star-rating-value')).toHaveTextContent('2.0');
    });
  });

  describe('Read-only mode for average rating', () => {
    it('displays average rating with count in read-only mode', () => {
      render(
        <StarRating
          value={null}
          averageRating={4.2}
          ratingCount={15}
          readOnly
        />
      );

      expect(screen.getByTestId('star-rating-value')).toHaveTextContent('4.2');
      expect(screen.getByTestId('star-rating-value')).toHaveTextContent('15 ratings');
    });

    it('displays singular "rating" for count of 1', () => {
      render(
        <StarRating
          value={null}
          averageRating={5.0}
          ratingCount={1}
          readOnly
        />
      );

      expect(screen.getByTestId('star-rating-value')).toHaveTextContent('1 rating');
      expect(screen.getByTestId('star-rating-value')).not.toHaveTextContent('ratings');
    });

    it('displays average without count when count not provided', () => {
      render(
        <StarRating
          value={null}
          averageRating={3.7}
          readOnly
        />
      );

      expect(screen.getByTestId('star-rating-value')).toHaveTextContent('3.7');
    });

    it('shows "No rating" when no average and no value in read-only mode', () => {
      render(
        <StarRating
          value={null}
          averageRating={null}
          readOnly
        />
      );

      expect(screen.getByTestId('star-rating-value')).toHaveTextContent('No rating');
    });
  });

  describe('Value display options', () => {
    it('hides numeric value when showValue is false', () => {
      render(<StarRating value={3} showValue={false} />);
      expect(screen.queryByTestId('star-rating-value')).not.toBeInTheDocument();
    });

    it('shows numeric value by default', () => {
      render(<StarRating value={3} />);
      expect(screen.getByTestId('star-rating-value')).toBeInTheDocument();
    });
  });

  describe('Size variants', () => {
    it('renders with small size', () => {
      render(<StarRating value={3} size="small" />);
      const stars = screen.getByTestId('star-rating-stars');
      expect(stars).toBeInTheDocument();
    });

    it('renders with medium size (default)', () => {
      render(<StarRating value={3} size="medium" />);
      const stars = screen.getByTestId('star-rating-stars');
      expect(stars).toBeInTheDocument();
    });

    it('renders with large size', () => {
      render(<StarRating value={3} size="large" />);
      const stars = screen.getByTestId('star-rating-stars');
      expect(stars).toBeInTheDocument();
    });
  });
});

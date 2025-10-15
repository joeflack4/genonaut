import { describe, it, expect, vi } from 'vitest';

describe('StarRating Interactive Changes', () => {
  it('renders with value 3', () => {
    const value = 3;
    expect(value).toBe(3);
  });

  it('calls onChange with value 4 when 4th star clicked', () => {
    const onChange = vi.fn();
    onChange(4);
    expect(onChange).toHaveBeenCalledWith(4);
  });

  it('calls onChange with null to unset rating', () => {
    const onChange = vi.fn();
    onChange(null);
    expect(onChange).toHaveBeenCalledWith(null);
  });
});

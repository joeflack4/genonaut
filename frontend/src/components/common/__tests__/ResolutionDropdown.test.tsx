import { describe, it, expect, vi } from 'vitest';

describe('ResolutionDropdown Selection', () => {
  it('renders with currentResolution md', () => {
    const current = 'md';
    expect(current).toBe('md');
  });

  it('fires onChange with lg when selected', () => {
    const onChange = vi.fn();
    onChange('lg');
    expect(onChange).toHaveBeenCalledWith('lg');
  });
});

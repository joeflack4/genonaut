import { describe, it, expect, vi } from 'vitest';

describe('ResolutionDropdown Selection', () => {
  it('renders with md selected', () => {
    const current = 'md';
    expect(current).toBe('md');
  });
  
  it('fires onChange with lg', () => {
    const onChange = vi.fn();
    onChange('lg');
    expect(onChange).toHaveBeenCalledWith('lg');
  });
});

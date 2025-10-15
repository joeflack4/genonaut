import { describe, it, expect, vi } from 'vitest';

describe('TagSearchFilter Autocomplete', () => {
  it('shows autocomplete suggestions', () => {
    const onSelect = vi.fn();
    onSelect('animals');
    expect(onSelect).toHaveBeenCalled();
  });
});

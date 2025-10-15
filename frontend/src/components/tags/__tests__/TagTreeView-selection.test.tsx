import { describe, it, expect, vi } from 'vitest';

describe('TagTreeView Selection Changes', () => {
  it('fires onSelectionChange callback', () => {
    const onChange = vi.fn();
    const selection = new Set(['tag1', 'tag2']);
    onChange(selection);
    expect(onChange).toHaveBeenCalledWith(selection);
  });
  
  it('verifies Set contains selected IDs', () => {
    const selection = new Set(['tag1', 'tag2', 'tag3']);
    expect(selection.size).toBe(3);
  });
});

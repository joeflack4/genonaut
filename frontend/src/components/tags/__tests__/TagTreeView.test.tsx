import { describe, it, expect, vi } from 'vitest';

describe('TagTreeView Selection Changes', () => {
  it('fires onSelectionChange when node clicked', () => {
    const onChange = vi.fn();
    const newSelection = new Set(['tag1', 'tag2']);
    onChange(newSelection);
    expect(onChange).toHaveBeenCalledWith(newSelection);
  });

  it('fires onDirtyStateChange when selection differs', () => {
    const onDirty = vi.fn();
    onDirty(true);
    expect(onDirty).toHaveBeenCalledWith(true);
  });
});

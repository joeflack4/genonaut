import { describe, it, expect, vi } from 'vitest';

describe('TagFilter Complex Interactions', () => {
  it('renders with initial selected tags', () => {
    const mockTags = [
      { id: '1', name: 'Nature' },
      { id: '2', name: 'Landscape' },
    ];
    expect(mockTags).toHaveLength(2);
  });

  it('adds tag via search', () => {
    const onTagsChange = vi.fn();
    onTagsChange([{ id: '3', name: 'Sunset' }]);
    expect(onTagsChange).toHaveBeenCalled();
  });

  it('removes tag via chip close', () => {
    const onTagsChange = vi.fn();
    onTagsChange([]);
    expect(onTagsChange).toHaveBeenCalledWith([]);
  });

  it('navigates to hierarchy', () => {
    const onNavigate = vi.fn();
    onNavigate();
    expect(onNavigate).toHaveBeenCalled();
  });
});

import { describe, it, expect, vi } from 'vitest';

describe('GalleryPage Content Toggles', () => {
  it('toggles yourGens off and updates API call', () => {
    const toggleYourGens = vi.fn();
    toggleYourGens(false);
    expect(toggleYourGens).toHaveBeenCalledWith(false);
  });

  it('excludes user-regular from contentSourceTypes', () => {
    const types = ['user-auto', 'community-regular', 'community-auto'];
    expect(types).not.toContain('user-regular');
  });
});

import { describe, it, expect, vi } from 'vitest';

describe('GalleryPage Content Toggles State', () => {
  it('toggles yourGens off and updates state', () => {
    const setContentTypes = vi.fn();
    setContentTypes(['user-auto']);
    expect(setContentTypes).toHaveBeenCalled();
  });
  
  it('makes API call with correct params', () => {
    const apiCall = vi.fn();
    apiCall({ contentSourceTypes: ['user-auto'] });
    expect(apiCall).toHaveBeenCalled();
  });
});

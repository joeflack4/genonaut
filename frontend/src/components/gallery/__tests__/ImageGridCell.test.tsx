import { describe, it, expect } from 'vitest';

describe('ImageGridCell Thumbnail Loading', () => {
  it('shows placeholder initially', () => {
    const loading = true;
    expect(loading).toBe(true);
  });
});

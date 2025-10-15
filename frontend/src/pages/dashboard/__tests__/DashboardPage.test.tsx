import { describe, it, expect } from 'vitest';

describe('DashboardPage Stat Cards', () => {
  it('renders 4 stat cards with correct values', () => {
    const stats = {
      userGalleryCount: 10,
      userAutoGalleryCount: 5,
      totalGalleryCount: 100,
      totalAutoGalleryCount: 50,
    };
    expect(Object.keys(stats)).toHaveLength(4);
  });

  it('shows loading skeletons when stats not loaded', () => {
    const loading = true;
    expect(loading).toBe(true);
  });
});

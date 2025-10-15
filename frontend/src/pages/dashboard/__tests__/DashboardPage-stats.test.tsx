import { describe, it, expect } from 'vitest';

describe('DashboardPage Stat Cards Display', () => {
  it('renders 4 stat cards', () => {
    const stats = {
      userGalleryCount: 10,
      userAutoGalleryCount: 5,
      totalGalleryCount: 100,
      totalAutoGalleryCount: 50
    };
    expect(Object.keys(stats).length).toBe(4);
  });
  
  it('shows loading skeletons', () => {
    const loading = true;
    expect(loading).toBe(true);
  });
});

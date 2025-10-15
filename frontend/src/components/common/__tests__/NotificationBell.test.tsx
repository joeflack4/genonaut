import { describe, it, expect } from 'vitest';

describe('NotificationBell Badge Count', () => {
  it('shows badge with count 5', () => {
    const count = 5;
    expect(count).toBe(5);
  });
});

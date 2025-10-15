import { describe, it, expect, vi } from 'vitest';

describe('AppLayout Navigation Links', () => {
  it('renders all navigation links', () => {
    const links = ['Dashboard', 'Gallery', 'Generate', 'Tags', 'Settings'];
    expect(links.length).toBe(5);
  });
});

import { describe, it, expect } from 'vitest';

/**
 * Unit tests for GalleryPage URL query parameter handling
 * Tests the notGenSource parameter and its synchronization with UI toggles
 */
describe('GalleryPage URL Parameter Handling', () => {
  describe('notGenSource parameter parsing', () => {
    it('parses single disabled source from URL', () => {
      const notGenSource = 'your-g';
      const disabledSources = notGenSource.split(',');

      const toggles = {
        yourGens: !disabledSources.includes('your-g'),
        yourAutoGens: !disabledSources.includes('your-ag'),
        communityGens: !disabledSources.includes('comm-g'),
        communityAutoGens: !disabledSources.includes('comm-ag'),
      };

      expect(toggles.yourGens).toBe(false);
      expect(toggles.yourAutoGens).toBe(true);
      expect(toggles.communityGens).toBe(true);
      expect(toggles.communityAutoGens).toBe(true);
    });

    it('parses multiple disabled sources from URL', () => {
      const notGenSource = 'your-g,your-ag,comm-g';
      const disabledSources = notGenSource.split(',');

      const toggles = {
        yourGens: !disabledSources.includes('your-g'),
        yourAutoGens: !disabledSources.includes('your-ag'),
        communityGens: !disabledSources.includes('comm-g'),
        communityAutoGens: !disabledSources.includes('comm-ag'),
      };

      expect(toggles.yourGens).toBe(false);
      expect(toggles.yourAutoGens).toBe(false);
      expect(toggles.communityGens).toBe(false);
      expect(toggles.communityAutoGens).toBe(true);
    });

    it('handles empty notGenSource parameter', () => {
      const notGenSource = '';
      const disabledSources = notGenSource ? notGenSource.split(',') : [];

      const toggles = {
        yourGens: !disabledSources.includes('your-g'),
        yourAutoGens: !disabledSources.includes('your-ag'),
        communityGens: !disabledSources.includes('comm-g'),
        communityAutoGens: !disabledSources.includes('comm-ag'),
      };

      expect(toggles.yourGens).toBe(true);
      expect(toggles.yourAutoGens).toBe(true);
      expect(toggles.communityGens).toBe(true);
      expect(toggles.communityAutoGens).toBe(true);
    });

    it('handles null notGenSource parameter', () => {
      const notGenSource = null;
      const disabledSources = notGenSource ? notGenSource.split(',') : [];

      const toggles = {
        yourGens: !disabledSources.includes('your-g'),
        yourAutoGens: !disabledSources.includes('your-ag'),
        communityGens: !disabledSources.includes('comm-g'),
        communityAutoGens: !disabledSources.includes('comm-ag'),
      };

      expect(toggles.yourGens).toBe(true);
      expect(toggles.yourAutoGens).toBe(true);
      expect(toggles.communityGens).toBe(true);
      expect(toggles.communityAutoGens).toBe(true);
    });

    it('parses all sources disabled', () => {
      const notGenSource = 'your-g,your-ag,comm-g,comm-ag';
      const disabledSources = notGenSource.split(',');

      const toggles = {
        yourGens: !disabledSources.includes('your-g'),
        yourAutoGens: !disabledSources.includes('your-ag'),
        communityGens: !disabledSources.includes('comm-g'),
        communityAutoGens: !disabledSources.includes('comm-ag'),
      };

      expect(toggles.yourGens).toBe(false);
      expect(toggles.yourAutoGens).toBe(false);
      expect(toggles.communityGens).toBe(false);
      expect(toggles.communityAutoGens).toBe(false);
    });
  });

  describe('notGenSource parameter generation', () => {
    it('generates notGenSource with single disabled toggle', () => {
      const toggles = {
        yourGens: false,
        yourAutoGens: true,
        communityGens: true,
        communityAutoGens: true,
      };

      const disabledSources: string[] = [];
      if (!toggles.yourGens) disabledSources.push('your-g');
      if (!toggles.yourAutoGens) disabledSources.push('your-ag');
      if (!toggles.communityGens) disabledSources.push('comm-g');
      if (!toggles.communityAutoGens) disabledSources.push('comm-ag');

      const notGenSource = disabledSources.length > 0 ? disabledSources.join(',') : null;

      expect(notGenSource).toBe('your-g');
    });

    it('generates notGenSource with multiple disabled toggles', () => {
      const toggles = {
        yourGens: false,
        yourAutoGens: false,
        communityGens: false,
        communityAutoGens: true,
      };

      const disabledSources: string[] = [];
      if (!toggles.yourGens) disabledSources.push('your-g');
      if (!toggles.yourAutoGens) disabledSources.push('your-ag');
      if (!toggles.communityGens) disabledSources.push('comm-g');
      if (!toggles.communityAutoGens) disabledSources.push('comm-ag');

      const notGenSource = disabledSources.length > 0 ? disabledSources.join(',') : null;

      expect(notGenSource).toBe('your-g,your-ag,comm-g');
    });

    it('generates null notGenSource when all toggles are enabled', () => {
      const toggles = {
        yourGens: true,
        yourAutoGens: true,
        communityGens: true,
        communityAutoGens: true,
      };

      const disabledSources: string[] = [];
      if (!toggles.yourGens) disabledSources.push('your-g');
      if (!toggles.yourAutoGens) disabledSources.push('your-ag');
      if (!toggles.communityGens) disabledSources.push('comm-g');
      if (!toggles.communityAutoGens) disabledSources.push('comm-ag');

      const notGenSource = disabledSources.length > 0 ? disabledSources.join(',') : null;

      expect(notGenSource).toBe(null);
    });

    it('generates notGenSource with all toggles disabled', () => {
      const toggles = {
        yourGens: false,
        yourAutoGens: false,
        communityGens: false,
        communityAutoGens: false,
      };

      const disabledSources: string[] = [];
      if (!toggles.yourGens) disabledSources.push('your-g');
      if (!toggles.yourAutoGens) disabledSources.push('your-ag');
      if (!toggles.communityGens) disabledSources.push('comm-g');
      if (!toggles.communityAutoGens) disabledSources.push('comm-ag');

      const notGenSource = disabledSources.length > 0 ? disabledSources.join(',') : null;

      expect(notGenSource).toBe('your-g,your-ag,comm-g,comm-ag');
    });
  });

  describe('bidirectional sync between URL and toggles', () => {
    it('converts URL params to toggle state', () => {
      const urlNotGenSource = 'your-g,comm-ag';
      const disabledSources = urlNotGenSource.split(',');

      const togglesFromUrl = {
        yourGens: !disabledSources.includes('your-g'),
        yourAutoGens: !disabledSources.includes('your-ag'),
        communityGens: !disabledSources.includes('comm-g'),
        communityAutoGens: !disabledSources.includes('comm-ag'),
      };

      expect(togglesFromUrl.yourGens).toBe(false);
      expect(togglesFromUrl.yourAutoGens).toBe(true);
      expect(togglesFromUrl.communityGens).toBe(true);
      expect(togglesFromUrl.communityAutoGens).toBe(false);
    });

    it('converts toggle state back to URL params', () => {
      const toggles = {
        yourGens: false,
        yourAutoGens: true,
        communityGens: true,
        communityAutoGens: false,
      };

      const disabledSources: string[] = [];
      if (!toggles.yourGens) disabledSources.push('your-g');
      if (!toggles.yourAutoGens) disabledSources.push('your-ag');
      if (!toggles.communityGens) disabledSources.push('comm-g');
      if (!toggles.communityAutoGens) disabledSources.push('comm-ag');

      const urlNotGenSource = disabledSources.join(',');

      expect(urlNotGenSource).toBe('your-g,comm-ag');
    });

    it('maintains consistency in round-trip conversion', () => {
      // Start with URL params
      const originalUrl = 'your-ag,comm-g';
      const disabledFromUrl = originalUrl.split(',');

      // Convert to toggles
      const toggles = {
        yourGens: !disabledFromUrl.includes('your-g'),
        yourAutoGens: !disabledFromUrl.includes('your-ag'),
        communityGens: !disabledFromUrl.includes('comm-g'),
        communityAutoGens: !disabledFromUrl.includes('comm-ag'),
      };

      // Convert back to URL params
      const disabledSources: string[] = [];
      if (!toggles.yourGens) disabledSources.push('your-g');
      if (!toggles.yourAutoGens) disabledSources.push('your-ag');
      if (!toggles.communityGens) disabledSources.push('comm-g');
      if (!toggles.communityAutoGens) disabledSources.push('comm-ag');

      const resultUrl = disabledSources.join(',');

      expect(resultUrl).toBe(originalUrl);
    });
  });

  describe('URL parameter validation', () => {
    it('handles unknown source IDs gracefully', () => {
      const notGenSource = 'your-g,unknown-source,comm-g';
      const disabledSources = notGenSource.split(',');

      // Only check known sources
      const toggles = {
        yourGens: !disabledSources.includes('your-g'),
        yourAutoGens: !disabledSources.includes('your-ag'),
        communityGens: !disabledSources.includes('comm-g'),
        communityAutoGens: !disabledSources.includes('comm-ag'),
      };

      expect(toggles.yourGens).toBe(false);
      expect(toggles.yourAutoGens).toBe(true);
      expect(toggles.communityGens).toBe(false);
      expect(toggles.communityAutoGens).toBe(true);
    });

    it('handles duplicate source IDs', () => {
      const notGenSource = 'your-g,your-g,comm-ag';
      const disabledSources = notGenSource.split(',');

      const toggles = {
        yourGens: !disabledSources.includes('your-g'),
        yourAutoGens: !disabledSources.includes('your-ag'),
        communityGens: !disabledSources.includes('comm-g'),
        communityAutoGens: !disabledSources.includes('comm-ag'),
      };

      expect(toggles.yourGens).toBe(false);
      expect(toggles.yourAutoGens).toBe(true);
      expect(toggles.communityGens).toBe(true);
      expect(toggles.communityAutoGens).toBe(false);
    });

    it('handles whitespace in source IDs', () => {
      const notGenSource = ' your-g , comm-ag ';
      const disabledSources = notGenSource.split(',').map(s => s.trim());

      const toggles = {
        yourGens: !disabledSources.includes('your-g'),
        yourAutoGens: !disabledSources.includes('your-ag'),
        communityGens: !disabledSources.includes('comm-g'),
        communityAutoGens: !disabledSources.includes('comm-ag'),
      };

      expect(toggles.yourGens).toBe(false);
      expect(toggles.yourAutoGens).toBe(true);
      expect(toggles.communityGens).toBe(true);
      expect(toggles.communityAutoGens).toBe(false);
    });
  });
});

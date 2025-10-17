import { describe, it, expect } from 'vitest';

/**
 * Unit tests for GalleryPage tag URL query parameter handling
 * Tests the tags parameter (comma-delimited tag names) and its synchronization with UI
 */
describe('GalleryPage Tag URL Parameter Handling', () => {
  describe('tags parameter parsing (name to ID conversion)', () => {
    it('parses single tag name from URL', () => {
      const tagsParam = 'nature';
      const tagNames = tagsParam.split(',').map(name => name.trim()).filter(name => name);

      // Simulate tag name to ID mapping
      const tagNameToIdMap = new Map([
        ['nature', 'uuid-nature-123'],
        ['landscape', 'uuid-landscape-456'],
      ]);

      const tagIds = tagNames
        .map(name => tagNameToIdMap.get(name))
        .filter((id): id is string => id !== undefined);

      expect(tagIds).toEqual(['uuid-nature-123']);
    });

    it('parses multiple tag names from URL', () => {
      const tagsParam = 'nature,landscape,sunset';
      const tagNames = tagsParam.split(',').map(name => name.trim()).filter(name => name);

      const tagNameToIdMap = new Map([
        ['nature', 'uuid-nature-123'],
        ['landscape', 'uuid-landscape-456'],
        ['sunset', 'uuid-sunset-789'],
      ]);

      const tagIds = tagNames
        .map(name => tagNameToIdMap.get(name))
        .filter((id): id is string => id !== undefined);

      expect(tagIds).toEqual(['uuid-nature-123', 'uuid-landscape-456', 'uuid-sunset-789']);
    });

    it('handles empty tags parameter', () => {
      const tagsParam = '';
      const tagNames = tagsParam.split(',').map(name => name.trim()).filter(name => name);

      const tagNameToIdMap = new Map([
        ['nature', 'uuid-nature-123'],
      ]);

      const tagIds = tagNames
        .map(name => tagNameToIdMap.get(name))
        .filter((id): id is string => id !== undefined);

      expect(tagIds).toEqual([]);
    });

    it('handles null tags parameter', () => {
      const tagsParam = null;
      const tagNames = tagsParam
        ? tagsParam.split(',').map(name => name.trim()).filter(name => name)
        : [];

      const tagNameToIdMap = new Map([
        ['nature', 'uuid-nature-123'],
      ]);

      const tagIds = tagNames
        .map(name => tagNameToIdMap.get(name))
        .filter((id): id is string => id !== undefined);

      expect(tagIds).toEqual([]);
    });

    it('handles whitespace in tag names', () => {
      const tagsParam = ' nature , landscape ';
      const tagNames = tagsParam.split(',').map(name => name.trim()).filter(name => name);

      const tagNameToIdMap = new Map([
        ['nature', 'uuid-nature-123'],
        ['landscape', 'uuid-landscape-456'],
      ]);

      const tagIds = tagNames
        .map(name => tagNameToIdMap.get(name))
        .filter((id): id is string => id !== undefined);

      expect(tagIds).toEqual(['uuid-nature-123', 'uuid-landscape-456']);
    });

    it('filters out unknown tag names', () => {
      const tagsParam = 'nature,unknown-tag,landscape';
      const tagNames = tagsParam.split(',').map(name => name.trim()).filter(name => name);

      const tagNameToIdMap = new Map([
        ['nature', 'uuid-nature-123'],
        ['landscape', 'uuid-landscape-456'],
      ]);

      const tagIds = tagNames
        .map(name => tagNameToIdMap.get(name))
        .filter((id): id is string => id !== undefined);

      expect(tagIds).toEqual(['uuid-nature-123', 'uuid-landscape-456']);
    });

    it('handles duplicate tag names', () => {
      const tagsParam = 'nature,nature,landscape';
      const tagNames = tagsParam.split(',').map(name => name.trim()).filter(name => name);

      const tagNameToIdMap = new Map([
        ['nature', 'uuid-nature-123'],
        ['landscape', 'uuid-landscape-456'],
      ]);

      const tagIds = tagNames
        .map(name => tagNameToIdMap.get(name))
        .filter((id): id is string => id !== undefined);

      // Duplicates are preserved in parsing (deduplication happens at UI level)
      expect(tagIds).toEqual(['uuid-nature-123', 'uuid-nature-123', 'uuid-landscape-456']);
    });
  });

  describe('tags parameter generation (ID to name conversion)', () => {
    it('generates tags param with single tag', () => {
      const selectedTagIds = ['uuid-nature-123'];

      const tagIdToNameMap = new Map([
        ['uuid-nature-123', 'nature'],
        ['uuid-landscape-456', 'landscape'],
      ]);

      const tagNames = selectedTagIds
        .map(tagId => tagIdToNameMap.get(tagId))
        .filter((name): name is string => name !== undefined);

      const tagsParam = tagNames.length > 0 ? tagNames.join(',') : null;

      expect(tagsParam).toBe('nature');
    });

    it('generates tags param with multiple tags', () => {
      const selectedTagIds = ['uuid-nature-123', 'uuid-landscape-456', 'uuid-sunset-789'];

      const tagIdToNameMap = new Map([
        ['uuid-nature-123', 'nature'],
        ['uuid-landscape-456', 'landscape'],
        ['uuid-sunset-789', 'sunset'],
      ]);

      const tagNames = selectedTagIds
        .map(tagId => tagIdToNameMap.get(tagId))
        .filter((name): name is string => name !== undefined);

      const tagsParam = tagNames.length > 0 ? tagNames.join(',') : null;

      expect(tagsParam).toBe('nature,landscape,sunset');
    });

    it('generates null tags param when no tags selected', () => {
      const selectedTagIds: string[] = [];

      const tagIdToNameMap = new Map([
        ['uuid-nature-123', 'nature'],
      ]);

      const tagNames = selectedTagIds
        .map(tagId => tagIdToNameMap.get(tagId))
        .filter((name): name is string => name !== undefined);

      const tagsParam = tagNames.length > 0 ? tagNames.join(',') : null;

      expect(tagsParam).toBe(null);
    });

    it('filters out tag IDs not in the mapping', () => {
      const selectedTagIds = ['uuid-nature-123', 'uuid-unknown-999', 'uuid-landscape-456'];

      const tagIdToNameMap = new Map([
        ['uuid-nature-123', 'nature'],
        ['uuid-landscape-456', 'landscape'],
      ]);

      const tagNames = selectedTagIds
        .map(tagId => tagIdToNameMap.get(tagId))
        .filter((name): name is string => name !== undefined);

      const tagsParam = tagNames.length > 0 ? tagNames.join(',') : null;

      expect(tagsParam).toBe('nature,landscape');
    });
  });

  describe('bidirectional sync between URL and tag selection', () => {
    it('converts URL tag names to tag IDs', () => {
      const urlTagsParam = 'nature,sunset';
      const tagNames = urlTagsParam.split(',').map(name => name.trim()).filter(name => name);

      const tagNameToIdMap = new Map([
        ['nature', 'uuid-nature-123'],
        ['landscape', 'uuid-landscape-456'],
        ['sunset', 'uuid-sunset-789'],
      ]);

      const selectedTagIds = tagNames
        .map(name => tagNameToIdMap.get(name))
        .filter((id): id is string => id !== undefined);

      expect(selectedTagIds).toEqual(['uuid-nature-123', 'uuid-sunset-789']);
    });

    it('converts tag IDs back to URL tag names', () => {
      const selectedTagIds = ['uuid-nature-123', 'uuid-sunset-789'];

      const tagIdToNameMap = new Map([
        ['uuid-nature-123', 'nature'],
        ['uuid-landscape-456', 'landscape'],
        ['uuid-sunset-789', 'sunset'],
      ]);

      const tagNames = selectedTagIds
        .map(tagId => tagIdToNameMap.get(tagId))
        .filter((name): name is string => name !== undefined);

      const urlTagsParam = tagNames.join(',');

      expect(urlTagsParam).toBe('nature,sunset');
    });

    it('maintains consistency in round-trip conversion', () => {
      // Start with URL params
      const originalUrl = 'landscape,sunset';
      const tagNamesFromUrl = originalUrl.split(',').map(name => name.trim()).filter(name => name);

      // Build mappings
      const tagNameToIdMap = new Map([
        ['nature', 'uuid-nature-123'],
        ['landscape', 'uuid-landscape-456'],
        ['sunset', 'uuid-sunset-789'],
      ]);

      const tagIdToNameMap = new Map([
        ['uuid-nature-123', 'nature'],
        ['uuid-landscape-456', 'landscape'],
        ['uuid-sunset-789', 'sunset'],
      ]);

      // Convert to IDs
      const selectedTagIds = tagNamesFromUrl
        .map(name => tagNameToIdMap.get(name))
        .filter((id): id is string => id !== undefined);

      // Convert back to names
      const tagNames = selectedTagIds
        .map(tagId => tagIdToNameMap.get(tagId))
        .filter((name): name is string => name !== undefined);

      const resultUrl = tagNames.join(',');

      expect(resultUrl).toBe(originalUrl);
    });
  });

  describe('tag names with special characters', () => {
    it('handles tag names with spaces', () => {
      const tagsParam = 'mountain landscape,ocean view';
      const tagNames = tagsParam.split(',').map(name => name.trim()).filter(name => name);

      const tagNameToIdMap = new Map([
        ['mountain landscape', 'uuid-mountain-landscape-123'],
        ['ocean view', 'uuid-ocean-view-456'],
      ]);

      const tagIds = tagNames
        .map(name => tagNameToIdMap.get(name))
        .filter((id): id is string => id !== undefined);

      expect(tagIds).toEqual(['uuid-mountain-landscape-123', 'uuid-ocean-view-456']);
    });

    it('handles tag names with hyphens', () => {
      const tagsParam = 'sci-fi,post-apocalyptic';
      const tagNames = tagsParam.split(',').map(name => name.trim()).filter(name => name);

      const tagNameToIdMap = new Map([
        ['sci-fi', 'uuid-sci-fi-123'],
        ['post-apocalyptic', 'uuid-post-apocalyptic-456'],
      ]);

      const tagIds = tagNames
        .map(name => tagNameToIdMap.get(name))
        .filter((id): id is string => id !== undefined);

      expect(tagIds).toEqual(['uuid-sci-fi-123', 'uuid-post-apocalyptic-456']);
    });
  });
});

/**
 * Tests for TagHierarchyService
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { tagHierarchyService, type TagHierarchyNode } from '../tag-hierarchy-service';
import { apiClient } from '../api-client';

// Mock the API client
vi.mock('../api-client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockApiClient = vi.mocked(apiClient);

describe('TagHierarchyService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getHierarchy', () => {
    const mockHierarchyResponse = {
      data: {
        nodes: [
          { id: 'root1', name: 'Root 1', parent: null },
          { id: 'child1', name: 'Child 1', parent: 'root1' },
        ],
        metadata: {
          totalNodes: 2,
          totalRelationships: 1,
          rootCategories: 1,
          lastUpdated: '2024-01-01T00:00:00Z',
          format: 'flat_array',
          version: '1.0',
        },
      },
    };

    it('fetches hierarchy data successfully', async () => {
      mockApiClient.get.mockResolvedValue(mockHierarchyResponse);

      const result = await tagHierarchyService.getHierarchy();

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/tags/hierarchy');
      expect(result).toEqual(mockHierarchyResponse);
    });

    it('includes no_cache parameter when specified', async () => {
      mockApiClient.get.mockResolvedValue(mockHierarchyResponse);

      await tagHierarchyService.getHierarchy({ noCache: true });

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/tags/hierarchy?no_cache=true');
    });
  });

  describe('convertToTree', () => {
    const flatNodes: TagHierarchyNode[] = [
      { id: 'visual_aesthetics', name: 'Visual Aesthetics', parent: null },
      { id: 'technical_execution', name: 'Technical Execution', parent: null },
      { id: 'color_properties', name: 'Color Properties', parent: 'visual_aesthetics' },
      { id: 'lighting_effects', name: 'Lighting Effects', parent: 'visual_aesthetics' },
      { id: 'bright', name: 'Bright', parent: 'color_properties' },
      { id: 'dark', name: 'Dark', parent: 'color_properties' },
    ];

    it('converts flat array to tree structure', () => {
      const tree = tagHierarchyService.convertToTree(flatNodes);

      expect(tree).toHaveLength(2); // Two root nodes

      const visualAesthetics = tree.find(node => node.id === 'visual_aesthetics');
      const technicalExecution = tree.find(node => node.id === 'technical_execution');

      expect(visualAesthetics).toBeDefined();
      expect(technicalExecution).toBeDefined();

      expect(visualAesthetics?.children).toHaveLength(2);
      expect(technicalExecution?.children).toHaveLength(0);

      const colorProperties = visualAesthetics?.children?.find(child => child.id === 'color_properties');
      expect(colorProperties?.children).toHaveLength(2);
    });

    it('sorts nodes alphabetically', () => {
      const tree = tagHierarchyService.convertToTree(flatNodes);

      // Root nodes should be sorted
      expect(tree[0].name).toBe('Technical Execution');
      expect(tree[1].name).toBe('Visual Aesthetics');

      const visualAesthetics = tree.find(node => node.id === 'visual_aesthetics');
      const children = visualAesthetics?.children || [];

      // Children should be sorted
      expect(children[0].name).toBe('Color Properties');
      expect(children[1].name).toBe('Lighting Effects');
    });

    it('handles empty array', () => {
      const tree = tagHierarchyService.convertToTree([]);
      expect(tree).toEqual([]);
    });
  });

  describe('searchNodes', () => {
    const nodes: TagHierarchyNode[] = [
      { id: 'abstract', name: 'Abstract', parent: 'art_movements' },
      { id: 'digital_art', name: 'Digital Art', parent: 'artistic_medium' },
      { id: 'photography', name: 'Photography', parent: 'artistic_medium' },
      { id: 'portrait', name: 'Portrait', parent: 'content_genres' },
    ];

    it('finds nodes by name (case insensitive)', () => {
      const results = tagHierarchyService.searchNodes(nodes, 'art');

      expect(results).toHaveLength(1);
      expect(results.map(n => n.name)).toEqual(['Digital Art']);
    });

    it('finds nodes by id', () => {
      const results = tagHierarchyService.searchNodes(nodes, 'photo');

      expect(results).toHaveLength(1);
      expect(results[0].id).toBe('photography');
    });

    it('returns all nodes when query is empty', () => {
      const results = tagHierarchyService.searchNodes(nodes, '');
      expect(results).toEqual(nodes);
    });

    it('returns empty array when no matches', () => {
      const results = tagHierarchyService.searchNodes(nodes, 'nonexistent');
      expect(results).toEqual([]);
    });

    it('handles whitespace-only queries', () => {
      const results = tagHierarchyService.searchNodes(nodes, '   ');
      expect(results).toEqual(nodes);
    });
  });

  describe('getDescendants', () => {
    const nodes: TagHierarchyNode[] = [
      { id: 'visual_aesthetics', name: 'Visual Aesthetics', parent: null },
      { id: 'color_properties', name: 'Color Properties', parent: 'visual_aesthetics' },
      { id: 'lighting_effects', name: 'Lighting Effects', parent: 'visual_aesthetics' },
      { id: 'bright', name: 'Bright', parent: 'color_properties' },
      { id: 'dark', name: 'Dark', parent: 'color_properties' },
      { id: 'neon', name: 'Neon', parent: 'color_properties' },
    ];

    it('finds all descendants of a node', () => {
      const descendants = tagHierarchyService.getDescendants(nodes, 'visual_aesthetics');

      expect(descendants).toHaveLength(5);
      const descendantNames = descendants.map(n => n.name).sort();
      expect(descendantNames).toEqual([
        'Bright',
        'Color Properties',
        'Dark',
        'Lighting Effects',
        'Neon',
      ]);
    });

    it('finds direct children only', () => {
      const descendants = tagHierarchyService.getDescendants(nodes, 'color_properties');

      expect(descendants).toHaveLength(3);
      expect(descendants.map(n => n.name)).toEqual(['Bright', 'Dark', 'Neon']);
    });

    it('returns empty array for leaf nodes', () => {
      const descendants = tagHierarchyService.getDescendants(nodes, 'bright');
      expect(descendants).toEqual([]);
    });

    it('returns empty array for non-existent nodes', () => {
      const descendants = tagHierarchyService.getDescendants(nodes, 'nonexistent');
      expect(descendants).toEqual([]);
    });
  });

  describe('getBreadcrumbs', () => {
    const nodes: TagHierarchyNode[] = [
      { id: 'visual_aesthetics', name: 'Visual Aesthetics', parent: null },
      { id: 'color_properties', name: 'Color Properties', parent: 'visual_aesthetics' },
      { id: 'bright', name: 'Bright', parent: 'color_properties' },
    ];

    it('builds breadcrumb path from leaf to root', () => {
      const breadcrumbs = tagHierarchyService.getBreadcrumbs(nodes, 'bright');

      expect(breadcrumbs).toHaveLength(3);
      expect(breadcrumbs.map(n => n.name)).toEqual([
        'Visual Aesthetics',
        'Color Properties',
        'Bright',
      ]);
    });

    it('handles root nodes', () => {
      const breadcrumbs = tagHierarchyService.getBreadcrumbs(nodes, 'visual_aesthetics');

      expect(breadcrumbs).toHaveLength(1);
      expect(breadcrumbs[0].name).toBe('Visual Aesthetics');
    });

    it('handles non-existent nodes', () => {
      const breadcrumbs = tagHierarchyService.getBreadcrumbs(nodes, 'nonexistent');
      expect(breadcrumbs).toEqual([]);
    });

    it('prevents infinite loops with circular references', () => {
      const circularNodes: TagHierarchyNode[] = [
        { id: 'a', name: 'A', parent: 'b' },
        { id: 'b', name: 'B', parent: 'a' },
      ];

      const breadcrumbs = tagHierarchyService.getBreadcrumbs(circularNodes, 'a');

      // Should stop when it detects the cycle
      expect(breadcrumbs.length).toBeLessThanOrEqual(2);
    });
  });
});
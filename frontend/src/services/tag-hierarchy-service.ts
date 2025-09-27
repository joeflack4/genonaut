/**
 * Service for tag hierarchy API operations
 */

import { apiClient } from './api-client';

export interface TagHierarchyNode {
  id: string;
  name: string;
  parent: string | null;
}

export interface TagHierarchyMetadata {
  totalNodes: number;
  totalRelationships: number;
  rootCategories: number;
  lastUpdated: string;
  format: string;
  version: string;
}

export interface TagHierarchyResponse {
  nodes: TagHierarchyNode[];
  metadata: TagHierarchyMetadata;
}

export interface TreeNode {
  id: string;
  name: string;
  children?: TreeNode[];
  parent?: TreeNode | null;
}

class TagHierarchyService {
  private readonly baseUrl = '/api/v1/tags';

  /**
   * Get the complete tag hierarchy
   */
  async getHierarchy(options?: { noCache?: boolean }): Promise<TagHierarchyResponse> {
    const params = new URLSearchParams();
    if (options?.noCache) {
      params.append('no_cache', 'true');
    }

    const url = `${this.baseUrl}/hierarchy${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await apiClient.get<TagHierarchyResponse>(url);
    return response;
  }

  /**
   * Get a specific tag node by ID
   */
  async getNode(nodeId: string): Promise<TagHierarchyNode> {
    const response = await apiClient.get<TagHierarchyNode>(`${this.baseUrl}/hierarchy/nodes/${nodeId}`);
    return response;
  }

  /**
   * Get all direct children of a parent tag
   */
  async getChildren(parentId: string): Promise<TagHierarchyNode[]> {
    const response = await apiClient.get<TagHierarchyNode[]>(`${this.baseUrl}/hierarchy/children/${parentId}`);
    return response;
  }

  /**
   * Get all root tags (tags without parents)
   */
  async getRootTags(): Promise<TagHierarchyNode[]> {
    const response = await apiClient.get<TagHierarchyNode[]>(`${this.baseUrl}/hierarchy/roots`);
    return response;
  }

  /**
   * Get the path from a tag to its root
   */
  async getTagPath(nodeId: string): Promise<TagHierarchyNode[]> {
    const response = await apiClient.get<TagHierarchyNode[]>(`${this.baseUrl}/hierarchy/path/${nodeId}`);
    return response;
  }

  /**
   * Refresh tag hierarchy cache
   */
  async refreshHierarchy(): Promise<{ message: string; metadata: TagHierarchyMetadata }> {
    const response = await apiClient.post<{ message: string; metadata: TagHierarchyMetadata }>(
      `${this.baseUrl}/hierarchy/refresh`
    );
    return response;
  }

  /**
   * Convert flat node array to hierarchical tree structure
   */
  convertToTree(nodes: TagHierarchyNode[]): TreeNode[] {
    // Create a map for quick lookup
    const nodeMap = new Map<string, TreeNode>();
    const rootNodes: TreeNode[] = [];

    // First pass: create tree nodes
    nodes.forEach(node => {
      nodeMap.set(node.id, {
        id: node.id,
        name: node.name,
        children: [],
      });
    });

    // Second pass: build parent-child relationships
    nodes.forEach(node => {
      const treeNode = nodeMap.get(node.id)!;

      if (node.parent === null) {
        // Root node
        rootNodes.push(treeNode);
      } else {
        // Child node - add to parent's children
        const parentNode = nodeMap.get(node.parent);
        if (parentNode) {
          if (!parentNode.children) {
            parentNode.children = [];
          }
          parentNode.children.push(treeNode);
          treeNode.parent = parentNode;
        }
      }
    });

    // Sort root nodes and children alphabetically
    const sortNodes = (nodes: TreeNode[]) => {
      nodes.sort((a, b) => a.name.localeCompare(b.name));
      nodes.forEach(node => {
        if (node.children) {
          sortNodes(node.children);
        }
      });
    };

    sortNodes(rootNodes);
    return rootNodes;
  }

  /**
   * Search nodes by name (case-insensitive)
   */
  searchNodes(nodes: TagHierarchyNode[], query: string): TagHierarchyNode[] {
    if (!query.trim()) {
      return nodes;
    }

    const searchTerm = query.toLowerCase();
    return nodes.filter(node =>
      node.name.toLowerCase().includes(searchTerm) ||
      node.id.toLowerCase().includes(searchTerm)
    );
  }

  /**
   * Get all descendants of a node
   */
  getDescendants(nodes: TagHierarchyNode[], parentId: string): TagHierarchyNode[] {
    const descendants: TagHierarchyNode[] = [];
    const visited = new Set<string>();

    const findChildren = (currentParentId: string) => {
      nodes.forEach(node => {
        if (node.parent === currentParentId && !visited.has(node.id)) {
          visited.add(node.id);
          descendants.push(node);
          findChildren(node.id); // Recursively find children
        }
      });
    };

    findChildren(parentId);
    return descendants;
  }

  /**
   * Get breadcrumb path from root to node
   */
  getBreadcrumbs(nodes: TagHierarchyNode[], nodeId: string): TagHierarchyNode[] {
    const path: TagHierarchyNode[] = [];
    const nodeMap = new Map(nodes.map(node => [node.id, node]));

    let currentId: string | null = nodeId;
    const visited = new Set<string>();

    while (currentId && !visited.has(currentId)) {
      visited.add(currentId);
      const node = nodeMap.get(currentId);
      if (node) {
        path.unshift(node); // Add to beginning to get root->leaf order
        currentId = node.parent;
      } else {
        break;
      }
    }

    return path;
  }
}

export const tagHierarchyService = new TagHierarchyService();
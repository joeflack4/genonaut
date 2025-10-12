/**
 * Tag Tree View Component using react-accessible-treeview
 */

import { useMemo, useState } from 'react';
import TreeView from 'react-accessible-treeview';
import type { INode, ITreeViewOnNodeSelectProps } from 'react-accessible-treeview';
import {
  Box,
  Typography,
  IconButton,
  Chip,
  alpha,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
  Folder as FolderIcon,
  FolderOpen as FolderOpenIcon,
  Label as LabelIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTagHierarchyTree } from '../../hooks/useTagHierarchy';
import { usePersistedSetState } from '../../hooks/usePersistedState';
import type { TagHierarchyNode, TreeNode } from '../../services/tag-hierarchy-service';

interface TagTreeViewProps {
  onNodeClick?: (nodeId: string, nodeName: string) => void;
  selectedNodeId?: string;
  showNodeCounts?: boolean;
  maxHeight?: number | string;
  className?: string;
  selectedTagIds?: Set<string>;
  onSelectionChange?: (selectedTagIds: Set<string>) => void;
  onDirtyStateChange?: (isDirty: boolean) => void;
}

interface TreeNodeData extends INode {
  tagData: TagHierarchyNode;
  isLeaf: boolean;
  level: number;
}

export default function TagTreeView({
  onNodeClick,
  selectedNodeId,
  showNodeCounts = false,
  maxHeight = 600,
  className,
  selectedTagIds = new Set(),
  onSelectionChange,
  onDirtyStateChange,
}: TagTreeViewProps) {
  const navigate = useNavigate();
  const { data: treeStructure, flatNodes, isLoading, error } = useTagHierarchyTree();
  const [expandedIds, setExpandedIds] = usePersistedSetState('tagHierarchy:expandedIds', new Set(['__virtual_root__']));

  // Convert tree structure to react-accessible-treeview format
  const treeData = useMemo((): TreeNodeData[] => {
    if (!treeStructure || !flatNodes) {
      return [];
    }

    const result: TreeNodeData[] = [];
    const nodeMap = new Map<string, TagHierarchyNode>();

    // Create a map for quick lookup of flat node data
    flatNodes.forEach(node => {
      nodeMap.set(node.id, node);
    });

    // Create a virtual root node since react-accessible-treeview requires a single root
    const virtualRootData: TagHierarchyNode = {
      id: '__virtual_root__',
      name: 'Tag Categories',
      parent: null,
    };

    // Get the root category IDs for the virtual root's children array
    const rootCategoryIds = treeStructure.map(node => node.id);

    result.push({
      id: '__virtual_root__',
      name: 'Tag Categories',
      parent: null,
      children: rootCategoryIds, // Array of root category IDs
      tagData: virtualRootData,
      isLeaf: false,
      level: 0,
    });

    // Recursive function to convert TreeNode to TreeNodeData
    const convertNode = (node: TreeNode, parent: string | null, level: number): TreeNodeData => {
      const flatNodeData = nodeMap.get(node.id);
      if (!flatNodeData) {
        throw new Error(`Missing flat node data for ${node.id}`);
      }

      const hasChildren = node.children && node.children.length > 0;
      const childIds = hasChildren ? node.children!.map(child => child.id) : [];

      return {
        id: node.id,
        name: node.name,
        parent,
        children: childIds, // Array of child IDs for react-accessible-treeview
        tagData: flatNodeData,
        isLeaf: !hasChildren,
        level,
      };
    };

    // Recursive function to build the flat array with proper parent-child relationships
    const buildTreeData = (nodes: TreeNode[], parent: string | null, level: number) => {
      nodes.forEach(node => {
        const treeNodeData = convertNode(node, parent, level);
        result.push(treeNodeData);

        // Recursively add children
        if (node.children && node.children.length > 0) {
          buildTreeData(node.children, node.id, level + 1);
        }
      });
    };

    // Build the tree data starting from root nodes as children of virtual root
    buildTreeData(treeStructure, '__virtual_root__', 1);

    return result;
  }, [treeStructure, flatNodes]);

  const handleNodeSelect = ({ element, isSelected }: ITreeViewOnNodeSelectProps) => {
    const nodeData = element as TreeNodeData;
    const tagId = nodeData.tagData.id;

    // Don't handle selection for the virtual root node
    if (tagId === '__virtual_root__') {
      return;
    }

    // Toggle tag selection
    const newSelectedTags = new Set(selectedTagIds);
    if (newSelectedTags.has(tagId)) {
      newSelectedTags.delete(tagId);
    } else {
      newSelectedTags.add(tagId);
    }

    // Notify parent component of selection change
    if (onSelectionChange) {
      onSelectionChange(newSelectedTags);
    }

    // Notify parent if dirty state changed
    if (onDirtyStateChange) {
      onDirtyStateChange(newSelectedTags.size > 0);
    }

    // Call the optional click handler
    if (onNodeClick) {
      onNodeClick(tagId, nodeData.tagData.name);
    }
  };

  const handleNodeToggle = ({ element, isExpanded }: { element: TreeNodeData; isExpanded: boolean }) => {
    const newExpandedIds = new Set(expandedIds);
    if (isExpanded) {
      newExpandedIds.add(element.tagData.id);
    } else {
      newExpandedIds.delete(element.tagData.id);
    }
    setExpandedIds(newExpandedIds);
  };

  // Custom node renderer
  const NodeRenderer = ({ element, isBranch, isExpanded, getNodeProps, level }: any) => {
    const nodeData = element as TreeNodeData;
    const isHighlighted = selectedNodeId === nodeData.tagData.id;
    const isSelected = selectedTagIds.has(nodeData.tagData.id);

    return (
      <div
        {...getNodeProps()}
        style={{
          paddingLeft: `${level * 20 + 8}px`,
          display: 'flex',
          alignItems: 'center',
          padding: '8px 12px',
          cursor: 'pointer',
          backgroundColor: isSelected
            ? alpha('#4caf50', 0.15) // Green for Selected tags
            : isHighlighted
            ? alpha('#1976d2', 0.1) // Blue for highlighted
            : 'transparent',
          borderLeft: isSelected
            ? '3px solid #4caf50' // Green border for selected
            : isHighlighted
            ? '3px solid #1976d2' // Blue border for highlighted
            : '3px solid transparent',
          transition: 'all 0.2s ease',
        }}
        onMouseEnter={(e) => {
          if (!isSelected && !isHighlighted) {
            e.currentTarget.style.backgroundColor = alpha('#000', 0.04);
          }
        }}
        onMouseLeave={(e) => {
          if (!isSelected && !isHighlighted) {
            e.currentTarget.style.backgroundColor = 'transparent';
          }
        }}
      >
        {/* Expand/Collapse Icon */}
        {isBranch && (
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation(); // Prevent triggering node selection
              handleNodeToggle({
                element: nodeData,
                isExpanded: !isExpanded
              });
            }}
            sx={{
              mr: 0.5,
              p: 0.25,
              color: 'text.secondary',
            }}
          >
            {isExpanded ? (
              <ExpandMoreIcon fontSize="small" />
            ) : (
              <ChevronRightIcon fontSize="small" />
            )}
          </IconButton>
        )}

        {/* Node Icon */}
        <Box sx={{ mr: 1, display: 'flex', alignItems: 'center' }}>
          {isBranch ? (
            isExpanded ? (
              <FolderOpenIcon fontSize="small" color="primary" />
            ) : (
              <FolderIcon fontSize="small" color="action" />
            )
          ) : (
            <LabelIcon fontSize="small" color="secondary" />
          )}
        </Box>

        {/* Node Label */}
        <Typography
          variant="body2"
          sx={{
            flex: 1,
            fontWeight: isSelected ? 600 : isHighlighted ? 500 : 400,
            color: isSelected
              ? '#4caf50' // Green for selected
              : isHighlighted
              ? 'primary.main' // Blue for highlighted
              : 'text.primary',
          }}
        >
          {nodeData.name}
        </Typography>

        {/* Selection Indicator */}
        {isSelected && (
          <CheckCircleIcon
            fontSize="small"
            sx={{
              ml: 1,
              color: '#4caf50',
            }}
          />
        )}

        {/* Node Count Badge (if enabled) */}
        {showNodeCounts && isBranch && (
          <Chip
            size="small"
            label={nodeData.children?.length || 0}
            sx={{
              ml: 1,
              height: 20,
              fontSize: '0.75rem',
              backgroundColor: 'grey.100',
              color: 'text.secondary',
            }}
          />
        )}
      </div>
    );
  };

  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: 200,
          flexDirection: 'column',
          gap: 2,
        }}
      >
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary">
          Loading tag hierarchy...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load tag hierarchy. Please try refreshing the page.
      </Alert>
    );
  }

  if (!treeData.length) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        No tag hierarchy data available.
      </Alert>
    );
  }


  return (
    <Box
      className={className}
      sx={{
        maxHeight,
        overflow: 'auto',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 1,
        backgroundColor: 'background.paper',
        '& .tree': {
          listStyle: 'none',
          margin: 0,
          padding: 0,
        },
        '& .tree-node': {
          listStyle: 'none',
        },
        '& .tree-node:focus': {
          outline: '2px solid #1976d2',
          outlineOffset: '-2px',
        },
      }}
    >
      <TreeView
        data={treeData}
        aria-label="Tag hierarchy tree"
        nodeRenderer={NodeRenderer}
        onNodeSelect={handleNodeSelect}
        expandedIds={Array.from(expandedIds)}
        multiSelect={false}
        togglableSelect
        clickAction="EXCLUSIVE_SELECT"
      />
    </Box>
  );
}
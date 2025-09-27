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
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTagHierarchy } from '../../hooks/useTagHierarchy';
import type { TagHierarchyNode } from '../../services/tag-hierarchy-service';

interface TagTreeViewProps {
  onNodeClick?: (nodeId: string, nodeName: string) => void;
  selectedNodeId?: string;
  showNodeCounts?: boolean;
  maxHeight?: number | string;
  className?: string;
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
}: TagTreeViewProps) {
  const navigate = useNavigate();
  const { data: hierarchy, isLoading, error } = useTagHierarchy();
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  // Convert flat hierarchy to react-accessible-treeview format
  // Use a simple list approach for testing - just show the first root node and its children
  const treeData = useMemo((): TreeNodeData[] => {
    if (!hierarchy?.nodes) return [];

    // For testing, just create a simple tree with the first few nodes
    const result: TreeNodeData[] = [];
    const rootNodes = hierarchy.nodes.filter(node => !node.parent);

    if (rootNodes.length === 0) return [];

    // Just use the first root node to avoid react-accessible-treeview multiple root issues
    const firstRoot = rootNodes[0];
    const children = hierarchy.nodes.filter(node => node.parent === firstRoot.id);

    // Add the root node
    result.push({
      id: 'root_0',
      name: firstRoot.name,
      parent: null,
      children: [],
      tagData: firstRoot,
      isLeaf: children.length === 0,
      level: 0,
    });

    // Add direct children
    children.forEach((child, index) => {
      result.push({
        id: `child_${index}`,
        name: child.name,
        parent: 'root_0',
        children: [],
        tagData: child,
        isLeaf: true,
        level: 1,
      });
    });

    return result;
  }, [hierarchy?.nodes]);

  const handleNodeSelect = ({ element, isSelected }: ITreeViewOnNodeSelectProps) => {
    if (isSelected) {
      const nodeData = element as TreeNodeData;
      const tagId = nodeData.tagData.id;

      if (onNodeClick) {
        onNodeClick(tagId, nodeData.tagData.name);
      } else {
        // Default behavior: navigate to gallery with tag filter
        navigate(`/gallery?tag=${encodeURIComponent(tagId)}`);
      }
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
    const isSelected = selectedNodeId === nodeData.tagData.id;

    return (
      <div
        {...getNodeProps()}
        style={{
          paddingLeft: `${level * 20 + 8}px`,
          display: 'flex',
          alignItems: 'center',
          padding: '8px 12px',
          cursor: 'pointer',
          backgroundColor: isSelected ? alpha('#1976d2', 0.1) : 'transparent',
          borderLeft: isSelected ? '3px solid #1976d2' : '3px solid transparent',
          transition: 'background-color 0.2s ease',
        }}
        onMouseEnter={(e) => {
          if (!isSelected) {
            e.currentTarget.style.backgroundColor = alpha('#000', 0.04);
          }
        }}
        onMouseLeave={(e) => {
          if (!isSelected) {
            e.currentTarget.style.backgroundColor = 'transparent';
          }
        }}
      >
        {/* Expand/Collapse Icon */}
        {isBranch && (
          <IconButton
            size="small"
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
            fontWeight: isSelected ? 600 : 400,
            color: isSelected ? 'primary.main' : 'text.primary',
          }}
        >
          {nodeData.name}
        </Typography>

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
        defaultExpandedIds={[]}
        multiSelect={false}
        togglableSelect
        clickAction="EXCLUSIVE_SELECT"
      />
    </Box>
  );
}
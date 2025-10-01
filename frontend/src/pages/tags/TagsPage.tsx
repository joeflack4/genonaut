/**
 * Tags Page - Main page for browsing and exploring tag hierarchy
 */

import { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Chip,
  Divider,
  Alert,
  Skeleton,
  Button,
  Collapse,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Info as InfoIcon,
  Search as SearchIcon,
  AccountTree as AccountTreeIcon,
  Check as CheckIcon,
  Launch as LaunchIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import TagTreeView from '../../components/tags/TagTreeView';
import TagSearchFilter from '../../components/tags/TagSearchFilter';
import { useTagHierarchy, useRefreshHierarchy } from '../../hooks/useTagHierarchy';
import { usePersistedSetState } from '../../hooks/usePersistedState';

export default function TagsPage() {
  const navigate = useNavigate();
  const { data: hierarchy, isLoading, error } = useTagHierarchy();
  const refreshMutation = useRefreshHierarchy();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [searchMode, setSearchMode] = useState(false);
  const [selectedTagIds, setSelectedTagIds] = usePersistedSetState('tagHierarchy:selectedTags', new Set());
  const [isDirty, setIsDirty] = useState(false);
  const [helpExpanded, setHelpExpanded] = useState(false);
  const [hierarchyOverviewExpanded, setHierarchyOverviewExpanded] = useState(false);

  // Initialize dirty state based on persisted selected tags
  useEffect(() => {
    setIsDirty(selectedTagIds.size > 0);
  }, [selectedTagIds.size]);

  const handleNodeClick = useCallback((nodeId: string, _nodeName: string) => {
    setSelectedNodeId(nodeId);
    // No longer navigate immediately - only highlight the node
  }, []);

  const handleTagSelect = useCallback((nodeId: string, nodeName: string) => {
    handleNodeClick(nodeId, nodeName);
  }, [handleNodeClick]);

  const handleSelectionChange = useCallback((newSelectedTagIds: Set<string>) => {
    setSelectedTagIds(newSelectedTagIds);
  }, []);

  const handleDirtyStateChange = useCallback((newIsDirty: boolean) => {
    setIsDirty(newIsDirty);
  }, []);

  const handleApply = useCallback(() => {
    // For now, this button does nothing as requested
    // It just confirms the current selection without navigating
    console.log('Apply clicked - maintaining current state');
  }, []);

  const handleApplyAndQuery = useCallback(() => {
    if (selectedTagIds.size > 0) {
      // Build URLSearchParams to properly handle multiple tag parameters
      const searchParams = new URLSearchParams();
      Array.from(selectedTagIds).forEach(tagId => {
        searchParams.append('tag', tagId);
      });
      navigate(`/gallery?${searchParams.toString()}`);

      // Reset dirty state
      setIsDirty(false);
    }
  }, [selectedTagIds, navigate]);

  const handleRefresh = useCallback(() => {
    refreshMutation.mutate();
  }, [refreshMutation]);

  const toggleSearchMode = useCallback(() => {
    setSearchMode(!searchMode);
  }, [searchMode]);

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load tag hierarchy. Please check your connection and try again.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: '100%', overflow: 'hidden' }}>
      {/* Page Header */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AccountTreeIcon color="primary" sx={{ fontSize: 32 }} />
            <Typography variant="h4" component="h1">
              Tag Hierarchy
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title={searchMode ? "Show tree view" : "Show search"}>
              <IconButton
                onClick={toggleSearchMode}
                color={searchMode ? "primary" : "default"}
              >
                {searchMode ? <AccountTreeIcon /> : <SearchIcon />}
              </IconButton>
            </Tooltip>

            <Tooltip title="Refresh hierarchy">
              <IconButton
                onClick={handleRefresh}
                disabled={refreshMutation.isPending}
                color="primary"
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          Explore the organized structure of content tags. Click on any tag to view related content.
        </Typography>

        {/* Hierarchy Stats */}
        {isLoading ? (
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Skeleton variant="rectangular" width={120} height={32} />
            <Skeleton variant="rectangular" width={100} height={32} />
            <Skeleton variant="rectangular" width={140} height={32} />
          </Box>
        ) : hierarchy ? (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            <Chip
              icon={<InfoIcon />}
              label={`${hierarchy.metadata.totalNodes} total tags`}
              variant="outlined"
              size="small"
            />
            <Chip
              label={`${hierarchy.metadata.rootCategories} root categories`}
              variant="outlined"
              size="small"
            />
            <Chip
              label={`${hierarchy.metadata.totalRelationships} relationships`}
              variant="outlined"
              size="small"
            />
            <Chip
              label={`Updated: ${new Date(hierarchy.metadata.lastUpdated).toLocaleDateString()}`}
              variant="outlined"
              size="small"
            />
          </Box>
        ) : null}
      </Box>

      <Grid container spacing={3}>
        {/* Main Content Area */}
        <Grid size={{ xs: 12, lg: 9 }}>
          <Paper elevation={1} sx={{ height: 'fit-content', minHeight: 600 }}>
            {searchMode ? (
              <Box sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Search Tags
                </Typography>
                <TagSearchFilter
                  onTagSelect={handleTagSelect}
                  placeholder="Search for tags by name..."
                  showBreadcrumbs={true}
                  maxResults={100}
                />
                <Box sx={{ mt: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Start typing to search through all {hierarchy?.metadata.totalNodes || 0} tags in the hierarchy.
                    Click on any result to view related content.
                  </Typography>
                </Box>
              </Box>
            ) : (
              <Box>
                <TagTreeView
                  onNodeClick={handleNodeClick}
                  selectedNodeId={selectedNodeId || undefined}
                  selectedTagIds={selectedTagIds}
                  onSelectionChange={handleSelectionChange}
                  onDirtyStateChange={handleDirtyStateChange}
                  showNodeCounts={false}
                  maxHeight={600}
                />
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Sidebar */}
        <Grid size={{ xs: 12, lg: 3 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Tag Selection Status & Action Buttons - shows when tree state is dirty */}
            {isDirty && (
              <Card>
                <CardContent>
                  {/* Tag Count Display */}
                  <Box sx={{ mb: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Selection Status
                    </Typography>
                    <Chip
                      label={`${selectedTagIds.size} tag${selectedTagIds.size !== 1 ? 's' : ''} selected`}
                      color="primary"
                      variant="outlined"
                      sx={{ fontWeight: 600 }}
                    />
                  </Box>

                  {/* Clear All Tags Button */}
                  <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                    <Button
                      variant="outlined"
                      color="secondary"
                      size="small"
                      onClick={() => {
                        setSelectedTagIds(new Set());
                        setIsDirty(false);
                      }}
                    >
                      Clear All Tags
                    </Button>
                  </Box>

                  {/* Action Buttons */}
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="outlined"
                      color="primary"
                      onClick={handleApply}
                      startIcon={<CheckIcon />}
                      sx={{
                        flex: 1,
                        py: 1.5,
                        fontWeight: 600,
                      }}
                    >
                      Apply
                    </Button>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={handleApplyAndQuery}
                      startIcon={<LaunchIcon />}
                      sx={{
                        flex: 1,
                        py: 1.5,
                        fontWeight: 600,
                      }}
                    >
                      Apply & Query
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            )}

            {/* Quick Search Card */}
            {!searchMode && (
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Quick Search
                  </Typography>
                  <TagSearchFilter
                    onTagSelect={handleTagSelect}
                    placeholder="Quick tag search..."
                    showBreadcrumbs={false}
                    maxResults={10}
                  />
                </CardContent>
              </Card>
            )}

            {/* Help Card */}
            <Card>
              <CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    mb: helpExpanded ? 2 : 0
                  }}
                  onClick={() => setHelpExpanded(!helpExpanded)}
                >
                  <Typography variant="h6">
                    How to Use
                  </Typography>
                  <IconButton
                    size="small"
                    sx={{
                      transform: helpExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                      transition: 'transform 0.3s',
                    }}
                  >
                    <ExpandMoreIcon />
                  </IconButton>
                </Box>
                <Collapse in={helpExpanded}>
                  <Box component="ul" sx={{ pl: 2, m: 0 }}>
                    <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                      <strong>Browse:</strong> Expand categories in the tree to explore subcategories
                    </Typography>
                    <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                      <strong>Search:</strong> Use the search box to quickly find specific tags
                    </Typography>
                    <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                      <strong>Navigate:</strong> Click any tag to view related content in the gallery
                    </Typography>
                    <Typography component="li" variant="body2">
                      <strong>Switch views:</strong> Toggle between tree and search modes using the toolbar
                    </Typography>
                  </Box>
                </Collapse>
              </CardContent>
            </Card>

            {/* Hierarchy Info Card */}
            {hierarchy && (
              <Card>
                <CardContent>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      mb: hierarchyOverviewExpanded ? 2 : 0
                    }}
                    onClick={() => setHierarchyOverviewExpanded(!hierarchyOverviewExpanded)}
                  >
                    <Typography variant="h6">
                      Hierarchy Overview
                    </Typography>
                    <IconButton
                      size="small"
                      sx={{
                        transform: hierarchyOverviewExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.3s',
                      }}
                    >
                      <ExpandMoreIcon />
                    </IconButton>
                  </Box>
                  <Collapse in={hierarchyOverviewExpanded}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Total Tags:</Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {hierarchy.metadata.totalNodes}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Root Categories:</Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {hierarchy.metadata.rootCategories}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Relationships:</Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {hierarchy.metadata.totalRelationships}
                        </Typography>
                      </Box>
                      <Divider sx={{ my: 1 }} />
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Format:</Typography>
                        <Typography variant="body2">{hierarchy.metadata.format}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Version:</Typography>
                        <Typography variant="body2">{hierarchy.metadata.version}</Typography>
                      </Box>
                    </Box>
                  </Collapse>
                </CardContent>
              </Card>
            )}
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}
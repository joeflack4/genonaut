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
      <Box sx={{ p: 3 }} data-testid="tags-page-error">
        <Alert severity="error" data-testid="tags-page-error-alert">
          Failed to load tag hierarchy. Please check your connection and try again.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: '100%', overflow: 'hidden' }} data-testid="tags-page-root">
      {/* Page Header */}
      <Box sx={{ mb: 3 }} data-testid="tags-page-header">
        <Box
          sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}
          data-testid="tags-page-toolbar"
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} data-testid="tags-page-title-group">
            <AccountTreeIcon color="primary" sx={{ fontSize: 32 }} data-testid="tags-page-title-icon" />
            <Typography variant="h4" component="h1" data-testid="tags-page-title">
              Tag Hierarchy
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }} data-testid="tags-page-action-buttons">
            <Tooltip title={searchMode ? "Show tree view" : "Show search"}>
              <IconButton
                onClick={toggleSearchMode}
                color={searchMode ? "primary" : "default"}
                data-testid="tags-page-toggle-search"
              >
                {searchMode ? <AccountTreeIcon /> : <SearchIcon />}
              </IconButton>
            </Tooltip>

            <Tooltip title="Refresh hierarchy">
              <IconButton
                onClick={handleRefresh}
                disabled={refreshMutation.isPending}
                color="primary"
                data-testid="tags-page-refresh"
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Typography
          variant="body1"
          color="text.secondary"
          sx={{ mb: 2 }}
          data-testid="tags-page-description"
        >
          Explore the organized structure of content tags. Click on any tag to view related content.
        </Typography>

        {/* Hierarchy Stats */}
        {isLoading ? (
          <Box sx={{ display: 'flex', gap: 2 }} data-testid="tags-page-stats-loading">
            <Skeleton variant="rectangular" width={120} height={32} data-testid="tags-page-stats-skeleton-0" />
            <Skeleton variant="rectangular" width={100} height={32} data-testid="tags-page-stats-skeleton-1" />
            <Skeleton variant="rectangular" width={140} height={32} data-testid="tags-page-stats-skeleton-2" />
          </Box>
        ) : hierarchy ? (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }} data-testid="tags-page-stats">
            <Chip
              icon={<InfoIcon />}
              label={`${hierarchy.metadata.totalNodes} total tags`}
              variant="outlined"
              size="small"
              data-testid="tags-page-stats-total-tags"
            />
            <Chip
              label={`${hierarchy.metadata.rootCategories} root categories`}
              variant="outlined"
              size="small"
              data-testid="tags-page-stats-root-categories"
            />
            <Chip
              label={`${hierarchy.metadata.totalRelationships} relationships`}
              variant="outlined"
              size="small"
              data-testid="tags-page-stats-relationships"
            />
            <Chip
              label={`Updated: ${new Date(hierarchy.metadata.lastUpdated).toLocaleDateString()}`}
              variant="outlined"
              size="small"
              data-testid="tags-page-stats-updated"
            />
          </Box>
        ) : null}
      </Box>

      <Grid container spacing={3} data-testid="tags-page-layout">
        {/* Main Content Area */}
        <Grid size={{ xs: 12, lg: 9 }} data-testid="tags-page-main">
          <Paper elevation={1} sx={{ height: 'fit-content', minHeight: 600 }} data-testid="tags-page-main-card">
            {searchMode ? (
              <Box sx={{ p: 3 }} data-testid="tags-page-search-mode">
                <Typography variant="h6" sx={{ mb: 2 }} data-testid="tags-page-search-title">
                  Search Tags
                </Typography>
                <TagSearchFilter
                  onTagSelect={handleTagSelect}
                  placeholder="Search for tags by name..."
                  showBreadcrumbs={true}
                  maxResults={100}
                />
                <Box sx={{ mt: 3 }} data-testid="tags-page-search-hint">
                  <Typography variant="body2" color="text.secondary" data-testid="tags-page-search-hint-text">
                    Start typing to search through all {hierarchy?.metadata.totalNodes || 0} tags in the hierarchy.
                    Click on any result to view related content.
                  </Typography>
                </Box>
              </Box>
            ) : (
              <Box data-testid="tags-page-tree-mode">
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
        <Grid size={{ xs: 12, lg: 3 }} data-testid="tags-page-sidebar">
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }} data-testid="tags-page-sidebar-content">
            {/* Tag Selection Status & Action Buttons - shows when tree state is dirty */}
            {isDirty && (
              <Card data-testid="tags-page-selection-card">
                <CardContent data-testid="tags-page-selection-content">
                  {/* Tag Count Display */}
                  <Box sx={{ mb: 2, textAlign: 'center' }} data-testid="tags-page-selection-status">
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }} data-testid="tags-page-selection-status-label">
                      Selection Status
                    </Typography>
                    <Chip
                      label={`${selectedTagIds.size} tag${selectedTagIds.size !== 1 ? 's' : ''} selected`}
                      color="primary"
                      variant="outlined"
                      sx={{ fontWeight: 600 }}
                      data-testid="tags-page-selection-count"
                    />
                  </Box>

                  {/* Clear All Tags Button */}
                  <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }} data-testid="tags-page-selection-clear">
                    <Button
                      variant="outlined"
                      color="secondary"
                      size="small"
                      onClick={() => {
                        setSelectedTagIds(new Set());
                        setIsDirty(false);
                      }}
                      data-testid="tags-page-selection-clear-button"
                    >
                      Clear All Tags
                    </Button>
                  </Box>

                  {/* Action Buttons */}
                  <Box sx={{ display: 'flex', gap: 1 }} data-testid="tags-page-selection-actions">
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
                      data-testid="tags-page-apply-button"
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
                      data-testid="tags-page-apply-query-button"
                    >
                      Apply & Query
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            )}

            {/* Quick Search Card */}
            {!searchMode && (
              <Card data-testid="tags-page-quick-search-card">
                <CardContent data-testid="tags-page-quick-search-content">
                  <Typography variant="h6" sx={{ mb: 2 }} data-testid="tags-page-quick-search-title">
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
            <Card data-testid="tags-page-help-card">
              <CardContent data-testid="tags-page-help-content">
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    mb: helpExpanded ? 2 : 0
                  }}
                  onClick={() => setHelpExpanded(!helpExpanded)}
                  data-testid="tags-page-help-header"
                >
                  <Typography variant="h6" data-testid="tags-page-help-title">
                    How to Use
                  </Typography>
                  <IconButton
                    size="small"
                    sx={{
                      transform: helpExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                      transition: 'transform 0.3s',
                    }}
                    data-testid="tags-page-help-toggle"
                  >
                    <ExpandMoreIcon />
                  </IconButton>
                </Box>
                <Collapse in={helpExpanded} data-testid="tags-page-help-collapse">
                  <Box component="ul" sx={{ pl: 2, m: 0 }} data-testid="tags-page-help-list">
                    <Typography component="li" variant="body2" sx={{ mb: 1 }} data-testid="tags-page-help-item-browse">
                      <strong>Browse:</strong> Expand categories in the tree to explore subcategories
                    </Typography>
                    <Typography component="li" variant="body2" sx={{ mb: 1 }} data-testid="tags-page-help-item-search">
                      <strong>Search:</strong> Use the search box to quickly find specific tags
                    </Typography>
                    <Typography component="li" variant="body2" sx={{ mb: 1 }} data-testid="tags-page-help-item-navigate">
                      <strong>Navigate:</strong> Click any tag to view related content in the gallery
                    </Typography>
                    <Typography component="li" variant="body2" data-testid="tags-page-help-item-switch">
                      <strong>Switch views:</strong> Toggle between tree and search modes using the toolbar
                    </Typography>
                  </Box>
                </Collapse>
              </CardContent>
            </Card>

            {/* Hierarchy Info Card */}
            {hierarchy && (
              <Card data-testid="tags-page-hierarchy-card">
                <CardContent data-testid="tags-page-hierarchy-content">
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      mb: hierarchyOverviewExpanded ? 2 : 0
                    }}
                    onClick={() => setHierarchyOverviewExpanded(!hierarchyOverviewExpanded)}
                    data-testid="tags-page-hierarchy-header"
                  >
                    <Typography variant="h6" data-testid="tags-page-hierarchy-title">
                      Hierarchy Overview
                    </Typography>
                    <IconButton
                      size="small"
                      sx={{
                        transform: hierarchyOverviewExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.3s',
                      }}
                      data-testid="tags-page-hierarchy-toggle"
                    >
                      <ExpandMoreIcon />
                    </IconButton>
                  </Box>
                  <Collapse in={hierarchyOverviewExpanded} data-testid="tags-page-hierarchy-collapse">
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }} data-testid="tags-page-hierarchy-details">
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }} data-testid="tags-page-hierarchy-total-tags">
                        <Typography variant="body2">Total Tags:</Typography>
                        <Typography variant="body2" fontWeight="bold" data-testid="tags-page-hierarchy-total-tags-value">
                          {hierarchy.metadata.totalNodes}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }} data-testid="tags-page-hierarchy-root-categories">
                        <Typography variant="body2">Root Categories:</Typography>
                        <Typography variant="body2" fontWeight="bold" data-testid="tags-page-hierarchy-root-categories-value">
                          {hierarchy.metadata.rootCategories}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }} data-testid="tags-page-hierarchy-relationships">
                        <Typography variant="body2">Relationships:</Typography>
                        <Typography variant="body2" fontWeight="bold" data-testid="tags-page-hierarchy-relationships-value">
                          {hierarchy.metadata.totalRelationships}
                        </Typography>
                      </Box>
                      <Divider sx={{ my: 1 }} data-testid="tags-page-hierarchy-divider" />
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }} data-testid="tags-page-hierarchy-format">
                        <Typography variant="body2">Format:</Typography>
                        <Typography variant="body2" data-testid="tags-page-hierarchy-format-value">{hierarchy.metadata.format}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }} data-testid="tags-page-hierarchy-version">
                        <Typography variant="body2">Version:</Typography>
                        <Typography variant="body2" data-testid="tags-page-hierarchy-version-value">{hierarchy.metadata.version}</Typography>
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

/**
 * Tag Search and Filter Component
 */

import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Paper,
  Collapse,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  Label as LabelIcon,
} from '@mui/icons-material';
import { useTagHierarchySearch, useTagBreadcrumbs } from '../../hooks/useTagHierarchy';
import type { TagHierarchyNode } from '../../services/tag-hierarchy-service';

interface TagSearchFilterProps {
  onTagSelect?: (nodeId: string, nodeName: string) => void;
  selectedTags?: string[];
  placeholder?: string;
  showBreadcrumbs?: boolean;
  maxResults?: number;
}

export default function TagSearchFilter({
  onTagSelect,
  selectedTags = [],
  placeholder = "Search tags...",
  showBreadcrumbs = true,
  maxResults = 50,
}: TagSearchFilterProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showResults, setShowResults] = useState(false);

  const { results, isLoading, error, hasQuery, totalResults } = useTagHierarchySearch(searchQuery);

  // Limit results for performance
  const displayResults = useMemo(() => {
    return results.slice(0, maxResults);
  }, [results, maxResults]);

  const handleSearchChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setSearchQuery(value);
    setShowResults(!!value.trim());
  }, []);

  const handleClearSearch = useCallback(() => {
    setSearchQuery('');
    setShowResults(false);
  }, []);

  const handleTagClick = useCallback((node: TagHierarchyNode) => {
    if (onTagSelect) {
      onTagSelect(node.id, node.name);
    }
    // Keep search open for multi-selection scenarios
    // setShowResults(false);
  }, [onTagSelect]);

  const handleSearchFocus = useCallback(() => {
    if (hasQuery) {
      setShowResults(true);
    }
  }, [hasQuery]);

  const handleSearchBlur = useCallback(() => {
    // Delay hiding results to allow for click events
    setTimeout(() => setShowResults(false), 200);
  }, []);

  return (
    <Box sx={{ position: 'relative', width: '100%' }}>
      {/* Search Input */}
      <TextField
        fullWidth
        variant="outlined"
        placeholder={placeholder}
        value={searchQuery}
        onChange={handleSearchChange}
        onFocus={handleSearchFocus}
        onBlur={handleSearchBlur}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon color="action" />
            </InputAdornment>
          ),
          endAdornment: searchQuery && (
            <InputAdornment position="end">
              <IconButton
                onClick={handleClearSearch}
                size="small"
                edge="end"
                aria-label="Clear search"
              >
                <ClearIcon />
              </IconButton>
            </InputAdornment>
          ),
        }}
        sx={{
          mb: selectedTags.length > 0 ? 1 : 0,
        }}
      />

      {/* Selected tags */}
      {selectedTags.length > 0 && (
        <Box sx={{ mb: 2, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          {selectedTags.map((tagId) => (
            <SelectedTagChip
              key={tagId}
              tagId={tagId}
              showBreadcrumbs={showBreadcrumbs}
              onRemove={() => {
                // Handle tag removal if needed
                // This would typically be managed by parent component
              }}
            />
          ))}
        </Box>
      )}

      {/* Search Results */}
      <Collapse in={showResults}>
        <Paper
          elevation={3}
          sx={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            zIndex: 1000,
            maxHeight: 400,
            overflow: 'auto',
            mt: 0.5,
          }}
        >
          {isLoading && (
            <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <CircularProgress size={16} />
              <Typography variant="body2" color="text.secondary">
                Searching...
              </Typography>
            </Box>
          )}

          {error && (
            <Alert severity="error" sx={{ m: 1 }}>
              Failed to search tags. Please try again.
            </Alert>
          )}

          {!isLoading && !error && hasQuery && (
            <>
              {/* Results Header */}
              <Box sx={{ p: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
                <Typography variant="body2" color="text.secondary">
                  {totalResults > maxResults ? (
                    <>Showing {maxResults} of {totalResults} results</>
                  ) : (
                    <>{totalResults} result{totalResults !== 1 ? 's' : ''} found</>
                  )}
                </Typography>
              </Box>

              {/* Results List */}
              {displayResults.length > 0 ? (
                <List dense sx={{ py: 0 }}>
                  {displayResults.map((node: TagHierarchyNode) => (
                    <SearchResultItem
                      key={node.id}
                      node={node}
                      searchQuery={searchQuery}
                      onSelect={handleTagClick}
                      isSelected={selectedTags.includes(node.id)}
                      showBreadcrumbs={showBreadcrumbs}
                    />
                  ))}
                </List>
              ) : (
                <Box sx={{ p: 3, textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    No tags found matching "{searchQuery}"
                  </Typography>
                </Box>
              )}
            </>
          )}
        </Paper>
      </Collapse>
    </Box>
  );
}

// Component for individual search result items
interface SearchResultItemProps {
  node: TagHierarchyNode;
  searchQuery: string;
  onSelect: (node: TagHierarchyNode) => void;
  isSelected: boolean;
  showBreadcrumbs: boolean;
}

function SearchResultItem({
  node,
  searchQuery,
  onSelect,
  isSelected,
  showBreadcrumbs,
}: SearchResultItemProps) {
  const { breadcrumbs } = useTagBreadcrumbs(node.id);

  // Highlight search matches in text
  const highlightText = (text: string, query: string) => {
    if (!query) return text;

    const regex = new RegExp(`(${query})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, index) => (
      regex.test(part) ? (
        <Box
          key={index}
          component="span"
          sx={{
            backgroundColor: 'warning.light',
            color: 'warning.contrastText',
            fontWeight: 'bold',
            borderRadius: 0.5,
            px: 0.25,
          }}
        >
          {part}
        </Box>
      ) : (
        part
      )
    ));
  };

  return (
    <ListItem disablePadding>
      <ListItemButton
        onClick={() => onSelect(node)}
        selected={isSelected}
        sx={{
          flexDirection: 'column',
          alignItems: 'flex-start',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          <ListItemIcon sx={{ minWidth: 36 }}>
            <LabelIcon fontSize="small" color="secondary" />
          </ListItemIcon>
          <ListItemText
            primary={highlightText(node.name, searchQuery)}
            primaryTypographyProps={{
              variant: 'body2',
              fontWeight: isSelected ? 600 : 400,
            }}
          />
        </Box>

        {/* Breadcrumb Path */}
        {showBreadcrumbs && breadcrumbs.length > 1 && (
          <Box sx={{ ml: 4.5, mt: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              {breadcrumbs.slice(0, -1).map(crumb => crumb.name).join(' > ')}
            </Typography>
          </Box>
        )}
      </ListItemButton>
    </ListItem>
  );
}

// Component for selected tag chips with breadcrumbs
interface SelectedTagChipProps {
  tagId: string;
  showBreadcrumbs: boolean;
  onRemove: () => void;
}

function SelectedTagChip({ tagId, showBreadcrumbs, onRemove }: SelectedTagChipProps) {
  const { breadcrumbs } = useTagBreadcrumbs(tagId);
  const tagName = breadcrumbs[breadcrumbs.length - 1]?.name || tagId;

  const label = showBreadcrumbs && breadcrumbs.length > 1
    ? `${breadcrumbs.slice(0, -1).map(b => b.name).join(' > ')} > ${tagName}`
    : tagName;

  return (
    <Chip
      label={label}
      variant="outlined"
      color="primary"
      onDelete={onRemove}
      icon={<LabelIcon />}
      sx={{
        maxWidth: 300,
        '& .MuiChip-label': {
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        },
      }}
    />
  );
}
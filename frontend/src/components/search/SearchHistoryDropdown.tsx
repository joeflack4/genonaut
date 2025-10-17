/**
 * Dropdown component displaying recent search history.
 * Shows the 3 most recent searches with delete buttons.
 */

import { Box, List, ListItem, ListItemText, IconButton, Typography, Paper, Button, Divider } from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import { useNavigate } from 'react-router-dom'
import type { SearchHistoryRecord } from '../../services'

interface SearchHistoryDropdownProps {
  /** Recent search history items (non-aggregated) */
  items: SearchHistoryRecord[]
  /** Callback when user clicks on a history item */
  onItemClick: (searchQuery: string) => void
  /** Callback when user deletes a history item */
  onItemDelete: (searchQuery: string) => void
  /** Whether to show the dropdown */
  show: boolean
}

/**
 * Truncates a string to maxLength characters and adds ellipsis.
 */
function truncateString(str: string, maxLength: number): string {
  if (str.length <= maxLength) {
    return str
  }
  return str.substring(0, maxLength) + '...'
}

export function SearchHistoryDropdown({
  items,
  onItemClick,
  onItemDelete,
  show,
}: SearchHistoryDropdownProps) {
  const navigate = useNavigate()

  if (!show || items.length === 0) {
    return null
  }

  const handleSeeAllClick = () => {
    navigate('/settings/search-history')
  }

  return (
    <Paper
      elevation={3}
      data-testid="search-history-dropdown"
      sx={{
        position: 'absolute',
        top: '100%',
        left: 0,
        right: 0,
        zIndex: 1000,
        mt: 1,
        maxHeight: 300,
        overflow: 'auto',
      }}
    >
      <List dense>
        {items.map((item) => (
          <ListItem
            key={item.id}
            data-testid={`search-history-item-${item.id}`}
            sx={{
              cursor: 'pointer',
              '&:hover': {
                backgroundColor: 'action.hover',
              },
            }}
            secondaryAction={
              <IconButton
                edge="end"
                aria-label="delete"
                data-testid={`search-history-delete-${item.id}`}
                onClick={(e) => {
                  e.stopPropagation()
                  onItemDelete(item.search_query)
                }}
                size="small"
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            }
            onClick={() => onItemClick(item.search_query)}
          >
            <ListItemText
              primary={
                <Typography
                  variant="body2"
                  data-testid={`search-history-text-${item.id}`}
                  sx={{ pr: 1 }}
                >
                  {truncateString(item.search_query, 30)}
                </Typography>
              }
            />
          </ListItem>
        ))}
      </List>
      <Divider />
      <Box sx={{ p: 1, textAlign: 'center' }}>
        <Button
          fullWidth
          variant="text"
          size="small"
          onClick={handleSeeAllClick}
          data-testid="search-history-see-all-button"
          sx={{
            textTransform: 'none',
            fontSize: '0.875rem',
          }}
        >
          See all
        </Button>
      </Box>
    </Paper>
  )
}

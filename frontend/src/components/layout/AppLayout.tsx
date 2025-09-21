import { forwardRef } from 'react'
import type { NavLinkProps } from 'react-router-dom'
import { NavLink, Outlet } from 'react-router-dom'
import {
  AppBar,
  Box,
  Button,
  Container,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Skeleton,
  Toolbar,
  Typography,
} from '@mui/material'
import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined'
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined'
import { useCurrentUser } from '../../hooks'
import { useThemeMode } from '../../app/providers/theme'

const navItems = [
  { label: 'Dashboard', to: '/dashboard' },
  { label: 'Content', to: '/content' },
  { label: 'Recommendations', to: '/recommendations' },
  { label: 'Settings', to: '/settings' },
]

const NavLinkButton = forwardRef<HTMLAnchorElement, NavLinkProps>((props, ref) => (
  <NavLink ref={ref} {...props} />
))

NavLinkButton.displayName = 'NavLinkButton'

export function AppLayout() {
  const { data: currentUser, isLoading: isUserLoading } = useCurrentUser()
  const { mode, toggleMode } = useThemeMode()

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', color: 'text.primary' }}>
      <AppBar position="static" component="header" elevation={0} color="primary">
        <Toolbar sx={{ justifyContent: 'space-between', gap: 2 }}>
          <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
            Genonaut
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Button
              variant="outlined"
              color="inherit"
              onClick={toggleMode}
              startIcon={
                mode === 'dark' ? <LightModeOutlinedIcon fontSize="small" /> : <DarkModeOutlinedIcon fontSize="small" />
              }
              sx={{ textTransform: 'none' }}
            >
              {mode === 'dark' ? 'Light mode' : 'Dark mode'}
            </Button>
            {isUserLoading ? (
              <Skeleton variant="text" width={120} />
            ) : (
              <Typography variant="subtitle1" component="div">
                {currentUser?.name ?? 'Admin'}
              </Typography>
            )}
          </Box>
        </Toolbar>
      </AppBar>
      <Box sx={{ display: 'flex', minHeight: 'calc(100vh - 64px)' }}>
        <Box
          component="nav"
          sx={{
            width: 220,
            flexShrink: 0,
            borderRight: 1,
            borderColor: 'divider',
            display: { xs: 'none', md: 'block' },
          }}
        >
          <List>
            {navItems.map((item) => (
              <ListItem key={item.to} disablePadding>
                <ListItemButton
                  component={NavLinkButton}
                  to={item.to}
                  sx={{
                    '&.active': {
                      bgcolor: 'action.selected',
                    },
                  }}
                >
                  <ListItemText primary={item.label} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
        <Container component="main" sx={{ flexGrow: 1, py: 4 }}>
          <Outlet />
        </Container>
      </Box>
    </Box>
  )
}

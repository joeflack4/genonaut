import { forwardRef, useState, useEffect } from 'react'
import type { NavLinkProps } from 'react-router-dom'
import { NavLink, Outlet } from 'react-router-dom'
import {
  AppBar,
  Box,
  Button,
  Container,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Skeleton,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined'
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined'
import MenuIcon from '@mui/icons-material/Menu'
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

const drawerWidth = 220

export function AppLayout() {
  const { data: currentUser, isLoading: isUserLoading } = useCurrentUser()
  const { mode, toggleMode } = useThemeMode()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

  // State for sidebar open/closed
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Set default sidebar state based on screen size
  useEffect(() => {
    setSidebarOpen(!isMobile)
  }, [isMobile])

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen)
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', color: 'text.primary' }}>
      <AppBar position="static" component="header" elevation={0} color="primary">
        <Toolbar sx={{ justifyContent: 'space-between', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton
              color="inherit"
              aria-label="toggle sidebar"
              edge="start"
              onClick={handleSidebarToggle}
              sx={{ mr: 1 }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
              Genonaut
            </Typography>
          </Box>
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
        <Box component="nav" sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}>
          <Drawer
            variant={isMobile ? 'temporary' : 'persistent'}
            open={sidebarOpen}
            onClose={handleSidebarToggle}
            ModalProps={{
              keepMounted: true, // Better mobile performance
            }}
            sx={{
              '& .MuiDrawer-paper': {
                width: drawerWidth,
                boxSizing: 'border-box',
                borderRight: 1,
                borderColor: 'divider',
                position: { xs: 'fixed', md: 'relative' },
                height: { md: '100%' },
                top: { xs: 64, md: 0 }, // Account for AppBar height on mobile
              },
            }}
          >
            <List>
              {navItems.map((item) => (
                <ListItem key={item.to} disablePadding>
                  <ListItemButton
                    component={NavLinkButton}
                    to={item.to}
                    onClick={isMobile ? handleSidebarToggle : undefined}
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
          </Drawer>
        </Box>
        <Container
          component="main"
          sx={{
            flexGrow: 1,
            py: 4,
            ml: { md: sidebarOpen ? 0 : `-${drawerWidth}px` },
            transition: theme.transitions.create(['margin'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.leavingScreen,
            }),
          }}
        >
          <Outlet />
        </Container>
      </Box>
    </Box>
  )
}

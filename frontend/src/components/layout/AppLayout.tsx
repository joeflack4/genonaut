import { forwardRef, useState, useEffect } from 'react'
import type { NavLinkProps } from 'react-router-dom'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
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
  ListItemIcon,
  ListItemText,
  Skeleton,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined'
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined'
import MenuIcon from '@mui/icons-material/Menu'
import PersonIcon from '@mui/icons-material/Person'
import DashboardIcon from '@mui/icons-material/Dashboard'
import ArticleIcon from '@mui/icons-material/Article'
import RecommendIcon from '@mui/icons-material/Recommend'
import SettingsIcon from '@mui/icons-material/Settings'
import { useCurrentUser } from '../../hooks'
import { useThemeMode } from '../../app/providers/theme'
import { useUiSettings } from '../../app/providers/ui'

const navItems = [
  { label: 'Dashboard', to: '/dashboard', icon: DashboardIcon },
  { label: 'Gallery', to: '/gallery', icon: ArticleIcon },
  { label: 'Recommendations', to: '/recommendations', icon: RecommendIcon },
  { label: 'Settings', to: '/settings', icon: SettingsIcon },
]

const NavLinkButton = forwardRef<HTMLAnchorElement, NavLinkProps>((props, ref) => (
  <NavLink ref={ref} {...props} />
))

NavLinkButton.displayName = 'NavLinkButton'

export function AppLayout() {
  const { data: currentUser, isLoading: isUserLoading } = useCurrentUser()
  const { mode, toggleMode } = useThemeMode()
  const { showButtonLabels } = useUiSettings()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const navigate = useNavigate()

  // Dynamic drawer width based on whether labels are shown
  const drawerWidth = showButtonLabels ? 220 : 72

  // State for sidebar open/closed
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Set default sidebar state based on screen size
  useEffect(() => {
    setSidebarOpen(!isMobile)
  }, [isMobile])

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen)
  }

  const handleUserClick = () => {
    navigate('/settings')
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', color: 'text.primary' }}>
      <AppBar position="static" component="header" elevation={0} color="primary">
        <Toolbar sx={{ justifyContent: 'space-between', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title="Toggle sidebar" enterDelay={1500} arrow>
              <IconButton
                color="inherit"
                aria-label="toggle sidebar"
                edge="start"
                onClick={handleSidebarToggle}
                sx={{ mr: 1 }}
              >
                <MenuIcon />
              </IconButton>
            </Tooltip>
            <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
              Genonaut
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Tooltip title={mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} enterDelay={1500} arrow>
              <Button
                variant={showButtonLabels ? "outlined" : "text"}
                color="inherit"
                onClick={toggleMode}
                startIcon={
                  mode === 'dark' ? <LightModeOutlinedIcon fontSize="small" /> : <DarkModeOutlinedIcon fontSize="small" />
                }
                sx={{ textTransform: 'none' }}
              >
                {showButtonLabels && (mode === 'dark' ? 'Light mode' : 'Dark mode')}
              </Button>
            </Tooltip>
            {isUserLoading ? (
              <Skeleton variant="text" width={120} />
            ) : (
              <Tooltip title="Go to account settings" enterDelay={1500} arrow>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    cursor: 'pointer',
                    borderRadius: 1,
                    px: 1,
                    py: 0.5,
                    '&:hover': {
                      bgcolor: 'action.hover'
                    }
                  }}
                  onClick={handleUserClick}
                >
                  <PersonIcon fontSize="small" />
                  {showButtonLabels && (
                    <Typography variant="subtitle1" component="div">
                      {currentUser?.name ?? 'Admin'}
                    </Typography>
                  )}
                </Box>
              </Tooltip>
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
              {navItems.map((item) => {
                const IconComponent = item.icon
                return (
                  <ListItem key={item.to} disablePadding>
                    <Tooltip title={item.label} enterDelay={1500} arrow placement="right">
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
                        <ListItemIcon>
                          <IconComponent />
                        </ListItemIcon>
                        {showButtonLabels && <ListItemText primary={item.label} />}
                      </ListItemButton>
                    </Tooltip>
                  </ListItem>
                )
              })}
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
